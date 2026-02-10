"""
Shared profile operations for DocsAI.

Used by both the CLI commands and the FastAPI endpoints.
All functions work with direct file/ChromaDB access — no HTTP server needed.
"""

import shutil
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .config_loader import load_config, profile_paths

PROFILES_DIR = Path("profiles")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_profile_name(name: str) -> bool:
    """Check that a profile name is non-empty and alphanumeric (plus dash/underscore)."""
    if not name:
        return False
    return name.replace("_", "").replace("-", "").isalnum()


def profile_exists(name: str) -> bool:
    """Check whether a profile directory with a config.yaml exists."""
    return (PROFILES_DIR / name / "config.yaml").exists()


# ---------------------------------------------------------------------------
# Discovery & stats
# ---------------------------------------------------------------------------

def discover_profiles() -> List[str]:
    """Return sorted list of profile names found in profiles/."""
    if not PROFILES_DIR.exists():
        return []
    names = []
    for p in PROFILES_DIR.iterdir():
        if p.is_dir() and (p / "config.yaml").exists():
            names.append(p.name)
    return sorted(names)


def get_profile_summary(name: str) -> Dict[str, Any]:
    """
    Return a summary dict for a profile:
      name, description, source_type, domain, allowed_paths, depth,
      local_paths, chunk_count, cache_size, chroma_size
    """
    cfg = load_config(name)
    paths = profile_paths(name)
    source = cfg.get("source", {})

    # Chunk count from ChromaDB
    chunk_count = 0
    try:
        import gc
        import chromadb
        from chromadb.config import Settings

        client = chromadb.Client(
            Settings(is_persistent=True, persist_directory=str(paths["chroma"]))
        )
        coll = client.get_or_create_collection("docs")
        chunk_count = coll.count()
        # Release SQLite handles (critical on Windows)
        del coll, client
        gc.collect()
    except Exception:
        pass

    return {
        "name": name,
        "description": cfg.get("description", ""),
        "source_type": source.get("type", "unknown"),
        "domain": source.get("domain", ""),
        "allowed_paths": source.get("allowed_paths", []),
        "depth": source.get("depth", 2),
        "local_paths": source.get("local_paths", []),
        "chunk_count": chunk_count,
        "cache_size": dir_size(paths["cache"]),
        "chroma_size": dir_size(paths["chroma"]),
    }


# ---------------------------------------------------------------------------
# Profile creation
# ---------------------------------------------------------------------------

def create_profile_on_disk(
    name: str,
    description: str,
    source_type: str,
    domain: Optional[str] = None,
    allowed_paths: Optional[List[str]] = None,
    depth: int = 2,
    local_paths: Optional[List[str]] = None,
    file_types: Optional[List[str]] = None,
) -> Path:
    """
    Create a profile directory + config.yaml. Returns the profile directory path.
    Raises ValueError on invalid input, FileExistsError if profile already exists.
    """
    if not validate_profile_name(name):
        raise ValueError(
            f"Invalid profile name '{name}'. Use alphanumeric characters, dashes, or underscores."
        )

    profile_dir = PROFILES_DIR / name
    if profile_dir.exists():
        raise FileExistsError(f"Profile '{name}' already exists.")

    # Build config — only include what the user set (defaults come from config_loader)
    config: Dict[str, Any] = {
        "name": name,
        "description": description or f"{name} knowledge base",
        "source": {},
    }

    if source_type == "web":
        if not domain:
            raise ValueError("A domain is required for web source type.")
        parsed = urlparse(domain.rstrip("/"))
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        default_paths = [parsed.path] if parsed.path and parsed.path != "/" else ["/"]
        config["source"]["type"] = "web"
        config["source"]["domain"] = base_domain
        config["source"]["allowed_paths"] = allowed_paths or default_paths
        config["source"]["depth"] = depth
        config["source"]["respect_robots"] = True

    elif source_type == "local":
        if not local_paths:
            raise ValueError("At least one local path is required for local source type.")
        config["source"]["type"] = "local"
        config["source"]["local_paths"] = local_paths
        config["source"]["file_types"] = file_types or ["all"]

    elif source_type == "mixed":
        config["source"]["type"] = "mixed"
        if domain:
            parsed = urlparse(domain.rstrip("/"))
            base_domain = f"{parsed.scheme}://{parsed.netloc}"
            default_paths = [parsed.path] if parsed.path and parsed.path != "/" else ["/"]
            config["source"]["domain"] = base_domain
            config["source"]["allowed_paths"] = allowed_paths or default_paths
            config["source"]["depth"] = depth
            config["source"]["respect_robots"] = True
        if local_paths:
            config["source"]["local_paths"] = local_paths
            config["source"]["file_types"] = file_types or ["all"]

    else:
        raise ValueError(f"Invalid source type '{source_type}'. Use: web, local, or mixed.")

    # Add model defaults (keep config clean but functional out of the box)
    config["model"] = {
        "llm": {
            "mode": "ollama",
            "ollama_model": "qwen2.5:14b-instruct",
            "n_ctx": 256000,
            "temperature": 0.2,
        },
        "embedding": {"hf_name": "BAAI/bge-base-en-v1.5"},
    }

    # Create directories
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "cache").mkdir(exist_ok=True)
    (profile_dir / "data").mkdir(exist_ok=True)
    (profile_dir / "data" / "chroma").mkdir(exist_ok=True)

    # Write config
    config_path = profile_dir / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return profile_dir


# ---------------------------------------------------------------------------
# Add sources to existing profiles
# ---------------------------------------------------------------------------

def _read_raw_config(name: str) -> Dict[str, Any]:
    """Read the raw YAML config without merging defaults."""
    cfg_path = PROFILES_DIR / name / "config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Profile '{name}' not found.")
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}


def _write_raw_config(name: str, config: Dict[str, Any]) -> None:
    """Write config dict back to YAML."""
    cfg_path = PROFILES_DIR / name / "config.yaml"
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def add_web_source(profile_name: str, url: str) -> str:
    """
    Add a web URL to an existing profile.

    - If the profile has no domain yet, sets it from the URL.
    - If the URL is on the same domain, adds its path to allowed_paths.
    - If different domain, raises ValueError with guidance.

    Returns a description of what changed.
    """
    if not profile_exists(profile_name):
        raise FileNotFoundError(f"Profile '{profile_name}' not found.")

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    new_domain = f"{parsed.scheme}://{parsed.netloc}"
    new_path = parsed.path or "/"

    config = _read_raw_config(profile_name)
    source = config.setdefault("source", {})
    existing_domain = source.get("domain", "")

    if not existing_domain:
        # No domain set yet — set it
        source["type"] = "web" if source.get("type") != "mixed" else "mixed"
        source["domain"] = new_domain
        source["allowed_paths"] = [new_path] if new_path != "/" else ["/"]
        source.setdefault("depth", 2)
        source.setdefault("respect_robots", True)
        _write_raw_config(profile_name, config)
        return f"Set domain to {new_domain} with path {new_path}"

    if new_domain.rstrip("/") == existing_domain.rstrip("/"):
        # Same domain — add path
        paths_list = source.get("allowed_paths", ["/"])
        if new_path not in paths_list:
            paths_list.append(new_path)
            source["allowed_paths"] = paths_list
            _write_raw_config(profile_name, config)
            return f"Added path {new_path} to {existing_domain}"
        else:
            return f"Path {new_path} already exists for {existing_domain}"
    else:
        raise ValueError(
            f"Profile '{profile_name}' uses domain {existing_domain} but URL is on {new_domain}. "
            f"Create a new profile for a different domain: docsai init --name <name> --source-type web --domain {new_domain}"
        )


def add_local_source(profile_name: str, path: str) -> str:
    """
    Add a local path to an existing profile.

    - If source type is "web", changes to "mixed".
    - Appends to source.local_paths.

    Returns a description of what changed.
    """
    if not profile_exists(profile_name):
        raise FileNotFoundError(f"Profile '{profile_name}' not found.")

    abs_path = str(Path(path).resolve())

    config = _read_raw_config(profile_name)
    source = config.setdefault("source", {})

    # If currently web-only, upgrade to mixed
    if source.get("type") == "web":
        source["type"] = "mixed"

    if not source.get("type"):
        source["type"] = "local"

    local_paths = source.get("local_paths", [])
    if abs_path not in local_paths:
        local_paths.append(abs_path)
        source["local_paths"] = local_paths
        source.setdefault("file_types", ["all"])
        _write_raw_config(profile_name, config)
        return f"Added local path: {abs_path}"
    else:
        return f"Path already exists: {abs_path}"


# ---------------------------------------------------------------------------
# Removal
# ---------------------------------------------------------------------------

def remove_profile(name: str) -> None:
    """Delete a profile directory entirely."""
    import gc

    profile_dir = PROFILES_DIR / name
    if not profile_dir.exists():
        raise FileNotFoundError(f"Profile '{name}' not found.")

    # Force-close any lingering ChromaDB connections (Windows SQLite lock issue)
    try:
        import chromadb
        # Trigger garbage collection to release SQLite handles
        gc.collect()
    except ImportError:
        pass

    shutil.rmtree(profile_dir, ignore_errors=False)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def dir_size(path: Path) -> int:
    """Recursive directory size in bytes."""
    if not path.exists():
        return 0
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                pass
    return total


def human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    if size_bytes == 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
