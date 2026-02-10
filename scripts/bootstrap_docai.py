# bootstrap_docsai.py
"""
Creates the initial DocsAI backend scaffold.
Run this in an empty folder:  python bootstrap_docsai.py
"""

import os, textwrap, pathlib, sys

ROOT = pathlib.Path.cwd()

def w(path, text):
    if path.exists():
        # Safety check: don't overwrite if it looks like a real implementation
        try:
            current_content = path.read_text(encoding="utf-8")
            if len(current_content) > 1000 or "DOCS_ONLY_PROMPT" not in text and "app = FastAPI" in current_content:
                print(f"⚠️  Skipping {path} - existing file looks like a full implementation.")
                return
        except:
            pass
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    print(f"  Created {path}")

# --------------- safety check -----------------
if (ROOT / "docsai" / "main.py").exists():
    print("❌ Error: 'docsai/main.py' already exists in this directory.")
    print("This script is intended to scaffold a NEW project in an EMPTY directory.")
    print("Running it here would overwrite your implementation with stubs.")
    sys.exit(1)

# --------------- directories -----------------
dirs = [
    "docsai/retriever",
    "docsai/guards",
    "profiles/stripe/data/chroma",
    "profiles/petstore/data/chroma",
    "ui"
]
for d in dirs:
    (ROOT / d).mkdir(parents=True, exist_ok=True)

# --------------- requirements -----------------
w(ROOT / "requirements.txt", """
fastapi
uvicorn
chromadb
beautifulsoup4
lxml
markdownify
rank-bm25
typer
pyyaml
orjson
requests
sentence-transformers
""")

# --------------- docsai/main.py -----------------
w(ROOT / "docsai/main.py", """
import typer, uvicorn, importlib
from fastapi import FastAPI
from pathlib import Path
from .config_loader import load_config

app = FastAPI(title="DocsAI Local")

@app.get("/status")
def status():
    return {"ok": True, "message": "DocsAI backend running."}

cli = typer.Typer(help="DocsAI command line")

@cli.command()
def serve(profile: str):
    cfg = load_config(profile)
    print(f"Starting server for profile: {profile}")
    uvicorn.run("docsai.main:app", host="127.0.0.1", port=cfg.get('server', {}).get('port', 8080))

@cli.command()
def ingest(profile: str):
    print(f"[stub] ingesting docs for {profile} (implement in retriever/ingest.py)")

@cli.command()
def ask(profile: str, question: str):
    print(f"[stub] asking {profile}: {question} (implement in llm_runner.py)")

if __name__ == "__main__":
    cli()
""")

# --------------- docsai/config_loader.py -----------------
w(ROOT / "docsai/config_loader.py", """
import yaml
from pathlib import Path

def load_config(profile: str):
    cfg_path = Path("profiles") / profile / "config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"No config found for profile {profile}")
    return yaml.safe_load(cfg_path.read_text())
""")

# --------------- retriever/ingest.py -----------------
w(ROOT / "docsai/retriever/ingest.py", """
def ingest_profile(profile_config):
    # TODO: Crawl or parse docs domain; chunk + embed into Chroma
    print(f"Ingest stub for {profile_config['name']}")
""")

# --------------- retriever/search.py -----------------
w(ROOT / "docsai/retriever/search.py", """
def search_docs(query, k=8):
    # TODO: hybrid BM25 + embedding search
    print(f"Search stub for: {query}")
    return []
""")

# --------------- guards/prompts.py -----------------
w(ROOT / "docsai/guards/prompts.py", """
DOCS_ONLY_PROMPT = '''You are a documentation expert. 
Answer only using the provided passages; if unsure, say "Not found in docs." 
Include citation numbers in brackets like [1].'''
""")

# --------------- guards/validator.py -----------------
w(ROOT / "docsai/guards/validator.py", """
def validate_answer(answer, passages):
    # TODO: verify that each claim is supported
    return True
""")

# --------------- llm_runner.py -----------------
w(ROOT / "docsai/llm_runner.py", """
def run_llm(question, passages, model_path=""):
    # TODO: connect to llama.cpp subprocess or API call
    print(f"[stub] would query model at {model_path} with {len(passages)} passages.")
    return "Answer generation stub."
""")

# --------------- mcp_server.py -----------------
w(ROOT / "docsai/mcp_server.py", """
from fastapi import APIRouter

router = APIRouter()

@router.get("/crawl")
def crawl():
    return {"ok": True, "message": "stub crawl"}

@router.get("/search")
def search(q: str):
    return {"ok": True, "query": q, "results": []}

@router.get("/get")
def get(id: str):
    return {"ok": True, "id": id, "text": "stub text"}
""")

# --------------- profiles configs -----------------
stripe_yaml = """
name: stripe
source:
  type: web
  domain: https://docs.stripe.com
  allowed_paths: ["/api"]
ingest:
  chunk_tokens: 800
  chunk_overlap: 120
model:
  llm:
    mode: ollama
    ollama_model: qwen2.5:14b-instruct
server:
  port: 8080
"""
petstore_yaml = """
name: petstore
source:
  type: openapi
  files: ["./data/petstore.yaml"]
  resolve_refs: true
model:
  llm:
    mode: ollama
    ollama_model: qwen2.5:14b-instruct
server:
  port: 8081
"""
w(ROOT / "profiles/stripe/config.yaml", stripe_yaml)
w(ROOT / "profiles/petstore/config.yaml", petstore_yaml)

# --------------- README -----------------
w(ROOT / "README.md", """
# DocsAI Scaffold (POC)

1. Create venv & install deps  
   ```bash
   python -m venv .venv
   .\\.venv\\Scripts\\activate
   pip install -r requirements.txt
Run:

python -m docsai.main serve --profile stripe


Future: implement ingestion, retrieval, and LLM in their stubs.

Directory layout:

docsai/
  main.py
  retriever/
  guards/
profiles/
  stripe/
  petstore/


""")

print("\n✅ DocsAI scaffold created in", ROOT)
print("Next steps:")
print(" 1. python -m venv .venv && .\.venv\Scripts\activate")
print(" 2. pip install -r requirements.txt")
print(" 3. python -m docsai.main serve --profile stripe")
print("Everything else is ready for you to start coding!")