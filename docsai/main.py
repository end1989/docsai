import typer, uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
import yaml
import os
import sys
import json
import traceback

from .config_loader import load_config, profile_paths
from .retriever.ingest import ingest_profile
from .retriever.search import search as search_docs
from .logger import server_logger
from .profile_ops import (
    validate_profile_name,
    profile_exists,
    discover_profiles,
    get_profile_summary,
    create_profile_on_disk,
    add_web_source,
    add_local_source,
    remove_profile as remove_profile_op,
    human_size,
)
from rich.console import Console
from rich.table import Table
# Use supercharged LLM runner for comprehensive responses
try:
    from .llm_runner_supercharged import run_llm, detect_prompt_mode
except ImportError:
    # Fallback to original if supercharged not available
    from .llm_runner import run_llm
    detect_prompt_mode = lambda x: "comprehensive"
from .guards.validator import validate_answer
from .ingestion_manager import ingestion_manager

app = FastAPI(title="DocsAI Local")
cli = typer.Typer(help="DocsAI command line")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status")
def status():
    return {"ok": True, "message": "DocsAI backend running."}

class AskResponse(BaseModel):
    answer: str
    citations: list[str]

class ProfileCreateRequest(BaseModel):
    name: str
    sourceType: str  # 'web', 'local', or 'mixed'
    webDomains: Optional[List[str]] = []
    localPaths: Optional[List[str]] = []
    fileTypes: Optional[List[str]] = ['all']
    crawlDepth: int = 2
    chunkSize: int = 800
    description: Optional[str] = ""

# Global variables to store config and profile
global_cfg = None
global_profile = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/profiles/create")
async def create_profile(request: ProfileCreateRequest):
    """Create a new profile configuration."""
    try:
        # Resolve web domain
        domain = None
        if request.webDomains and any(request.webDomains):
            domain = request.webDomains[0].rstrip("/")

        profile_dir = create_profile_on_disk(
            name=request.name,
            description=request.description or f"Profile for {request.name}",
            source_type=request.sourceType,
            domain=domain,
            depth=request.crawlDepth,
            local_paths=request.localPaths if request.localPaths else None,
            file_types=request.fileTypes if request.fileTypes else None,
        )

        return JSONResponse(content={
            "success": True,
            "profile": request.name,
            "path": str(profile_dir),
            "message": f"Profile '{request.name}' created successfully. Run 'python -m docsai.main ingest {request.name}' to index content."
        })

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/list")
async def list_profiles():
    """List all available profiles."""
    profiles = []
    for name in discover_profiles():
        try:
            s = get_profile_summary(name)
            profiles.append({
                "name": s["name"],
                "description": s["description"],
                "source_type": s["source_type"],
                "path": str(Path("profiles") / name),
            })
        except Exception:
            pass

    return JSONResponse(content={"profiles": profiles})

@app.post("/ingestion/start/{profile_name}")
async def start_ingestion(profile_name: str):
    """Start ingestion for a profile."""
    try:
        # Load the profile config
        config = load_config(profile_name)

        # Start ingestion task
        task_id = ingestion_manager.start_ingestion(profile_name, config)

        return JSONResponse(content={
            "success": True,
            "task_id": task_id,
            "message": f"Ingestion started for profile '{profile_name}'"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingestion/status/{task_id}")
async def get_ingestion_status(task_id: str):
    """Get the status of an ingestion task."""
    status = ingestion_manager.get_task_status(task_id)

    if not status:
        raise HTTPException(status_code=404, detail="Task not found")

    return JSONResponse(content=status)

@app.get("/ingestion/active")
async def get_active_ingestion():
    """Get the currently active ingestion task if any."""
    active_task = ingestion_manager.get_active_task()
    return JSONResponse(content={"active_task": active_task})

@app.post("/ingestion/cancel/{task_id}")
async def cancel_ingestion(task_id: str):
    """Cancel a running ingestion task."""
    success = ingestion_manager.cancel_task(task_id)

    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel task - it may not be running")

    return JSONResponse(content={
        "success": True,
        "message": f"Cancellation requested for task {task_id}"
    })

@app.post("/cache/clear/{profile_name}")
async def clear_cache(profile_name: str):
    """Clear the cache for a specific profile."""
    import shutil
    from pathlib import Path

    try:
        # Get the cache path for this profile
        cache_dir = Path(f"profiles/{profile_name}/cache")

        if not cache_dir.exists():
            return JSONResponse(content={
                "success": True,
                "message": f"No cache found for profile '{profile_name}'"
            })

        # Remove the cache directory and recreate it
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Also create the required subdirectories
        (cache_dir / "html").mkdir(exist_ok=True)
        (cache_dir / "metadata").mkdir(exist_ok=True)

        print(f"[INFO] Cleared cache for profile: {profile_name}")
        server_logger.info(f"Cleared cache for profile: {profile_name}")

        return JSONResponse(content={
            "success": True,
            "message": f"Cache cleared successfully for profile '{profile_name}'"
        })
    except Exception as e:
        server_logger.error(f"Failed to clear cache for {profile_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.delete("/profiles/{profile_name}")
async def delete_profile(profile_name: str):
    """Delete a profile and all its data."""
    try:
        remove_profile_op(profile_name)
        server_logger.info(f"Deleted profile: {profile_name}")
        return JSONResponse(content={
            "success": True,
            "message": f"Profile '{profile_name}' deleted successfully"
        })
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' not found")
    except Exception as e:
        server_logger.error(f"Failed to delete profile {profile_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")

@app.get("/profile/{profile_name}/stats")
async def get_profile_stats(profile_name: str):
    """Get statistics for a specific profile."""
    from pathlib import Path
    import json

    try:
        # Check if profile exists
        profile_dir = Path(f"profiles/{profile_name}")
        if not profile_dir.exists():
            raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' not found")

        stats = {
            "profile": profile_name,
            "totalDocuments": 0,
            "totalChunks": 0,
            "lastIngestion": None,
            "categories": {},
            "cacheSize": 0,
            "dataSize": 0
        }

        # Check for ingestion metadata
        metadata_file = profile_dir / "cache" / "metadata" / "ingestion_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    stats["lastIngestion"] = metadata.get("last_ingestion")
                    stats["totalDocuments"] = metadata.get("total_documents", 0)
            except:
                pass

        # Check ChromaDB for chunk count
        try:
            chroma_dir = profile_dir / "data" / "chroma"
            if chroma_dir.exists():
                # This is a rough estimate - actual implementation would query ChromaDB
                import chromadb
                from chromadb.config import Settings

                client = chromadb.PersistentClient(
                    path=str(chroma_dir),
                    settings=Settings(anonymized_telemetry=False)
                )

                try:
                    collection = client.get_collection(name=f"{profile_name}_docs")
                    count = collection.count()
                    stats["totalChunks"] = count

                    # Get category distribution if available
                    # For now, using estimated categories
                    if count > 0:
                        stats["categories"] = {
                            "technical": int(count * 0.57),
                            "api_reference": int(count * 0.25),
                            "guide": int(count * 0.18)
                        }
                except Exception as e:
                    server_logger.debug(f"Could not get collection stats: {e}")
                    # Use placeholder values if collection doesn't exist yet
                    stats["totalChunks"] = 0
                    stats["categories"] = {}

        except ImportError:
            server_logger.debug("ChromaDB not available for stats")

        # Calculate cache size
        cache_dir = profile_dir / "cache"
        if cache_dir.exists():
            cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            stats["cacheSize"] = cache_size

        # Calculate data size
        data_dir = profile_dir / "data"
        if data_dir.exists():
            data_size = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file())
            stats["dataSize"] = data_size

        return JSONResponse(content=stats)

    except Exception as e:
        server_logger.error(f"Failed to get stats for {profile_name}: {str(e)}")
        # Return default stats rather than error
        return JSONResponse(content={
            "profile": profile_name,
            "totalDocuments": 0,
            "totalChunks": 0,
            "lastIngestion": None,
            "categories": {},
            "cacheSize": 0,
            "dataSize": 0
        })

@app.post("/profile/switch/{profile_name}")
async def switch_profile(profile_name: str):
    """Switch to a different profile without restarting."""
    global global_cfg, global_profile

    try:
        # Load the new profile config
        cfg = load_config(profile_name)
        global_cfg = cfg
        global_profile = profile_name

        return JSONResponse(content={
            "success": True,
            "profile": profile_name,
            "message": f"Switched to profile '{profile_name}'"
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to switch profile: {str(e)}")

@app.get("/ask", response_model=AskResponse)
def ask_http(
    q: str = Query(..., description="User question"),
    mode: str = Query(None, description="Prompt mode: comprehensive, integration, debugging, or learning"),
    supercharged: bool = Query(True, description="Use supercharged prompts for comprehensive answers")
):
    server_logger.info(f"Received /ask request with query: {q}")
    try:
        # Check if config is loaded
        if global_cfg is None or global_profile is None:
            server_logger.error("Config not loaded - global_cfg or global_profile is None")
            return JSONResponse(
                status_code=500,
                content={
                    "answer": "",
                    "citations": [],
                    "error": "Server not initialized. Please start with 'python -m docsai.main serve <profile>'"
                },
            )

        server_logger.debug(f"Processing question: {q}")
        server_logger.debug(f"Profile: {global_profile}")

        # Get passages using the search function
        paths = profile_paths(global_profile)
        server_logger.debug(f"Paths: {paths}")

        search_results = search_docs(global_cfg, paths, q)
        server_logger.debug(f"Found {len(search_results)} search results")

        # Debug: print first result structure
        if search_results:
            server_logger.debug(f"First result structure: {len(search_results[0])} elements")
            if len(search_results[0]) >= 3:
                server_logger.debug(f"First result metadata: {search_results[0][2]}")

        # Extract passages and URLs from metadata
        passages = []
        cite_urls = []
        seen_urls = set()  # Track unique URLs

        for result in search_results[:12]:  # Limit to top 12 passages
            if len(result) == 3:
                doc_id, passage, metadata = result
            else:
                doc_id, passage = result
                metadata = {}

            passages.append(passage)

            # Get URL from metadata if available
            if metadata and 'source_url' in metadata:
                url = metadata['source_url']
                if url not in seen_urls:
                    cite_urls.append(url)
                    seen_urls.add(url)
                    server_logger.debug(f"Added citation: {url}")

        server_logger.debug(f"Extracted {len(passages)} passages")
        server_logger.debug(f"Final citations list: {cite_urls}")

        if not passages:
            # No passages found, return a helpful message
            return JSONResponse(
                content={
                    "answer": "No relevant documentation found for your question. The database might be empty or need to be populated with 'python -m docsai.main ingest stripe'",
                    "citations": []
                },
                media_type="application/json",
            )

        # Run LLM with the passages
        server_logger.debug(f"Running LLM with {len(passages)} passages")
        # Auto-detect mode if not specified
        if mode is None and supercharged:
            mode = detect_prompt_mode(q)
            server_logger.debug(f"Auto-detected prompt mode: {mode}")

        # Pass supercharged and mode parameters
        text = run_llm(global_cfg, q, passages, supercharged=supercharged, prompt_mode=mode)

        # Normalize output
        answer = (text or "").strip()
        if not answer:
            answer = "Unable to generate an answer. Please check if the LLM is properly configured."

        # If the answer indicates nothing was found, don't return citations
        if "not found in the provided documentation" in answer.lower():
            cite_urls = []
            server_logger.debug("Answer is 'not found', clearing citations")

        # Extract any citation numbers from the answer (e.g., [1], [2])
        # and map them to actual URLs
        import re
        citation_pattern = r'\[(\d+)\]'
        citations_in_answer = re.findall(citation_pattern, answer)

        if citations_in_answer:
            # Only include URLs that are actually referenced in the answer
            referenced_urls = []
            for cite_num in citations_in_answer:
                idx = int(cite_num) - 1  # Convert to 0-based index
                if 0 <= idx < len(cite_urls):
                    if cite_urls[idx] not in referenced_urls:
                        referenced_urls.append(cite_urls[idx])
            cite_urls = referenced_urls
            server_logger.debug(f"Found citations in answer: {citations_in_answer}, mapped to {len(cite_urls)} URLs")

        return JSONResponse(
            content={"answer": answer, "citations": cite_urls},
            media_type="application/json",
        )
    except Exception as e:
        server_logger.error(f"Exception in /ask endpoint: {str(e)}")
        server_logger.error(f"Traceback: {traceback.format_exc()}")
        # Make failure visible to the UI instead of silent
        return JSONResponse(
            status_code=500,
            content={
                "answer": "",
                "citations": [],
                "error": str(e),
            },
        )

@cli.command()
def serve(profile: str = typer.Argument(..., help="Profile name (e.g. stripe)")):
    global global_cfg, global_profile

    # Load config and set global variables
    cfg = load_config(profile)
    global_cfg = cfg
    global_profile = profile

    # CORS
    origins = cfg.get("server", {}).get("cors_origins", ["http://localhost:5175"])
    # Note: We're re-adding middleware, but FastAPI handles duplicates gracefully

    port = cfg.get('server', {}).get('port', 8080)
    server_logger.info(f"Starting server for profile: {profile} on port {port}")
    # Pass the app object directly instead of the string path
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)

@cli.command()
def ingest(profile: str = typer.Argument(..., help="Profile to ingest")):
    cfg = load_config(profile)
    paths = profile_paths(profile)
    ingest_profile(profile, cfg, paths)

@cli.command()
def ask(profile: str = typer.Argument(...), question: str = typer.Argument(...)):
    cfg = load_config(profile)
    paths = profile_paths(profile)
    search_results = search_docs(cfg, paths, question)
    # Handle both 2-tuple and 3-tuple formats
    passages = []
    for result in search_results:
        if len(result) == 3:
            _id, passage, _metadata = result
        else:
            _id, passage = result
        passages.append(passage)
    ans = run_llm(cfg, question, passages[:12])
    print(ans)

# ---------------------------------------------------------------------------
# New CLI commands: profile management
# ---------------------------------------------------------------------------

console = Console()

@cli.command()
def init(
    name: Optional[str] = typer.Option(None, help="Profile name"),
    source_type: Optional[str] = typer.Option(None, "--source-type", help="web, local, or mixed"),
    domain: Optional[str] = typer.Option(None, help="Web domain to crawl"),
    local_path: Optional[str] = typer.Option(None, "--path", help="Local directory path"),
    description: Optional[str] = typer.Option(None, help="Profile description"),
    depth: int = typer.Option(2, help="Crawl depth for web sources"),
):
    """Create a new knowledge base profile."""
    # Interactive prompts for missing values
    if not name:
        name = typer.prompt("Profile name")
    if not validate_profile_name(name):
        console.print(f"[red]Invalid name '{name}'. Use alphanumeric, dashes, or underscores.[/red]")
        raise typer.Exit(1)
    if profile_exists(name):
        console.print(f"[red]Profile '{name}' already exists.[/red]")
        raise typer.Exit(1)

    if not source_type:
        source_type = typer.prompt("Source type (web/local/mixed)", default="web")
    source_type = source_type.lower().strip()
    if source_type not in ("web", "local", "mixed"):
        console.print(f"[red]Invalid source type '{source_type}'. Use: web, local, or mixed.[/red]")
        raise typer.Exit(1)

    if not description:
        description = typer.prompt("Description", default=f"{name} knowledge base")

    # Source-specific prompts
    allowed_paths = None
    local_paths = None

    if source_type in ("web", "mixed"):
        interactive_web = not domain
        if not domain:
            domain = typer.prompt("Domain to crawl (e.g. https://docs.example.com)")
        if not domain.startswith("http"):
            domain = "https://" + domain
        if interactive_web:
            allowed_input = typer.prompt("Allowed paths (comma-separated, or / for all)", default="/")
            allowed_paths = [p.strip() for p in allowed_input.split(",") if p.strip()]
            depth = typer.prompt("Crawl depth", default=depth, type=int)

    if source_type in ("local", "mixed"):
        if not local_path:
            local_path = typer.prompt("Local directory path")
        resolved = Path(local_path).resolve()
        if not resolved.exists():
            console.print(f"[yellow]Warning: Path '{resolved}' does not exist yet.[/yellow]")
        local_paths = [str(resolved)]

    try:
        profile_dir = create_profile_on_disk(
            name=name,
            description=description,
            source_type=source_type,
            domain=domain,
            allowed_paths=allowed_paths,
            depth=depth,
            local_paths=local_paths,
        )
        console.print(f"\n[green]Created profile '{name}' at {profile_dir}[/green]")
        console.print(f"\nNext step: [bold]python -m docsai.main ingest {name}[/bold]")
    except (ValueError, FileExistsError) as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@cli.command("list")
def list_cmd():
    """List all knowledge base profiles."""
    names = discover_profiles()
    if not names:
        console.print("[yellow]No profiles found.[/yellow]")
        console.print("Create one with: [bold]python -m docsai.main init[/bold]")
        return

    table = Table(title="DocsAI Profiles")
    table.add_column("Profile", style="bold cyan")
    table.add_column("Type")
    table.add_column("Chunks", justify="right")
    table.add_column("Cache", justify="right")
    table.add_column("Description")

    for name in names:
        try:
            s = get_profile_summary(name)
            table.add_row(
                s["name"],
                s["source_type"],
                f"{s['chunk_count']:,}",
                human_size(s["cache_size"]),
                (s["description"][:50] + "...") if len(s["description"]) > 50 else s["description"],
            )
        except Exception as e:
            table.add_row(name, "[red]error[/red]", "-", "-", str(e)[:50])

    console.print(table)


@cli.command()
def status(
    profile: Optional[str] = typer.Argument(None, help="Profile name (omit for all)"),
):
    """Show profile status and statistics."""
    if profile:
        if not profile_exists(profile):
            console.print(f"[red]Profile '{profile}' not found.[/red]")
            raise typer.Exit(1)
        try:
            s = get_profile_summary(profile)
        except Exception as e:
            console.print(f"[red]Error loading profile: {e}[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold cyan]Profile:[/bold cyan] {s['name']}")
        console.print(f"[bold]Description:[/bold]  {s['description']}")
        source_line = s["source_type"]
        if s["domain"]:
            source_line += f" ({s['domain']})"
        console.print(f"[bold]Source:[/bold]       {source_line}")
        if s["allowed_paths"]:
            console.print(f"[bold]Paths:[/bold]        {', '.join(s['allowed_paths'])}")
        if s["local_paths"]:
            console.print(f"[bold]Local paths:[/bold]  {', '.join(s['local_paths'])}")
        console.print(f"[bold]Crawl depth:[/bold]  {s['depth']}")
        console.print(f"[bold]Chunks:[/bold]       {s['chunk_count']:,}")
        console.print(f"[bold]Cache size:[/bold]   {human_size(s['cache_size'])}")
        console.print(f"[bold]Vector store:[/bold] {human_size(s['chroma_size'])}")

        if s["chunk_count"] == 0:
            console.print(f"\n[yellow]No data indexed. Run:[/yellow] [bold]python -m docsai.main ingest {profile}[/bold]")
    else:
        # Show all profiles — delegate to list
        list_cmd()


@cli.command()
def add(
    source: str = typer.Argument(..., help="URL or local path to add"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Target profile"),
):
    """Add a source (URL or local path) to a profile."""
    # Resolve target profile
    if not profile:
        names = discover_profiles()
        if not names:
            console.print("[red]No profiles exist.[/red] Create one first:")
            console.print("  [bold]python -m docsai.main init[/bold]")
            raise typer.Exit(1)
        elif len(names) == 1:
            profile = names[0]
            console.print(f"Using profile: [bold]{profile}[/bold]")
        else:
            console.print("Multiple profiles found. Pick one:")
            for i, n in enumerate(names, 1):
                console.print(f"  {i}. {n}")
            choice = typer.prompt("Profile number", type=int)
            if choice < 1 or choice > len(names):
                console.print("[red]Invalid choice.[/red]")
                raise typer.Exit(1)
            profile = names[choice - 1]

    if not profile_exists(profile):
        console.print(f"[red]Profile '{profile}' not found.[/red]")
        raise typer.Exit(1)

    # Detect source type
    is_url = source.startswith("http://") or source.startswith("https://")

    try:
        if is_url:
            result = add_web_source(profile, source)
        else:
            p = Path(source)
            if not p.exists():
                console.print(f"[yellow]Warning: Path '{source}' does not exist.[/yellow]")
                if not typer.confirm("Add anyway?"):
                    raise typer.Exit(0)
            result = add_local_source(profile, source)

        console.print(f"[green]{result}[/green]")
        console.print(f"\nRe-ingest to index new content: [bold]python -m docsai.main ingest {profile}[/bold]")
    except (ValueError, FileNotFoundError) as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@cli.command()
def remove(
    profile: str = typer.Argument(..., help="Profile to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a profile and all its data."""
    if not profile_exists(profile):
        console.print(f"[red]Profile '{profile}' not found.[/red]")
        raise typer.Exit(1)

    # Show what will be deleted (avoid opening ChromaDB — it locks SQLite on Windows)
    from .profile_ops import dir_size as _dir_size
    paths = profile_paths(profile)
    console.print(f"\n[bold]Profile:[/bold] {profile}")
    console.print(f"  Cache:   {human_size(_dir_size(paths['cache']))}")
    console.print(f"  Vectors: {human_size(_dir_size(paths['chroma']))}")

    if not force:
        if not typer.confirm(f"\nPermanently delete profile '{profile}'?"):
            console.print("Cancelled.")
            raise typer.Exit(0)

    try:
        remove_profile_op(profile)
        console.print(f"[green]Removed profile '{profile}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# MCP subcommand group: docsai mcp install / status / uninstall
# ---------------------------------------------------------------------------

mcp_app = typer.Typer(help="Manage MCP server configuration")
cli.add_typer(mcp_app, name="mcp")


def _resolve_mcp_entries() -> dict:
    """Build MCP server entries for all discovered profiles."""
    names = discover_profiles()
    if not names:
        return {}

    # Resolve paths
    python_exe = sys.executable
    # docsai_mcp_server.py lives in project root (one level above docsai/)
    mcp_script = str(Path(__file__).resolve().parent.parent / "docsai_mcp_server.py")

    entries = {}
    for name in names:
        entries[f"docsai-{name}"] = {
            "command": python_exe,
            "args": [mcp_script, name],
        }
    return entries


def _get_config_path(target: str) -> Path:
    """Return the config file path for a given target."""
    if target == "claude-code":
        return Path.home() / ".claude" / ".mcp.json"
    elif target == "claude-desktop":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    else:
        raise ValueError(f"Unknown target: {target}")


def _read_mcp_config(path: Path) -> dict:
    """Read an MCP config file, returning empty structure if missing."""
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"mcpServers": {}}
    return {"mcpServers": {}}


def _write_mcp_config(path: Path, config: dict) -> None:
    """Write MCP config, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=4) + "\n", encoding="utf-8")


@mcp_app.command("install")
def mcp_install(
    target: str = typer.Option(
        "claude-code",
        help="Target: claude-code or claude-desktop",
    ),
):
    """Install MCP server entries for all profiles."""
    entries = _resolve_mcp_entries()
    if not entries:
        console.print("[yellow]No profiles found.[/yellow] Create one first:")
        console.print("  [bold]docsai init[/bold]")
        return

    # Merge into target config
    config_path = _get_config_path(target)
    config = _read_mcp_config(config_path)
    servers = config.setdefault("mcpServers", {})

    # Remove stale docsai entries, then add current ones
    stale = [k for k in servers if k.startswith("docsai-")]
    for k in stale:
        del servers[k]
    servers.update(entries)

    _write_mcp_config(config_path, config)

    # Also write project-local mcp_config.json for reference
    local_config = {"mcpServers": entries}
    local_path = Path(__file__).resolve().parent.parent / "mcp_config.json"
    _write_mcp_config(local_path, local_config)

    # Summary
    table = Table(title="MCP Servers Installed")
    table.add_column("Server", style="bold cyan")
    table.add_column("Profile")
    table.add_column("Python")
    for key, entry in entries.items():
        profile_name = entry["args"][-1]
        table.add_row(key, profile_name, entry["command"])
    console.print(table)
    console.print(f"\n[green]Wrote {len(entries)} server(s) to {config_path}[/green]")
    if target == "claude-code":
        console.print("[dim]Restart Claude Code to pick up the new tools.[/dim]")


@mcp_app.command("status")
def mcp_status():
    """Show MCP configuration status for all profiles."""
    names = discover_profiles()
    config_path = _get_config_path("claude-code")
    config = _read_mcp_config(config_path)
    servers = config.get("mcpServers", {})

    table = Table(title="MCP Status")
    table.add_column("Profile", style="bold cyan")
    table.add_column("MCP Key")
    table.add_column("Installed", justify="center")
    table.add_column("Path")

    for name in names:
        key = f"docsai-{name}"
        if key in servers:
            cmd = servers[key].get("command", "?")
            table.add_row(name, key, "[green]Yes[/green]", cmd)
        else:
            table.add_row(name, key, "[red]No[/red]", "-")

    # Check for stale entries (MCP entries for deleted profiles)
    stale = [k for k in servers if k.startswith("docsai-") and k.replace("docsai-", "", 1) not in names]
    for key in stale:
        table.add_row(
            key.replace("docsai-", "", 1),
            key,
            "[yellow]Stale[/yellow]",
            servers[key].get("command", "?"),
        )

    console.print(table)
    console.print(f"\n[dim]Config: {config_path}[/dim]")


@mcp_app.command("uninstall")
def mcp_uninstall(
    target: str = typer.Option(
        "claude-code",
        help="Target: claude-code or claude-desktop",
    ),
):
    """Remove all DocsAI MCP server entries."""
    config_path = _get_config_path(target)
    config = _read_mcp_config(config_path)
    servers = config.get("mcpServers", {})

    removed = [k for k in servers if k.startswith("docsai-")]
    if not removed:
        console.print("[yellow]No DocsAI MCP entries found.[/yellow]")
        return

    for k in removed:
        del servers[k]

    _write_mcp_config(config_path, config)

    console.print(f"[green]Removed {len(removed)} DocsAI MCP server(s):[/green]")
    for k in removed:
        console.print(f"  - {k}")
    console.print(f"\n[dim]Updated: {config_path}[/dim]")


if __name__ == "__main__":
    cli()
