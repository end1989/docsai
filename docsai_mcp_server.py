#!/usr/bin/env python
"""
DocsAI MCP Server — one instance per profile, direct search (no FastAPI needed).

Usage:
    python docsai_mcp_server.py <profile_name>

Each profile becomes its own MCP server with a search tool scoped to that
knowledge base. Configure in claude_desktop_config.json / mcp_config.json:

    "docsai-stripe": {
        "command": "python",
        "args": ["docsai_mcp_server.py", "stripe"]
    }
"""

import sys
import os
from pathlib import Path

# Allow override for when profiles are stored elsewhere
if "--profiles-dir" in sys.argv:
    idx = sys.argv.index("--profiles-dir")
    _profiles_dir = sys.argv[idx + 1]
    sys.argv.pop(idx)  # remove flag
    sys.argv.pop(idx)  # remove value
    os.chdir(_profiles_dir)
else:
    # Default: project root (where profiles/ lives)
    os.chdir(str(Path(__file__).resolve().parent))

# Ensure project root is on sys.path so `docsai.*` imports work
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mcp.server.fastmcp import FastMCP
from docsai.config_loader import load_config, profile_paths
from docsai.retriever.search import search as search_docs

# ---------------------------------------------------------------------------
# Resolve profile from CLI args
# ---------------------------------------------------------------------------
if len(sys.argv) < 2:
    print("Usage: python docsai_mcp_server.py <profile_name>", file=sys.stderr)
    sys.exit(1)

PROFILE = sys.argv[1]

try:
    CFG = load_config(PROFILE)
    PATHS = profile_paths(PROFILE)
except FileNotFoundError:
    print(f"Error: Profile '{PROFILE}' not found in profiles/", file=sys.stderr)
    sys.exit(1)

DESCRIPTION = CFG.get("description", f"{PROFILE} knowledge base")

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name=f"docsai-{PROFILE}",
    instructions=f"Search the {PROFILE} documentation knowledge base. {DESCRIPTION}",
)


@mcp.tool(
    name=f"search_{PROFILE}_docs",
    description=f"Search the {PROFILE} knowledge base. {DESCRIPTION}",
)
def search_knowledge(query: str) -> str:
    """Run hybrid BM25 + embedding search and return passages with sources."""
    results = search_docs(CFG, PATHS, query)

    if not results:
        return f"No results found in {PROFILE} knowledge base for: {query}"

    parts = []
    for i, (_doc_id, passage, meta) in enumerate(results, 1):
        source = meta.get("source_url", "unknown")
        parts.append(f"[{i}] {passage.strip()}\n    Source: {source}")

    return "\n\n---\n\n".join(parts)


@mcp.tool(
    name=f"{PROFILE}_profile_info",
    description=f"Get info about the {PROFILE} knowledge base (source, settings, stats).",
)
def profile_info() -> str:
    """Return profile configuration summary."""
    import chromadb
    from chromadb.config import Settings

    client = chromadb.Client(
        Settings(is_persistent=True, persist_directory=str(PATHS["chroma"]))
    )
    coll = client.get_or_create_collection("docs")
    count = coll.count()

    source = CFG.get("source", {})
    return (
        f"Profile: {PROFILE}\n"
        f"Description: {DESCRIPTION}\n"
        f"Source type: {source.get('type', 'unknown')}\n"
        f"Domain: {source.get('domain', 'N/A')}\n"
        f"Indexed chunks: {count}\n"
        f"Retrieval: BM25 top-{CFG['retrieval']['k_bm25']} + "
        f"Embedding top-{CFG['retrieval']['k_embed']} → "
        f"combined top-{CFG['retrieval']['combine_top_k']}"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
