"""
Ingestion Manager - Handles background ingestion with progress tracking
"""

import asyncio
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import uuid

class IngestionStatus(Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    SCANNING = "scanning"
    PROCESSING = "processing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class IngestionTask:
    def __init__(self, task_id: str, profile_name: str):
        self.id = task_id
        self.profile_name = profile_name
        self.status = IngestionStatus.IDLE
        self.progress = 0.0
        self.current_file = ""
        self.total_files = 0
        self.processed_files = 0
        self.total_chunks = 0
        self.indexed_chunks = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.start_time = None
        self.end_time = None
        self.stats = {}
        self.cancel_requested = False

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'profile_name': self.profile_name,
            'status': self.status.value,
            'progress': self.progress,
            'current_file': self.current_file,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'total_chunks': self.total_chunks,
            'indexed_chunks': self.indexed_chunks,
            'errors': self.errors,
            'warnings': self.warnings,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None,
            'stats': self.stats
        }

class IngestionManager:
    """Manages background ingestion tasks with progress tracking."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.tasks: Dict[str, IngestionTask] = {}
        self.active_task: Optional[IngestionTask] = None
        self.task_thread: Optional[threading.Thread] = None

    def start_ingestion(self, profile_name: str, config: Dict) -> str:
        """Start a new ingestion task."""
        # Check if already running for this profile
        if self.active_task and self.active_task.profile_name == profile_name:
            if self.active_task.status not in [IngestionStatus.COMPLETED, IngestionStatus.FAILED, IngestionStatus.CANCELLED]:
                return self.active_task.id  # Return existing task

        # Create new task
        task_id = str(uuid.uuid4())
        task = IngestionTask(task_id, profile_name)
        task.status = IngestionStatus.PREPARING
        task.start_time = datetime.now()

        self.tasks[task_id] = task
        self.active_task = task

        # Start ingestion in background thread
        self.task_thread = threading.Thread(
            target=self._run_ingestion,
            args=(task, config),
            daemon=True
        )
        self.task_thread.start()

        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a specific task."""
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None

    def get_active_task(self) -> Optional[Dict]:
        """Get the currently active task if any."""
        return self.active_task.to_dict() if self.active_task else None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self.tasks.get(task_id)
        if task and task.status in [IngestionStatus.SCANNING, IngestionStatus.PROCESSING, IngestionStatus.INDEXING]:
            task.cancel_requested = True
            return True
        return False

    def _run_ingestion(self, task: IngestionTask, config: Dict):
        """Run the actual ingestion process."""
        try:
            from .config_loader import profile_paths
            from .retriever.ingest import _chunk, _hash
            from .file_parsers import FileParser, scan_directory
            from .document_intelligence import DocumentIntelligence, SmartChunker
            from sentence_transformers import SentenceTransformer
            import chromadb
            from chromadb.config import Settings

            # Get paths
            paths = profile_paths(task.profile_name)

            # Initialize components
            task.status = IngestionStatus.PREPARING
            parser = FileParser()
            doc_intel = DocumentIntelligence()
            smart_chunker = SmartChunker()

            # Initialize embedder first
            embedder = SentenceTransformer(config["model"]["embedding"]["hf_name"])

            # Initialize ChromaDB
            client = chromadb.Client(Settings(
                is_persistent=True,
                persist_directory=str(paths["chroma"])
            ))

            # Get or create collection
            coll = client.get_or_create_collection(name="docs")

            # Check embedding dimension if collection has existing items
            try:
                if coll.count() > 0:
                    sample = coll.peek(1)
                    if sample['embeddings']:
                        existing_dim = len(sample['embeddings'][0])
                        test_embedding = embedder.encode(["test"], show_progress_bar=False)
                        new_dim = test_embedding.shape[1]

                        if existing_dim != new_dim:
                            task.warnings.append(f"Embedding dimension mismatch: Collection has {existing_dim}D, model produces {new_dim}D")
                            task.warnings.append("Clearing existing collection due to dimension mismatch...")
                            client.delete_collection(name="docs")
                            coll = client.get_or_create_collection(name="docs")
                            task.warnings.append("Created new collection with correct dimensions")
            except Exception:
                pass  # Dimension check failed, continue with existing collection

            # Collect all documents to process
            task.status = IngestionStatus.SCANNING
            all_files = []
            source_type = config["source"]["type"]

            # Handle web sources
            if source_type in ["web", "mixed"]:
                from .retriever.ingest import crawl_website

                domain = config["source"]["domain"].rstrip("/")
                allowed = config["source"].get("allowed_paths", [])
                depth = int(config["source"].get("depth", 2))

                task.current_file = f"Crawling {domain}..."

                def _crawl_progress(url, count):
                    task.current_file = f"Crawling... {url.split('/')[-1] or url}"
                    task.processed_files = count

                # Start crawling
                if allowed:
                    raw = {}
                    for path in allowed:
                        start_url = domain + path
                        crawl_results = crawl_website(start_url, allowed, depth, paths["cache"], on_page=_crawl_progress)
                        raw.update(crawl_results)
                else:
                    raw = crawl_website(domain, allowed, depth, paths["cache"], on_page=_crawl_progress)

                # Add web pages to file list
                for url, html in raw.items():
                    all_files.append({
                        'type': 'web',
                        'path': url,
                        'content': html
                    })

            # Handle local sources
            if source_type in ["local", "mixed"]:
                local_paths = config["source"].get("local_paths", [])
                file_types = config["source"].get("file_types", ['all'])

                for local_path in local_paths:
                    task.current_file = f"Scanning {local_path}..."
                    path = Path(local_path)

                    if not path.exists():
                        task.warnings.append(f"Path does not exist: {local_path}")
                        continue

                    if path.is_file():
                        files = [str(path)]
                    else:
                        files = scan_directory(str(path), file_types, recursive=True)

                    # Add local files to file list
                    for filepath in files:
                        all_files.append({
                            'type': 'local',
                            'path': filepath,
                            'content': None  # Will be parsed later
                        })

            task.total_files = len(all_files)

            # Check if cancelled
            if task.cancel_requested:
                task.status = IngestionStatus.CANCELLED
                return

            # Process all files
            task.status = IngestionStatus.PROCESSING
            all_chunks = []
            file_metadata = []

            for i, file_info in enumerate(all_files):
                if task.cancel_requested:
                    task.status = IngestionStatus.CANCELLED
                    return

                task.current_file = file_info['path']
                task.processed_files = i + 1
                task.progress = (i / len(all_files)) * 0.7  # 70% for processing

                try:
                    # Get content
                    if file_info['type'] == 'web':
                        from .retriever.ingest import _html_to_md
                        content = _html_to_md(file_info['content'])
                        filename = file_info['path']
                    else:
                        result = parser.parse_file(file_info['path'])
                        if not result or not result.get('content'):
                            task.warnings.append(f"Failed to parse: {file_info['path']}")
                            continue
                        content = result['content']
                        filename = Path(file_info['path']).name

                    if not content or len(content) < 100:
                        continue

                    # Categorize document
                    doc_category = doc_intel.categorize_document(filename, content)

                    # Extract metadata
                    metadata = doc_intel.extract_metadata(
                        content,
                        doc_category['metadata_extractors']
                    )
                    metadata['category'] = doc_category['category']
                    metadata['source_type'] = file_info['type']

                    # Smart chunking based on document type
                    chunk_strategy = doc_category['chunk_strategy']
                    chunk_size = doc_category['chunk_size']

                    chunks = smart_chunker.chunk(
                        content,
                        chunk_strategy,
                        chunk_size,
                        overlap=120
                    )

                    # Create chunk records
                    for chunk_data in chunks:
                        chunk_id = f"{_hash(filename)}_{len(all_chunks)}_{_hash(chunk_data['text'])[:8]}"

                        # Clean metadata - ChromaDB only accepts primitive types
                        clean_metadata = {}
                        for k, v in metadata.items():
                            if v is None:
                                continue
                            elif isinstance(v, (str, int, float, bool)):
                                clean_metadata[k] = v
                            elif isinstance(v, list):
                                # Convert lists to comma-separated strings
                                if all(isinstance(item, str) for item in v):
                                    clean_metadata[k] = ', '.join(v)
                                else:
                                    clean_metadata[k] = json.dumps(v)
                            elif isinstance(v, dict):
                                # Convert dicts to JSON strings
                                clean_metadata[k] = json.dumps(v)
                            else:
                                # Convert other types to string
                                clean_metadata[k] = str(v)

                        chunk_metadata = {
                            **clean_metadata,
                            'source': filename,
                            'chunk_type': chunk_data.get('type', 'unknown'),
                            'chunk_index': len(all_chunks)
                        }

                        # Add chunk-specific metadata with proper type handling
                        for key in ['speakers', 'endpoint', 'chapter', 'record_count']:
                            if key in chunk_data:
                                val = chunk_data[key]
                                if isinstance(val, (str, int, float, bool)):
                                    chunk_metadata[key] = val
                                elif isinstance(val, list):
                                    chunk_metadata[key] = ', '.join(str(v) for v in val)
                                elif val is not None:
                                    chunk_metadata[key] = str(val)

                        # Add source_url for web sources
                        if file_info['type'] == 'web':
                            chunk_metadata['source_url'] = file_info['path']

                        all_chunks.append({
                            'id': chunk_id,
                            'text': chunk_data['text'],
                            'metadata': chunk_metadata
                        })

                    # Store file metadata for relationship detection
                    file_metadata.append({
                        'id': _hash(filename),
                        'filename': filename,
                        'metadata': metadata,
                        'chunk_count': len(chunks)
                    })

                except Exception as e:
                    task.errors.append(f"Error processing {file_info['path']}: {str(e)}")

            task.total_chunks = len(all_chunks)

            # Check if cancelled
            if task.cancel_requested:
                task.status = IngestionStatus.CANCELLED
                return

            # Index chunks into ChromaDB
            task.status = IngestionStatus.INDEXING

            if all_chunks:
                # Batch process for efficiency
                batch_size = 100
                for i in range(0, len(all_chunks), batch_size):
                    if task.cancel_requested:
                        task.status = IngestionStatus.CANCELLED
                        return

                    batch = all_chunks[i:i + batch_size]

                    ids = [c['id'] for c in batch]
                    texts = [c['text'] for c in batch]
                    metadatas = [c['metadata'] for c in batch]

                    # Generate embeddings
                    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

                    # Upsert to ChromaDB
                    coll.upsert(
                        ids=ids,
                        documents=texts,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )

                    task.indexed_chunks = min(i + batch_size, len(all_chunks))
                    task.progress = 0.7 + (task.indexed_chunks / len(all_chunks)) * 0.25

            # Detect relationships (optional, for future use)
            # relationships = DocumentRelationshipDetector().detect_relationships(file_metadata)

            # Complete
            task.status = IngestionStatus.COMPLETED
            task.progress = 1.0
            task.end_time = datetime.now()

            # Calculate stats
            task.stats = {
                'total_files': task.total_files,
                'processed_files': task.processed_files,
                'total_chunks': task.total_chunks,
                'indexed_chunks': task.indexed_chunks,
                'errors_count': len(task.errors),
                'warnings_count': len(task.warnings),
                'duration_seconds': (task.end_time - task.start_time).total_seconds() if task.end_time and task.start_time else 0,
                'categories': {}
            }

            # Count categories
            for chunk in all_chunks:
                cat = chunk['metadata'].get('category', 'unknown')
                task.stats['categories'][cat] = task.stats['categories'].get(cat, 0) + 1

        except Exception as e:
            task.status = IngestionStatus.FAILED
            task.errors.append(f"Fatal error: {str(e)}")
            task.end_time = datetime.now()
            import traceback
            print(f"[INGESTION ERROR] {traceback.format_exc()}")

# Global singleton instance
ingestion_manager = IngestionManager()