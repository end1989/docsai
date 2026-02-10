<div align="center">

# DocsAI

**Turn any documentation into an AI expert in minutes.**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-14B8A6?style=flat-square)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F61?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-Server-8B5CF6?style=flat-square&logo=anthropic&logoColor=white)

A local-first RAG engine that crawls, indexes, and searches documentation so you don't have to. Point it at a website, a folder of PDFs, or an OpenAPI spec — it builds a knowledge base, runs hybrid search, and gives you cited answers.

No cloud. No API keys for search. Everything on your machine.

[Getting Started](#getting-started) · [Web UI](#web-ui) · [MCP Server](#use-as-an-mcp-server) · [CLI](#cli-reference) · [API](#rest-api) · [Configuration](#configuration-reference)

</div>

---

## What It Actually Does

```
You: "How do I implement webhook signature verification in Stripe?"

DocsAI: Here's the complete implementation...
        [1] Use stripe.webhooks.constructEvent() with your endpoint secret...
        [2] Always verify signatures before processing events...
        [3] Return 200 quickly, then process asynchronously...

        Sources:
        [1] https://docs.stripe.com/webhooks/signatures
        [2] https://docs.stripe.com/webhooks/best-practices
        [3] https://docs.stripe.com/webhooks#async-processing
```

Real answers. Real citations. From docs it crawled and indexed locally.

---

## Why This Exists

LLMs hallucinate. Context windows overflow. Copy-pasting docs into prompts doesn't scale.

DocsAI solves this by building a **persistent, searchable vector store** from your actual documentation, then retrieving only the relevant passages for each question. The LLM generates answers grounded in real source material — and every claim links back to where it came from.

This isn't a toy wrapper around an embedding API. It's a full pipeline:

- **Hybrid retrieval** — BM25 keyword matching + dense semantic embeddings, merged and deduplicated
- **Document intelligence** — Auto-categorizes documents and selects chunking strategies per category
- **Smart chunking** — API docs keep endpoints with parameters, conversations keep speaker turns together
- **Multi-mode prompting** — Auto-detects question intent: comprehensive, integration, debugging, or learning
- **Incremental updates** — Content-hash tracking means re-ingestion only processes what changed

---

## Getting Started

### Install

```bash
git clone https://github.com/end1989/docsai && cd docsai
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -e .                                 # Installs docsai CLI
```

### Create a Profile & Ingest

```bash
docsai init stripe --domain https://docs.stripe.com --depth 2
docsai ingest stripe       # Crawls, chunks, embeds, indexes
docsai ask stripe "How do I create a checkout session?"
```

That's it. You now have a Stripe API expert.

### Start the Web UI

```bash
docsai serve stripe        # Backend on :8080
cd ui && npm install && npm run dev  # Frontend on :5173
```

---

## Web UI

DocsAI ships with a full **React + TypeScript + Tailwind CSS** dashboard for managing everything through the browser.

```
+===================================================================+
| [DocsAI]                         [Profile: stripe v]  [+]  [*]   |
+===================================================================+
| [Chat]  [Dashboard]                                               |
+-------------------------------------------------------------------+
|                                                                   |
|  CHAT VIEW:                                                       |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │ Q: How do I verify webhook signatures?                      │  |
|  │ ─────────────────────────────────────────────────────────── │  |
|  │ A: To verify webhook signatures...  [formatted markdown]   │  |
|  │ Sources: [1] docs.stripe.com/webhooks/signatures           │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                                                                   |
|  DASHBOARD VIEW:                                                  |
|  ┌──────────────────┐  ┌──────────────────────────────────────┐  |
|  │ PROFILE INFO     │  │ INGESTION                            │  |
|  │ Stripe API Docs  │  │ [Start Ingestion]                    │  |
|  │ web · stripe.com │  │ Status: processing  [=====>--] 47%   │  |
|  └──────────────────┘  │ Files: 234/500 · chunks.html         │  |
|  ┌──────┐┌──────┐┌──┐ │ [Cancel]                              │  |
|  │1,933 ││12 MB ││48M│ └──────────────────────────────────────┘  |
|  │chunks││cache ││vec│                                            |
|  └──────┘└──────┘└──┘                                             |
+-------------------------------------------------------------------+
```

**Features:**
- Chat with your docs — formatted markdown answers with clickable citations
- Switch between profiles on the fly
- Create new profiles from the UI
- Start/cancel ingestion with real-time progress tracking
- Dashboard with chunk count, cache size, vector store stats
- Dark theme (because we build at night)

---

## Use as an MCP Server

Each profile runs as its own MCP server. Claude (or any MCP client) can query your knowledge bases as native tools.

### Auto-install (recommended)

```bash
docsai mcp install     # Adds all profiles to Claude Code
docsai mcp status      # Check what's installed
docsai mcp uninstall   # Clean removal
```

This merges into your existing `~/.claude/.mcp.json` without touching other servers.

### Manual config

Add to `claude_desktop_config.json` or `.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "docsai-stripe": {
      "command": "/path/to/.venv/Scripts/python.exe",
      "args": ["/path/to/docsai_mcp_server.py", "stripe"]
    }
  }
}
```

Now Claude has `search_stripe_docs` as a native tool. Ask it anything about the Stripe API and it retrieves from your indexed knowledge base — with citations.

---

## The Retrieval Pipeline

Every query runs through a two-stage ranking system:

```
Question
  │
  ├──→ BM25 Sparse Ranking (keyword matching via rank-bm25)
  │        Top 40 candidates
  │
  ├──→ Dense Embedding Ranking (cosine similarity via BAAI/bge-base-en-v1.5)
  │        Top 40 candidates
  │
  └──→ Merge + Deduplicate
           Top 10 passages → LLM with citations
```

BM25 catches exact terminology ("PaymentIntent", "webhook_endpoint_secret"). Embeddings catch semantics ("how to handle failed payments" matches docs about decline codes). Together they cover what either would miss alone.

---

## What It Can Ingest

| Source Type | Formats |
|------------|---------|
| **Web** | Any website with depth-limited crawling, robots.txt respect, local caching |
| **Documents** | PDF, DOCX, DOC, Markdown, plain text, RST, LaTeX |
| **Data** | JSON, CSV, YAML, XML |
| **Code** | Any source file with syntax-aware chunking |
| **Books** | EPUB with chapter boundary preservation |
| **Email** | .eml and .msg with thread-aware chunking |
| **APIs** | OpenAPI/Swagger specs with endpoint-aware splitting |
| **Web archives** | Raw HTML with boilerplate removal |

15+ formats. Each gets a category-specific chunking strategy so context isn't lost at chunk boundaries.

---

## Multi-Mode Expert System

Questions are classified by intent and routed to specialized prompt personas:

| Mode | Triggers | Behavior |
|------|----------|----------|
| **Comprehensive** | Default | Deep expert analysis, connects dots across docs |
| **Integration** | "How do I implement...", "Build...", "Create..." | Step-by-step with code, error handling, security |
| **Debugging** | "Error...", "Failed...", "Not working..." | Root cause diagnosis, multiple solutions, prevention |
| **Learning** | "Explain...", "What is...", "Why does..." | Educational, builds understanding from fundamentals |

Override with `?mode=debugging` or let it auto-detect from your question.

---

## CLI Reference

```bash
docsai init <name>           # Create a new profile
docsai list                  # List all profiles with stats
docsai add <profile> <url>   # Add a source to a profile
docsai status <profile>      # Show profile details
docsai remove <profile>      # Delete a profile

docsai serve <profile>       # Start the API server
docsai ingest <profile>      # Run ingestion via CLI
docsai ask <profile> "..."   # Ask a question via CLI

docsai mcp install           # Install MCP servers into Claude
docsai mcp status            # Show MCP installation state
docsai mcp uninstall         # Remove MCP servers from Claude
```

---

## Profile System

Each knowledge base is fully isolated:

```
profiles/
  stripe/
    config.yaml          # Source config, retrieval params, LLM settings
    cache/               # Crawled pages (HTML, metadata)
    data/chroma/         # Persistent vector store
  internal-wiki/
    config.yaml
    cache/
    data/chroma/
```

Profiles don't share state. You can have a Stripe expert, a React expert, and an internal docs expert all running simultaneously as separate MCP servers.

---

## REST API

Start with `docsai serve <profile>`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ask?q=<question>&mode=<mode>` | GET | Query with optional mode override |
| `/ingestion/start/{profile}` | POST | Start background ingestion |
| `/ingestion/status/{task_id}` | GET | Poll ingestion progress |
| `/ingestion/cancel/{task_id}` | POST | Cancel running ingestion |
| `/profiles/create` | POST | Create a new profile |
| `/profiles/list` | GET | List all profiles |
| `/profile/switch/{name}` | POST | Switch active profile |
| `/profile/{name}/stats` | GET | Profile statistics |
| `/health` | GET | Backend health check |

---

## Configuration Reference

```yaml
name: my-docs
description: What this knowledge base contains

source:
  type: web                            # web | local | mixed
  domain: https://docs.example.com     # For web sources
  allowed_paths: ["/api", "/guides"]   # Restrict crawl scope
  depth: 2                             # Crawl depth limit
  respect_robots: true                 # Honor robots.txt
  local_paths: ["./docs"]              # For local sources
  file_types: ["pdf", "md", "docx"]   # Filter file types

ingest:
  chunk_tokens: 800                    # Target chunk size
  chunk_overlap: 120                   # Overlap between chunks
  min_text_len: 180                    # Skip tiny chunks

retrieval:
  k_bm25: 40                          # BM25 candidates
  k_embed: 40                         # Embedding candidates
  combine_top_k: 10                   # Final passages to LLM

model:
  llm:
    mode: ollama                       # ollama | llamacpp
    ollama_model: qwen2.5:14b-instruct
    temperature: 0.2
  embedding:
    hf_name: BAAI/bge-base-en-v1.5

server:
  port: 8080
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Retrieval** | BM25 (rank-bm25) + dense embeddings (sentence-transformers, BAAI/bge-base-en-v1.5) |
| **Vector Store** | ChromaDB (persistent, on-disk) |
| **LLM** | Ollama or llama.cpp (local inference, no API keys) |
| **Backend** | FastAPI, Python 3.11+ |
| **Frontend** | React 19, TypeScript, Vite 6, Tailwind CSS 4 |
| **CLI** | Typer + Rich |
| **MCP** | FastMCP SDK, stdio transport |
| **Document Processing** | BeautifulSoup, markdownify, custom parsers for 15+ formats |

---

## Requirements

- **Python 3.11+**
- **Node.js 18+** (for the Web UI)
- **Ollama** (or llama.cpp) with a chat model
- ~2GB disk for the embedding model (downloaded once)
- Vector store grows with your docs (~1MB per 1000 chunks)

---
<img width="836" height="810" alt="Screenshot 2026-02-10 041038" src="https://github.com/user-attachments/assets/8342d00c-a1a1-4791-831d-630d2f0d278b" />

<img width="1027" height="1169" alt="Screenshot 2026-02-10 040522" src="https://github.com/user-attachments/assets/38eba43d-6013-492e-a46d-9459cfd7dd73" />

<img width="1033" height="1283" alt="Screenshot 2026-02-10 040812" src="https://github.com/user-attachments/assets/9d11bd4e-38ea-48ed-834a-d257f89db8eb" />

## License[MIT](LICENSE)
