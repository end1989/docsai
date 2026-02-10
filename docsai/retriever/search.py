from typing import List, Tuple, Dict
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import numpy as np

def _bm25_rank(query: str, corpus: List[str], top_k: int) -> List[int]:
    tokenized_corpus = [c.split() for c in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query.split())
    return list(np.argsort(scores)[::-1][:top_k])

def _top_k_embed(query: str, corpus: List[str], top_k: int, embedder) -> List[int]:
    qv = embedder.encode([query], normalize_embeddings=True)[0]
    D = embedder.encode(corpus, normalize_embeddings=True)
    sims = (D @ qv)
    return list(np.argsort(sims)[::-1][:top_k])

def search(cfg: Dict, paths: Dict, question: str) -> List[Tuple[str, str, Dict]]:
    client = chromadb.Client(Settings(is_persistent=True, persist_directory=str(paths["chroma"])))
    coll = client.get_or_create_collection("docs")

    # Get all documents (we need to use get() instead of peek() to get metadata)
    # First check how many documents we have
    count = coll.count()
    if count == 0:
        return []

    # Get documents with metadata
    # ChromaDB's get() without IDs returns all documents
    res = coll.get(limit=min(200, count))
    docs = res.get("documents") or []
    ids = res.get("ids") or []
    metadatas = res.get("metadatas") or []

    if not docs:
        return []

    k_bm25 = cfg["retrieval"]["k_bm25"]
    k_embed = cfg["retrieval"]["k_embed"]
    combine_top_k = cfg["retrieval"]["combine_top_k"]

    embedder = SentenceTransformer(cfg["model"]["embedding"]["hf_name"])
    bm_idx = _bm25_rank(question, docs, min(k_bm25, len(docs)))
    em_idx = _top_k_embed(question, docs, min(k_embed, len(docs)), embedder)

    merged = list(dict.fromkeys(bm_idx + em_idx))[:combine_top_k]
    out = [(ids[i], docs[i], metadatas[i] if i < len(metadatas) else {}) for i in merged]
    return out
