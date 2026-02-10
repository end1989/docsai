# 🗺️ DocsAI Roadmap

This document outlines the vision, current status, and future plans for DocsAI (Singular Source of Truth).

---

## 🌟 The Vision

DocsAI aims to be the **memory layer for the AI age**. A local-first knowledge engine that transforms raw documentation into actionable intelligence, keeping your data private and your answers grounded in truth.

1.  **Any Source, One Truth**: Connect multiple heterogeneous sources (Web, local files, APIs, Emails) into a unified knowledge mesh.
2.  **Privacy First**: All processing, from ingestion to inference, happens on your local machine.
3.  **Precision Engineering**: Moving beyond simple RAG to intelligent, context-aware retrieval with high-fidelity citations.

---

## 🚀 Current Status: Proof of Concept (v0.1.0)

✅ **Core Infrastructure**
- FastAPI backend with CORS support.
- Persistent ChromaDB vector store.
- Profile isolation (config, data, cache per profile).
- Local LLM integration via Ollama and llama.cpp.

✅ **Ingestion Pipeline**
- Multi-format support (PDF, MD, DOCX, HTML, EML, EPUB, etc.).
- Smart chunking based on document category.
- Incremental updates with content hashing.
- Background ingestion with real-time progress tracking.

✅ **Advanced Retrieval & Generation**
- Hybrid search (BM25 keyword matching + Dense vector embeddings).
- Multi-mode expert personas (Comprehensive, Integration, Debugging, Learning).
- Automatic intent detection for optimized prompting.
- Citation-backed answers with link mapping.

---

## 🧩 Immediate Next Steps (Phase 1.1)

### 1. UI & UX Refinement
- [ ] **Typewriter Effect**: Implement response streaming for a better chat experience.
- [ ] **Clickable Citations**: Map bracketed citations ([1], [2]) directly to source links in the UI.
- [ ] **Toast Notifications**: Real-time alerts for ingestion status, server errors, and completion.
- [ ] **Profile Management UI**: A dashboard to create, switch, edit, and delete profiles easily.

### 2. Backend & Ingestion
- [ ] **Internal Logging**: Implement robust logging to `logs/server.log` and `logs/ingest.log`.
- [ ] **Parallel Fetching**: Speed up web crawling with controlled parallel requests.
- [ ] **Drag-and-Drop Ingestion**: Allow users to drop files directly into the UI for instant indexing.
- [ ] **Watch Folders**: Automatically re-index local directories when files change.

### 3. Quality & Reliability
- [ ] **Health Dashboard**: View system status, vRAM usage, and model performance (tokens/sec).
- [ ] **Fallback Mechanisms**: Graceful degradation if the LLM or vector store is unavailable.
- [ ] **Validation Suite**: Automated RAG quality checks using the `diagnose_rag_quality.py` script.

---

## ⚙️ Medium-Term Goals (Phase 2)

### 4. Intelligent Querying 2.0
- [ ] **Semantic Memory**: Cache recent answers to frequent questions within a profile.
- [ ] **Query Expansion**: Use the LLM to expand queries for better recall in complex scenarios.
- [ ] **Reranking Pipeline**: Implement a secondary reranker (e.g., Cohere or local cross-encoder) for top results.

### 5. Advanced Visualization
- [ ] **Knowledge Graph**: Interactive D3.js visualization of document relationships and clusters.
- [ ] **Coverage Map**: A visual tree of crawled endpoints/paths to identify knowledge gaps.
- [ ] **Citation Analytics**: Track which documents are most frequently cited to measure source utility.

### 6. Integration & Ecosystem
- [ ] **Expanded MCP Support**: Expose more internal tools (crawling, stats) to MCP clients.
- [ ] **API Key Management**: Secure access for external local applications.
- [ ] **Export Options**: Export knowledge bases or chat histories to PDF, Markdown, or JSON.

---

## 🌐 Long-Term Vision (Phase 3)

### 7. Agentic Intelligence
- [ ] **Trace Reasoning**: Show the "thinking path" the AI took through the documentation to reach an answer.
- [ ] **Proactive Insights**: The system identifies contradictions or outdated info across your sources.
- [ ] **Self-Updating Scrapers**: Intelligent agents that monitor sources and auto-update the index.

### 8. The Knowledge Mesh
- [ ] **Cross-Profile Reasoning**: Ask questions that require connecting dots between different profiles (e.g., "Contrast Stripe and PayPal integrations").
- [ ] **Collaborative Knowledge**: Shared, version-controlled knowledge bases for teams.
- [ ] **Natural Language Control**: Manage the entire system (crawling, configuration) through chat.

---

## 🛠️ Environment Benchmarks

- **Target OS**: Windows 11 (developed on)
- **Primary GPU**: NVIDIA RTX 40-series (RTX 4070 Ti Super recommended)
- **Local LLM**: Qwen 2.5 14B / Mistral Nemo 12B
- **Context Window**: 128k - 256k tokens
