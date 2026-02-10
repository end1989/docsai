# How to Use DocsAI

A step-by-step guide to turning any documentation into a searchable, AI-powered knowledge base.

---

## What is DocsAI?

DocsAI lets you point at a website or a folder of documents, ingest them, and then ask questions in plain English. It finds the most relevant passages using hybrid search (keywords + AI embeddings) and generates answers with citations back to the original sources. Everything runs locally on your machine.

---

## 1. Install

**You need:**
- Python 3.11 or newer
- [Ollama](https://ollama.com) installed and running

```bash
# Pull the default LLM model
ollama pull qwen2.5:14b-instruct

# Clone the repo and set up a virtual environment
git clone https://github.com/your-org/docsai.git
cd docsai
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Mac / Linux

# Install dependencies
pip install -r requirements.txt
```

That's it for setup.

---

## 2. Create a Profile

A **profile** is a self-contained knowledge base. Each one has its own config, cached pages, and search index. Profiles live in the `profiles/` folder.

### Option A: Create via the API

Start the server first (using any existing profile, or the default):

```bash
python -m docsai.main serve stripe
```

Then create a profile with a POST request:

```bash
curl -X POST http://localhost:8080/profiles/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-docs",
    "sourceType": "web",
    "webDomains": ["https://docs.example.com"],
    "crawlDepth": 2,
    "description": "Example documentation"
  }'
```

### Option B: Create manually

Create the folder and config file yourself:

```
profiles/my-docs/
  config.yaml
```

Minimal `config.yaml` for a **website**:

```yaml
name: my-docs
description: My documentation knowledge base
source:
  type: web
  domain: https://docs.example.com
  allowed_paths: ["/"]
  depth: 2
  respect_robots: true
```

Minimal `config.yaml` for **local files**:

```yaml
name: my-docs
description: My local documents
source:
  type: local
  local_paths:
    - /path/to/your/docs
    - /another/folder
```

Everything else (chunk size, retrieval settings, model config) uses sensible defaults automatically.

---

## 3. Start the Server

```bash
python -m docsai.main serve my-docs
```

The server starts at `http://localhost:8080`. Keep this terminal open.

---

## 4. Ingest Documents

Open a **second terminal** and run:

```bash
python -m docsai.main ingest my-docs
```

This crawls the configured sources, parses documents, chunks them, and stores embeddings in the local vector database. Depending on the size of the docs, this can take a few minutes.

**Alternatively**, trigger ingestion via the API:

```bash
# Start ingestion
curl -X POST http://localhost:8080/ingestion/start/my-docs

# Check progress (use the task_id from the response above)
curl http://localhost:8080/ingestion/status/{task_id}
```

You can monitor progress in real-time:

```bash
python scripts/monitor_ingestion.py
```

---

## 5. Ask Questions

### Via the CLI

```bash
python -m docsai.main ask my-docs "How do I authenticate API requests?"
```

### Via the API

```bash
curl "http://localhost:8080/ask?q=How+do+I+authenticate+API+requests"
```

The response includes an answer with numbered citations like `[1]`, `[2]` that link back to the original source pages.

### Question Modes

DocsAI auto-detects the type of question and adjusts its answer style. You can also set the mode explicitly:

| Mode | Best for | Example questions |
|------|----------|-------------------|
| `comprehensive` | General questions, overviews | "What is the payments API?" |
| `integration` | Building something, step-by-step | "How do I set up webhooks?" |
| `debugging` | Fixing problems | "Why is my request returning 401?" |
| `learning` | Understanding concepts | "Explain how OAuth works" |

To set a mode explicitly:

```bash
curl "http://localhost:8080/ask?q=Why+is+my+request+failing&mode=debugging"
```

---

## 6. Manage Multiple Profiles

You can have many profiles and switch between them without restarting the server.

```bash
# List all profiles
curl http://localhost:8080/profiles/list

# Switch to a different profile
curl -X POST http://localhost:8080/profile/switch/another-profile

# Check stats for a profile
curl http://localhost:8080/profile/my-docs/stats
```

---

## 7. Use with Claude Desktop (MCP)

DocsAI can plug directly into Claude Desktop so you can query your knowledge base from within Claude.

1. Make sure the DocsAI server is running (`python -m docsai.main serve my-docs`)

2. Add this to your Claude Desktop config file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "docsai": {
      "command": "python",
      "args": ["C:/full/path/to/docsai/docsai_mcp_server.py"]
    }
  }
}
```

3. Restart Claude Desktop. You can now ask Claude to search your knowledge base directly.

---

## Common Tasks

### Re-ingest after docs change

Just run ingestion again. DocsAI tracks content hashes and only processes new or changed documents:

```bash
python -m docsai.main ingest my-docs
```

### Wipe and start fresh

If you want a clean slate for a profile's search index:

```bash
python scripts/clear_chroma.py my-docs
python -m docsai.main ingest my-docs
```

### Check answer quality

Run the diagnostic script to evaluate how well retrieval is working:

```bash
python scripts/diagnose_rag_quality.py
```

---

## Supported File Formats

When using local file sources, DocsAI can ingest:

| Format | Extensions |
|--------|-----------|
| Text | `.txt`, `.log`, `.rtf` |
| Markdown | `.md` |
| PDF | `.pdf` |
| Word | `.docx`, `.doc` |
| Email | `.eml`, `.msg` |
| EPUB | `.epub` |
| HTML | `.html`, `.htm` |
| JSON | `.json` |
| CSV | `.csv` |

---

## Config Reference

All settings are optional except `name` and `source`. Defaults are applied automatically.

```yaml
name: my-docs                              # Required
description: What this knowledge base is   # Optional

source:
  type: web                                # web, local, or mixed
  domain: https://docs.example.com         # For web sources
  allowed_paths: ["/"]                     # URL paths to crawl
  depth: 2                                 # How many links deep to follow
  respect_robots: true                     # Honor robots.txt
  local_paths: []                          # For local sources

ingest:
  chunk_tokens: 800                        # Size of each text chunk (default: 800)
  chunk_overlap: 120                       # Overlap between chunks (default: 120)
  min_text_len: 180                        # Skip chunks smaller than this

retrieval:
  k_bm25: 40                              # Keyword search candidates
  k_embed: 40                             # Semantic search candidates
  combine_top_k: 10                        # Final results sent to the LLM

model:
  llm:
    mode: ollama                           # ollama or llamacpp
    ollama_model: qwen2.5:14b-instruct     # Which Ollama model to use
    temperature: 0.2                       # Lower = more focused answers
  embedding:
    hf_name: BAAI/bge-base-en-v1.5         # Embedding model
```

---

## Troubleshooting

**"Connection refused" when asking questions**
The server isn't running. Start it with `python -m docsai.main serve <profile>`.

**"No results found" for queries**
Documents haven't been ingested yet. Run `python -m docsai.main ingest <profile>`.

**Ollama errors**
Make sure Ollama is running (`ollama serve`) and has the model pulled (`ollama pull qwen2.5:14b-instruct`).

**Ingestion seems stuck**
Check progress with `python scripts/monitor_ingestion.py` or `curl http://localhost:8080/ingestion/status/{task_id}`.

**Want to use a different LLM model?**
Change `model.llm.ollama_model` in your profile's `config.yaml` to any model you have in Ollama.
