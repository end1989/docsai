# DocsAI

**Turn any documentation into an AI expert in minutes.**

DocsAI is a local-first RAG engine that crawls, indexes, and searches documentation so you don't have to. Point it at a website, a folder of PDFs, or an OpenAPI spec — it builds a knowledge base, runs hybrid search, and gives you cited answers. No cloud. No API keys for search. Everything on your machine.

It also ships as an **MCP server**, so Claude (or any MCP client) can query your knowledge bases as native tools. Each knowledge base is its own isolated MCP server. Stripe docs, internal wiki, framework reference — each one becomes a tool your AI assistant can call.

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

- **Hybrid retrieval** — BM25 keyword matching + dense semantic embeddings, merged and deduplicated. Catches both exact terms and conceptual matches.
- **Document intelligence** — Automatically categorizes documents (technical, conversation, reference, API spec) and selects chunking strategies per category.
- **Smart chunking** — Recipes keep ingredients with instructions. API docs keep endpoints with parameters. Conversations keep speaker turns together.
- **Multi-mode prompting** — Auto-detects question intent and switches persona: comprehensive expert, integration guide, debugger, or educator.
- **Incremental updates** — Content-hash tracking means re-ingestion only processes what changed.

---

## 3 Minutes to an AI Expert

### 1. Install

```bash
git clone https://github.com/yourusername/docsai && cd docsai
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Create a Profile

```yaml
# profiles/stripe/config.yaml
name: stripe
description: Stripe API Documentation knowledge base
source:
  type: web
  domain: https://docs.stripe.com
  allowed_paths: ["/api", "/docs", "/payments"]
  depth: 2
model:
  llm:
    mode: ollama
    ollama_model: qwen2.5:14b-instruct
  embedding:
    hf_name: BAAI/bge-base-en-v1.5
```

### 3. Ingest & Ask

```bash
python -m docsai.main ingest stripe    # Crawls, chunks, embeds, indexes
python -m docsai.main ask stripe "How do I create a checkout session?"
```

That's it. You now have a Stripe API expert.

---

## Use as an MCP Server

Each profile runs as its own MCP server. No FastAPI backend needed — it searches the vector store directly.

Add to your Claude Code config or `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "docsai-stripe": {
      "command": "/path/to/docsai/.venv/Scripts/python.exe",
      "args": ["/path/to/docsai/docsai_mcp_server.py", "stripe"]
    },
    "docsai-petstore": {
      "command": "/path/to/docsai/.venv/Scripts/python.exe",
      "args": ["/path/to/docsai/docsai_mcp_server.py", "petstore"]
    }
  }
}
```

Now Claude has `search_stripe_docs` and `search_petstore_docs` as native tools. Ask it anything about those APIs and it retrieves from your indexed knowledge base — with citations.

Want another expert? Create a profile, ingest, add the MCP entry. Done.

---

## The Retrieval Pipeline

Every query runs through a two-stage ranking system:

```
Question
  |
  ├──→ BM25 Sparse Ranking (keyword matching via rank-bm25)
  |        Top 40 candidates
  |
  ├──→ Dense Embedding Ranking (cosine similarity via BAAI/bge-base-en-v1.5)
  |        Top 40 candidates
  |
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

DocsAI doesn't just retrieve — it adapts. Questions are classified by intent and routed to specialized prompt personas:

| Mode | Triggers | Behavior |
|------|----------|----------|
| **Comprehensive** | Default | Deep expert analysis, connects dots across docs |
| **Integration** | "How do I implement...", "Build...", "Create..." | Step-by-step with code, error handling, security |
| **Debugging** | "Error...", "Failed...", "Not working..." | Root cause diagnosis, multiple solutions, prevention |
| **Learning** | "Explain...", "What is...", "Why does..." | Educational, builds understanding from fundamentals |

Override with `?mode=debugging` or let it auto-detect from your question.

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

Start the server with `python -m docsai.main serve <profile>` for a full REST API:

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

---

## Configuration Reference

```yaml
name: my-docs
description: What this knowledge base contains

source:
  type: web                            # web | local | mixed | openapi
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

## Utility Scripts

| Script | What it does |
|--------|-------------|
| `scripts/diagnose_rag_quality.py` | Runs test questions and evaluates answer quality |
| `scripts/monitor_ingestion.py` | Real-time ingestion progress watcher |
| `scripts/clear_chroma.py` | Wipe a profile's vector store for fresh re-indexing |
| `scripts/ingestion_status.py` | Check current ingestion state |
| `scripts/schedule_ingestion.py` | Scheduled periodic re-ingestion |

---

## Requirements

- **Python 3.11+**
- **Ollama** (or llama.cpp) with a chat model
- ~2GB disk for the embedding model (downloaded once)
- Vector store grows with your docs (~1MB per 1000 chunks)

---

## License

[MIT](LICENSE)
