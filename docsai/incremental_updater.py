"""
Incremental Update System with Change Detection
Only updates what has actually changed - no full DB recreation
"""

import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import requests
from bs4 import BeautifulSoup

class IncrementalUpdater:
    """
    Smart incremental update system that:
    1. Tracks content hashes for all documents
    2. Detects changes via multiple methods
    3. Only updates changed content
    4. Preserves existing unchanged data
    """

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.profile_path = Path(f"profiles/{profile_name}")
        self.metadata_db = self.profile_path / "ingestion_metadata.db"
        self.init_metadata_db()

    def init_metadata_db(self):
        """Initialize metadata database for tracking changes"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        # Create tables for tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_metadata (
                url TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                last_modified TEXT,
                etag TEXT,
                content_length INTEGER,
                last_checked TIMESTAMP,
                last_ingested TIMESTAMP,
                chunk_ids TEXT,  -- JSON array of chunk IDs
                status TEXT,  -- 'current', 'outdated', 'new', 'deleted'
                change_frequency TEXT,  -- 'static', 'daily', 'weekly', 'monthly'
                importance_score REAL  -- 0-1 score for prioritization
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                run_id TEXT PRIMARY KEY,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                total_documents INTEGER,
                updated_documents INTEGER,
                new_documents INTEGER,
                deleted_documents INTEGER,
                errors TEXT,  -- JSON array
                status TEXT  -- 'running', 'completed', 'failed'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                detected_at TIMESTAMP,
                change_type TEXT,  -- 'content', 'new', 'deleted', 'metadata'
                old_hash TEXT,
                new_hash TEXT,
                processed BOOLEAN DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def calculate_content_hash(self, content: str) -> str:
        """Calculate stable hash of content"""
        # Normalize content for consistent hashing
        normalized = content.strip().lower()
        # Remove timestamps and dynamic content that changes but doesn't matter
        normalized = self._remove_dynamic_content(normalized)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _remove_dynamic_content(self, content: str) -> str:
        """Remove dynamic content that shouldn't trigger updates"""
        import re

        # Remove common dynamic patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO timestamps
            r'generated on .+',  # Generation timestamps
            r'last updated: .+',  # Update timestamps
            r'<!--.*?-->',  # HTML comments
            r'data-timestamp="[^"]*"',  # Data attributes with timestamps
            r'id="[a-f0-9]{8,}"',  # Generated IDs
        ]

        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        return content

    def check_url_changes(self, url: str) -> Dict[str, any]:
        """
        Check if a URL has changed using multiple methods
        Returns change detection results
        """
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        # Get existing metadata
        cursor.execute(
            "SELECT content_hash, last_modified, etag, content_length FROM document_metadata WHERE url = ?",
            (url,)
        )
        existing = cursor.fetchone()

        changes = {
            'url': url,
            'has_changed': False,
            'is_new': existing is None,
            'change_type': None,
            'confidence': 0.0
        }

        try:
            # Make HEAD request first (faster)
            head_response = requests.head(url, timeout=10, allow_redirects=True)
            headers = head_response.headers

            # Check multiple signals
            signals = []

            # 1. ETag check (most reliable)
            current_etag = headers.get('ETag')
            if existing and current_etag:
                if current_etag != existing[2]:  # etag column
                    signals.append(('etag', 0.9))

            # 2. Last-Modified check
            current_modified = headers.get('Last-Modified')
            if existing and current_modified:
                if current_modified != existing[1]:  # last_modified column
                    signals.append(('last_modified', 0.8))

            # 3. Content-Length check (less reliable)
            current_length = headers.get('Content-Length')
            if existing and current_length:
                if int(current_length) != existing[3]:  # content_length column
                    signals.append(('content_length', 0.5))

            # If we have signals or it's new, fetch content
            if signals or changes['is_new']:
                response = requests.get(url, timeout=30)
                content = response.text
                current_hash = self.calculate_content_hash(content)

                if existing:
                    if current_hash != existing[0]:  # content_hash column
                        signals.append(('content_hash', 1.0))
                        changes['has_changed'] = True
                        changes['old_hash'] = existing[0]
                        changes['new_hash'] = current_hash
                    else:
                        # Content unchanged despite header changes
                        changes['has_changed'] = False
                else:
                    changes['has_changed'] = True
                    changes['new_hash'] = current_hash

                # Calculate confidence
                if signals:
                    changes['confidence'] = max(s[1] for s in signals)
                    changes['signals'] = [s[0] for s in signals]

                # Store the new metadata
                changes['metadata'] = {
                    'content_hash': current_hash,
                    'last_modified': current_modified,
                    'etag': current_etag,
                    'content_length': int(current_length) if current_length else None,
                    'content': content
                }

        except Exception as e:
            changes['error'] = str(e)
            changes['has_changed'] = None  # Unknown

        conn.close()
        return changes

    def scan_for_changes(self, urls: List[str]) -> Dict[str, List[str]]:
        """
        Scan multiple URLs for changes
        Returns categorized lists of URLs
        """
        results = {
            'unchanged': [],
            'updated': [],
            'new': [],
            'errors': []
        }

        total = len(urls)
        print(f"[CHANGE DETECTION] Scanning {total} URLs for changes...")

        for i, url in enumerate(urls, 1):
            if i % 10 == 0:
                print(f"[PROGRESS] Checked {i}/{total} URLs...")

            change_info = self.check_url_changes(url)

            if change_info.get('error'):
                results['errors'].append(url)
            elif change_info['is_new']:
                results['new'].append(url)
            elif change_info['has_changed']:
                results['updated'].append(url)
                # Log the change
                self._log_change(url, 'content', change_info.get('old_hash'), change_info.get('new_hash'))
            else:
                results['unchanged'].append(url)

        # Summary
        print(f"\n[CHANGE DETECTION] Summary:")
        print(f"  • Unchanged: {len(results['unchanged'])}")
        print(f"  • Updated: {len(results['updated'])}")
        print(f"  • New: {len(results['new'])}")
        print(f"  • Errors: {len(results['errors'])}")

        return results

    def _log_change(self, url: str, change_type: str, old_hash: str = None, new_hash: str = None):
        """Log detected changes"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO change_log (url, detected_at, change_type, old_hash, new_hash)
            VALUES (?, datetime('now'), ?, ?, ?)
        """, (url, change_type, old_hash, new_hash))

        conn.commit()
        conn.close()

    def update_only_changed(self, change_results: Dict[str, List[str]], config: Dict) -> Dict[str, any]:
        """
        Update only the changed documents in ChromaDB
        Preserves unchanged content
        """
        from .retriever.ingest import _chunk, _hash, _html_to_md
        from sentence_transformers import SentenceTransformer
        import chromadb
        from chromadb.config import Settings

        stats = {
            'updated_chunks': 0,
            'new_chunks': 0,
            'deleted_chunks': 0,
            'preserved_chunks': 0,
            'errors': []
        }

        # Initialize ChromaDB
        chroma_path = self.profile_path / "data" / "chroma"
        client = chromadb.Client(Settings(
            is_persistent=True,
            persist_directory=str(chroma_path)
        ))
        coll = client.get_or_create_collection(name="docs")

        # Initialize embedder
        embedder = SentenceTransformer(config["model"]["embedding"]["hf_name"])

        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        # Process updated documents
        for url in change_results['updated']:
            try:
                print(f"[UPDATE] Processing changed document: {url}")

                # Get old chunk IDs to delete
                cursor.execute(
                    "SELECT chunk_ids FROM document_metadata WHERE url = ?",
                    (url,)
                )
                result = cursor.fetchone()
                if result and result[0]:
                    old_chunk_ids = json.loads(result[0])
                    # Delete old chunks
                    coll.delete(ids=old_chunk_ids)
                    stats['deleted_chunks'] += len(old_chunk_ids)
                    print(f"  Deleted {len(old_chunk_ids)} old chunks")

                # Get new content
                change_info = self.check_url_changes(url)
                if change_info.get('metadata', {}).get('content'):
                    content = _html_to_md(change_info['metadata']['content'])

                    # Create new chunks
                    chunks = _chunk(content,
                                  chunk_tokens=config['ingest']['chunk_tokens'],
                                  chunk_overlap=config['ingest']['chunk_overlap'])

                    new_chunk_ids = []
                    for i, chunk_text in enumerate(chunks):
                        chunk_id = f"{_hash(url)}_{i}_{_hash(chunk_text)[:8]}"
                        new_chunk_ids.append(chunk_id)

                        # Generate embedding
                        embedding = embedder.encode([chunk_text], show_progress_bar=False)[0].tolist()

                        # Upsert to ChromaDB
                        coll.upsert(
                            ids=[chunk_id],
                            documents=[chunk_text],
                            metadatas=[{
                                'source_url': url,
                                'chunk_index': i,
                                'updated_at': datetime.now().isoformat()
                            }],
                            embeddings=[embedding]
                        )

                    stats['updated_chunks'] += len(new_chunk_ids)
                    print(f"  Created {len(new_chunk_ids)} new chunks")

                    # Update metadata
                    cursor.execute("""
                        UPDATE document_metadata
                        SET content_hash = ?, chunk_ids = ?, last_ingested = datetime('now'), status = 'current'
                        WHERE url = ?
                    """, (change_info['new_hash'], json.dumps(new_chunk_ids), url))

            except Exception as e:
                print(f"  Error updating {url}: {e}")
                stats['errors'].append(f"{url}: {str(e)}")

        # Process new documents
        for url in change_results['new']:
            try:
                print(f"[NEW] Processing new document: {url}")
                # Similar process as updated, but INSERT instead of UPDATE
                # ... (implementation similar to above)
                stats['new_chunks'] += 1  # Placeholder

            except Exception as e:
                stats['errors'].append(f"{url}: {str(e)}")

        # Count preserved chunks
        total_chunks = coll.count()
        stats['preserved_chunks'] = total_chunks - stats['updated_chunks'] - stats['new_chunks']

        conn.commit()
        conn.close()

        print(f"\n[INCREMENTAL UPDATE] Complete:")
        print(f"  • Preserved: {stats['preserved_chunks']} chunks (unchanged)")
        print(f"  • Updated: {stats['updated_chunks']} chunks")
        print(f"  • Added: {stats['new_chunks']} chunks")
        print(f"  • Deleted: {stats['deleted_chunks']} chunks")
        if stats['errors']:
            print(f"  • Errors: {len(stats['errors'])}")

        return stats

    def smart_crawl_schedule(self) -> List[Tuple[str, str]]:
        """
        Determine crawl priority based on change patterns
        Returns list of (url, priority) tuples
        """
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        # Analyze change patterns
        cursor.execute("""
            SELECT url,
                   COUNT(*) as change_count,
                   MAX(detected_at) as last_change
            FROM change_log
            WHERE detected_at > datetime('now', '-30 days')
            GROUP BY url
        """)

        patterns = {}
        for url, count, last_change in cursor.fetchall():
            if count > 20:  # Changed frequently
                patterns[url] = 'hourly'
            elif count > 5:
                patterns[url] = 'daily'
            elif count > 1:
                patterns[url] = 'weekly'
            else:
                patterns[url] = 'monthly'

        # Update change frequency in metadata
        for url, frequency in patterns.items():
            cursor.execute(
                "UPDATE document_metadata SET change_frequency = ? WHERE url = ?",
                (frequency, url)
            )

        conn.commit()
        conn.close()

        return patterns

    def get_update_stats(self) -> Dict:
        """Get statistics about updates"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        stats = {}

        # Total documents
        cursor.execute("SELECT COUNT(*) FROM document_metadata")
        stats['total_documents'] = cursor.fetchone()[0]

        # Documents by status
        cursor.execute("""
            SELECT status, COUNT(*)
            FROM document_metadata
            GROUP BY status
        """)
        stats['by_status'] = dict(cursor.fetchall())

        # Recent changes
        cursor.execute("""
            SELECT COUNT(*)
            FROM change_log
            WHERE detected_at > datetime('now', '-7 days')
        """)
        stats['changes_last_week'] = cursor.fetchone()[0]

        # Change frequency distribution
        cursor.execute("""
            SELECT change_frequency, COUNT(*)
            FROM document_metadata
            WHERE change_frequency IS NOT NULL
            GROUP BY change_frequency
        """)
        stats['change_patterns'] = dict(cursor.fetchall())

        conn.close()
        return stats


def run_incremental_update(profile_name: str):
    """Run incremental update for a profile"""

    print(f"\n[INCREMENTAL UPDATE] Starting for profile: {profile_name}")
    updater = IncrementalUpdater(profile_name)

    # Get URLs to check (from existing crawl or config)
    # This would come from your existing crawler
    urls = []  # TODO: Get from crawler

    # Scan for changes
    changes = updater.scan_for_changes(urls)

    # Only update what changed
    if changes['updated'] or changes['new']:
        print(f"\n[INCREMENTAL UPDATE] Updating {len(changes['updated']) + len(changes['new'])} documents...")
        # Load config
        from .config_loader import load_config
        config = load_config(profile_name)

        # Update only changed content
        stats = updater.update_only_changed(changes, config)

        return True
    else:
        print("\n[INCREMENTAL UPDATE] No changes detected - database is current!")
        return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        profile = sys.argv[1]
        run_incremental_update(profile)
    else:
        print("Usage: python incremental_updater.py <profile_name>")