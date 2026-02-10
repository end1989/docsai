import yaml
from pathlib import Path

_DEFAULTS = {
    "retrieval": {"k_bm25": 40, "k_embed": 40, "combine_top_k": 10},
    "ingest": {"chunk_tokens": 800, "chunk_overlap": 120, "min_text_len": 180},
    "server": {"port": 8080, "cors_origins": ["http://localhost:5175"]},
    "model": {
        "llm": {"path": "", "n_ctx": 120000, "n_gpu_layers": 999, "llama_binary": ""},
        "embedding": {"hf_name": "BAAI/bge-base-en-v1.5"},
    },
}

def load_config(profile: str):
    cfg_path = Path("profiles") / profile / "config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"No config found for profile {profile}")
    cfg = yaml.safe_load(cfg_path.read_text())
    return _merge(_DEFAULTS, cfg)

def _merge(a, b):
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out

def profile_paths(profile: str):
    base = Path("profiles") / profile
    data = base / "data"
    chroma = data / "chroma"
    cache = base / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    chroma.mkdir(parents=True, exist_ok=True)
    return {"base": base, "data": data, "chroma": chroma, "cache": cache}
