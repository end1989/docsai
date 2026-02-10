"""
Document Intelligence System
Intelligently categorizes, organizes, and prepares documents for optimal AI understanding.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import hashlib
import json

class DocumentIntelligence:
    """
    Analyzes documents to determine:
    - Document type and category
    - Optimal chunking strategy
    - Metadata extraction
    - Relationship detection
    """

    def __init__(self):
        # Document categorization patterns
        self.categories = {
            'technical': {
                'patterns': ['manual', 'guide', 'documentation', 'readme', 'install', 'setup', 'config'],
                'extensions': ['.md', '.txt', '.pdf'],
                'chunk_strategy': 'section_aware',
                'chunk_size': 1000
            },
            'conversation': {
                'patterns': ['transcript', 'chat', 'conversation', 'meeting', 'call', 'interview'],
                'extensions': ['.txt', '.json', '.csv'],
                'chunk_strategy': 'conversation_aware',
                'chunk_size': 800
            },
            'correspondence': {
                'patterns': ['email', 'memo', 'letter', 'message'],
                'extensions': ['.eml', '.msg', '.txt'],
                'chunk_strategy': 'message_boundary',
                'chunk_size': 600
            },
            'reference': {
                'patterns': ['api', 'reference', 'specification', 'schema'],
                'extensions': ['.json', '.yaml', '.md'],
                'chunk_strategy': 'endpoint_aware',
                'chunk_size': 500
            },
            'literature': {
                'patterns': ['book', 'chapter', 'article', 'paper', 'journal'],
                'extensions': ['.epub', '.pdf', '.txt'],
                'chunk_strategy': 'chapter_aware',
                'chunk_size': 1200
            },
            'data': {
                'patterns': ['report', 'analysis', 'statistics', 'metrics', 'log'],
                'extensions': ['.csv', '.json', '.log', '.txt'],
                'chunk_strategy': 'record_aware',
                'chunk_size': 400
            },
            'media': {
                'patterns': ['subtitle', 'caption', 'lyrics', 'script'],
                'extensions': ['.srt', '.vtt', '.txt'],
                'chunk_strategy': 'time_aware',
                'chunk_size': 300
            }
        }

    def categorize_document(self, filepath: str, content: str) -> Dict[str, Any]:
        """
        Intelligently categorize a document based on multiple signals.
        """
        filepath = Path(filepath)
        filename_lower = filepath.name.lower()

        # Score each category
        scores = {}
        for category, config in self.categories.items():
            score = 0

            # Check filename patterns
            for pattern in config['patterns']:
                if pattern in filename_lower:
                    score += 10

            # Check extension
            if filepath.suffix.lower() in config['extensions']:
                score += 5

            # Check content patterns (first 1000 chars)
            content_sample = content[:1000].lower()
            for pattern in config['patterns']:
                if pattern in content_sample:
                    score += 3

            scores[category] = score

        # Get the best category
        best_category = max(scores.items(), key=lambda x: x[1])

        # Default to 'general' if no strong match
        if best_category[1] < 5:
            return {
                'category': 'general',
                'confidence': 0.3,
                'chunk_strategy': 'sliding_window',
                'chunk_size': 800,
                'metadata_extractors': ['basic']
            }

        category_name = best_category[0]
        config = self.categories[category_name]

        return {
            'category': category_name,
            'confidence': min(best_category[1] / 20, 1.0),
            'chunk_strategy': config['chunk_strategy'],
            'chunk_size': config['chunk_size'],
            'metadata_extractors': self._get_extractors(category_name)
        }

    def _get_extractors(self, category: str) -> List[str]:
        """Get relevant metadata extractors for a category."""
        extractors = {
            'technical': ['version', 'product', 'sections'],
            'conversation': ['participants', 'datetime', 'topics'],
            'correspondence': ['sender', 'recipient', 'date', 'subject'],
            'reference': ['endpoints', 'methods', 'parameters'],
            'literature': ['author', 'title', 'chapters'],
            'data': ['date_range', 'metrics', 'summary'],
            'media': ['duration', 'speakers', 'timestamps']
        }
        return extractors.get(category, ['basic'])

    def extract_metadata(self, content: str, extractors: List[str]) -> Dict[str, Any]:
        """Extract relevant metadata based on document type."""
        metadata = {}

        for extractor in extractors:
            if extractor == 'basic':
                metadata.update(self._extract_basic(content))
            elif extractor == 'version':
                metadata.update(self._extract_version(content))
            elif extractor == 'datetime':
                metadata.update(self._extract_datetime(content))
            elif extractor == 'participants':
                metadata.update(self._extract_participants(content))
            elif extractor == 'sender':
                metadata.update(self._extract_email_headers(content))
            elif extractor == 'sections':
                metadata.update(self._extract_sections(content))
            elif extractor == 'topics':
                metadata.update(self._extract_topics(content))

        return metadata

    def _extract_basic(self, content: str) -> Dict:
        """Extract basic metadata."""
        lines = content.split('\n')
        return {
            'line_count': len(lines),
            'word_count': len(content.split()),
            'has_code': bool(re.search(r'```|def |class |function |import ', content)),
            'has_urls': bool(re.search(r'https?://\S+', content))
        }

    def _extract_version(self, content: str) -> Dict:
        """Extract version information."""
        version_patterns = [
            r'[Vv]ersion\s*[:=]?\s*([\d.]+)',
            r'v([\d.]+)',
            r'release\s*[:=]?\s*([\d.]+)'
        ]

        for pattern in version_patterns:
            match = re.search(pattern, content[:2000])
            if match:
                return {'version': match.group(1)}
        return {}

    def _extract_datetime(self, content: str) -> Dict:
        """Extract date/time information."""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
        ]

        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content[:5000])
            dates_found.extend(matches[:3])  # Limit to first 3

        # Convert list to comma-separated string for ChromaDB compatibility
        return {'dates_mentioned': ', '.join(dates_found[:3])} if dates_found else {}

    def _extract_participants(self, content: str) -> Dict:
        """Extract conversation participants."""
        # Look for patterns like "John:", "Speaker 1:", etc.
        participant_pattern = r'^([A-Z][A-Za-z\s]+):\s'
        matches = re.findall(participant_pattern, content[:5000], re.MULTILINE)
        unique_participants = list(set(matches))[:10]  # Limit to 10

        # Convert list to comma-separated string for ChromaDB compatibility
        return {'participants': ', '.join(unique_participants)} if unique_participants else {}

    def _extract_email_headers(self, content: str) -> Dict:
        """Extract email headers."""
        headers = {}
        patterns = {
            'sender': r'From:\s*(.+)',
            'recipient': r'To:\s*(.+)',
            'subject': r'Subject:\s*(.+)',
            'date': r'Date:\s*(.+)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content[:2000])
            if match:
                headers[key] = match.group(1).strip()

        return headers

    def _extract_sections(self, content: str) -> Dict:
        """Extract document sections/chapters."""
        # Look for markdown headers or numbered sections
        section_patterns = [
            r'^#{1,3}\s+(.+)$',  # Markdown headers
            r'^(\d+\.?\s+[A-Z].+)$',  # Numbered sections
            r'^(Chapter\s+\d+.*)$'  # Chapter headings
        ]

        sections = []
        for pattern in section_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            sections.extend(matches[:20])  # Limit to 20

        # Convert list to comma-separated string for ChromaDB compatibility
        return {'sections': ' | '.join(sections[:20])} if sections else {}

    def _extract_topics(self, content: str) -> Dict:
        """Extract key topics using simple keyword frequency."""
        # This is a simplified topic extraction
        # In production, you'd use NLP libraries like spaCy or NLTK

        # Remove common words
        stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'to', 'for', 'of', 'in', 'with', 'as', 'by', 'that', 'this', 'it', 'from', 'or', 'but'}

        words = re.findall(r'\b[a-z]+\b', content.lower())
        word_freq = {}

        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top 10 most frequent words
        topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Convert list to comma-separated string for ChromaDB compatibility
        return {'key_terms': ', '.join([word for word, freq in topics])} if topics else {}


class SmartChunker:
    """
    Implements intelligent chunking strategies based on document type.
    """

    def __init__(self):
        self.strategies = {
            'sliding_window': self.chunk_sliding_window,
            'section_aware': self.chunk_by_sections,
            'conversation_aware': self.chunk_by_conversation,
            'message_boundary': self.chunk_by_messages,
            'endpoint_aware': self.chunk_by_endpoints,
            'chapter_aware': self.chunk_by_chapters,
            'record_aware': self.chunk_by_records,
            'time_aware': self.chunk_by_timestamps
        }

    def chunk(self, content: str, strategy: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
        """
        Apply the appropriate chunking strategy.

        Returns list of chunks with metadata about chunk type and boundaries.
        """
        chunk_func = self.strategies.get(strategy, self.chunk_sliding_window)
        return chunk_func(content, chunk_size, overlap)

    def chunk_sliding_window(self, content: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Traditional sliding window chunking."""
        words = content.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)

            chunks.append({
                'text': chunk_text,
                'type': 'sliding_window',
                'start_idx': i,
                'end_idx': min(i + chunk_size, len(words))
            })

        return chunks

    def chunk_by_sections(self, content: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Chunk respecting section boundaries."""
        # Detect sections
        section_pattern = r'(^#{1,6}\s+.+$|^=+$|^-+$|\n\n\n+)'
        sections = re.split(section_pattern, content, flags=re.MULTILINE)

        chunks = []
        current_chunk = []
        current_size = 0

        for section in sections:
            section_words = section.split()
            section_size = len(section_words)

            if current_size + section_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'text': ' '.join(current_chunk),
                    'type': 'section',
                    'boundary': 'section_end'
                })

                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:]
                else:
                    current_chunk = []
                current_size = len(current_chunk)

            current_chunk.extend(section_words)
            current_size += section_size

        # Don't forget the last chunk
        if current_chunk:
            chunks.append({
                'text': ' '.join(current_chunk),
                'type': 'section',
                'boundary': 'document_end'
            })

        return chunks if chunks else self.chunk_sliding_window(content, chunk_size, overlap)

    def chunk_by_conversation(self, content: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Chunk keeping conversation turns together."""
        # Pattern for conversation turns (e.g., "Speaker:", "John:", etc.)
        turn_pattern = r'^([A-Z][A-Za-z\s]+):\s*(.+?)(?=^[A-Z][A-Za-z\s]+:|$)'

        turns = re.findall(turn_pattern, content, re.MULTILINE | re.DOTALL)

        if not turns:
            return self.chunk_sliding_window(content, chunk_size, overlap)

        chunks = []
        current_chunk = []
        current_speakers = set()
        current_size = 0

        for speaker, text in turns:
            turn_size = len(text.split())

            if current_size + turn_size > chunk_size and current_chunk:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'type': 'conversation',
                    'speakers': ', '.join(list(current_speakers))  # Convert to string for ChromaDB
                })

                # Keep last turn for context
                if overlap > 0:
                    current_chunk = [f"{speaker}: {text[:overlap]}"]
                    current_speakers = {speaker}
                    current_size = min(overlap, turn_size)
                else:
                    current_chunk = []
                    current_speakers = set()
                    current_size = 0

            current_chunk.append(f"{speaker}: {text}")
            current_speakers.add(speaker)
            current_size += turn_size

        if current_chunk:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'type': 'conversation',
                'speakers': ', '.join(list(current_speakers))  # Convert to string for ChromaDB
            })

        return chunks

    def chunk_by_messages(self, content: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Chunk by message boundaries (emails, etc.)."""
        # Look for email-like boundaries
        message_boundary = r'(From:|Subject:|Date:|---+|===+|\n\n\n+)'
        messages = re.split(message_boundary, content)

        chunks = []
        current_chunk = []
        current_size = 0

        for msg in messages:
            msg_size = len(msg.split())

            if current_size + msg_size > chunk_size and current_chunk:
                chunks.append({
                    'text': ' '.join(current_chunk),
                    'type': 'message',
                    'boundary': 'message_end'
                })
                current_chunk = []
                current_size = 0

            if msg.strip():
                current_chunk.append(msg)
                current_size += msg_size

        if current_chunk:
            chunks.append({
                'text': ' '.join(current_chunk),
                'type': 'message',
                'boundary': 'thread_end'
            })

        return chunks if chunks else self.chunk_sliding_window(content, chunk_size, overlap)

    def chunk_by_endpoints(self, content: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Chunk API documentation by endpoints."""
        # Look for API endpoint patterns
        endpoint_patterns = [
            r'^(GET|POST|PUT|DELETE|PATCH)\s+/\S+',
            r'^### .+ Endpoint',
            r'^## /\S+'
        ]

        # Try to split by endpoints
        for pattern in endpoint_patterns:
            if re.search(pattern, content, re.MULTILINE):
                endpoints = re.split(f'({pattern})', content, flags=re.MULTILINE)

                chunks = []
                current_chunk = []
                current_endpoint = None

                for part in endpoints:
                    if re.match(pattern, part):
                        if current_chunk:
                            chunks.append({
                                'text': '\n'.join(current_chunk),
                                'type': 'api_endpoint',
                                'endpoint': current_endpoint
                            })
                        current_endpoint = part.strip()
                        current_chunk = [part]
                    else:
                        current_chunk.append(part)

                if current_chunk:
                    chunks.append({
                        'text': '\n'.join(current_chunk),
                        'type': 'api_endpoint',
                        'endpoint': current_endpoint
                    })

                return chunks

        return self.chunk_by_sections(content, chunk_size, overlap)

    def chunk_by_chapters(self, content: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Chunk books/long documents by chapters."""
        chapter_patterns = [
            r'^Chapter\s+\d+',
            r'^CHAPTER\s+[IVX]+',
            r'^\d+\.\s+[A-Z]'
        ]

        for pattern in chapter_patterns:
            if re.search(pattern, content, re.MULTILINE):
                chapters = re.split(f'({pattern})', content, flags=re.MULTILINE)

                chunks = []
                current_chapter = None

                for i in range(0, len(chapters), 2):
                    if i + 1 < len(chapters):
                        chapter_title = chapters[i] if i > 0 else None
                        chapter_content = chapters[i + 1] if i == 0 else chapters[i] + chapters[i + 1]

                        # Further chunk if chapter is too long
                        if len(chapter_content.split()) > chunk_size:
                            sub_chunks = self.chunk_sliding_window(chapter_content, chunk_size, overlap)
                            for sub_chunk in sub_chunks:
                                sub_chunk['chapter'] = chapter_title
                                sub_chunk['type'] = 'chapter_section'
                                chunks.append(sub_chunk)
                        else:
                            chunks.append({
                                'text': chapter_content,
                                'type': 'chapter',
                                'chapter': chapter_title
                            })

                return chunks

        return self.chunk_by_sections(content, chunk_size, overlap)

    def chunk_by_records(self, content: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Chunk structured data by records."""
        # Try to detect record boundaries (CSV, logs, etc.)
        lines = content.split('\n')

        # Check if it looks like CSV or structured data
        if len(lines) > 1 and all(',' in line or '\t' in line for line in lines[:5]):
            # Group records
            chunks = []
            current_chunk = []
            header = lines[0] if lines else ""

            for line in lines[1:]:
                current_chunk.append(line)

                if len('\n'.join(current_chunk).split()) > chunk_size:
                    chunks.append({
                        'text': header + '\n' + '\n'.join(current_chunk),
                        'type': 'records',
                        'record_count': len(current_chunk)
                    })
                    current_chunk = []

            if current_chunk:
                chunks.append({
                    'text': header + '\n' + '\n'.join(current_chunk),
                    'type': 'records',
                    'record_count': len(current_chunk)
                })

            return chunks

        return self.chunk_sliding_window(content, chunk_size, overlap)

    def chunk_by_timestamps(self, content: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Chunk time-based content (subtitles, transcripts with timestamps)."""
        # Look for timestamp patterns
        timestamp_patterns = [
            r'(\d{2}:\d{2}:\d{2})',  # HH:MM:SS
            r'(\[\d{2}:\d{2}\])',     # [MM:SS]
            r'(\d{2}:\d{2})'          # MM:SS
        ]

        for pattern in timestamp_patterns:
            if re.search(pattern, content):
                # Split by timestamps
                parts = re.split(pattern, content)

                chunks = []
                current_chunk = []
                current_time = None

                for i, part in enumerate(parts):
                    if re.match(pattern, part):
                        current_time = part
                    else:
                        if current_time:
                            current_chunk.append(f"{current_time} {part}")
                        else:
                            current_chunk.append(part)

                        if len(' '.join(current_chunk).split()) > chunk_size:
                            chunks.append({
                                'text': ' '.join(current_chunk),
                                'type': 'timed_content',
                                'has_timestamps': True
                            })
                            current_chunk = []

                if current_chunk:
                    chunks.append({
                        'text': ' '.join(current_chunk),
                        'type': 'timed_content',
                        'has_timestamps': True
                    })

                return chunks

        return self.chunk_sliding_window(content, chunk_size, overlap)


class DocumentRelationshipDetector:
    """Detects relationships between documents for better context understanding."""

    def detect_relationships(self, documents: List[Dict]) -> Dict[str, List[str]]:
        """
        Detect relationships between documents.
        Returns a graph of document relationships.
        """
        relationships = {}

        for i, doc1 in enumerate(documents):
            doc1_id = doc1.get('id', str(i))
            relationships[doc1_id] = []

            for j, doc2 in enumerate(documents):
                if i == j:
                    continue

                doc2_id = doc2.get('id', str(j))

                # Check for various relationship types
                if self._is_same_series(doc1, doc2):
                    relationships[doc1_id].append(f"series:{doc2_id}")

                if self._is_response_to(doc1, doc2):
                    relationships[doc1_id].append(f"response_to:{doc2_id}")

                if self._shares_participants(doc1, doc2):
                    relationships[doc1_id].append(f"shared_participants:{doc2_id}")

                if self._is_version_of(doc1, doc2):
                    relationships[doc1_id].append(f"version_of:{doc2_id}")

        return relationships

    def _is_same_series(self, doc1: Dict, doc2: Dict) -> bool:
        """Check if documents are part of the same series."""
        # Check for similar naming patterns
        name1 = doc1.get('filename', '').lower()
        name2 = doc2.get('filename', '').lower()

        # Remove numbers and check similarity
        base1 = re.sub(r'\d+', '', name1)
        base2 = re.sub(r'\d+', '', name2)

        return base1 == base2 and base1 != ''

    def _is_response_to(self, doc1: Dict, doc2: Dict) -> bool:
        """Check if one document is a response to another."""
        # Check for RE: in subjects or similar patterns
        if 'subject' in doc1.get('metadata', {}) and 'subject' in doc2.get('metadata', {}):
            subj1 = doc1['metadata']['subject'].lower()
            subj2 = doc2['metadata']['subject'].lower()

            return f"re: {subj2}" in subj1 or f"re: {subj1}" in subj2

        return False

    def _shares_participants(self, doc1: Dict, doc2: Dict) -> bool:
        """Check if documents share participants."""
        participants1 = set(doc1.get('metadata', {}).get('participants', []))
        participants2 = set(doc2.get('metadata', {}).get('participants', []))

        if participants1 and participants2:
            return len(participants1 & participants2) > 0

        return False

    def _is_version_of(self, doc1: Dict, doc2: Dict) -> bool:
        """Check if documents are different versions of the same content."""
        # Check for version indicators
        v1 = doc1.get('metadata', {}).get('version')
        v2 = doc2.get('metadata', {}).get('version')

        if v1 and v2 and v1 != v2:
            # Same base name but different versions
            name1 = re.sub(r'v?\d+(\.\d+)*', '', doc1.get('filename', '')).strip()
            name2 = re.sub(r'v?\d+(\.\d+)*', '', doc2.get('filename', '')).strip()

            return name1 == name2 and name1 != ''

        return False