#!/usr/bin/env python
"""
Analyze how Stripe documentation is indexed to diagnose why responses are shallow
"""

import chromadb
from chromadb.config import Settings
import json
from collections import Counter
import re

def analyze_stripe_indexing():
    """Analyze the quality of Stripe documentation indexing"""

    print("=" * 60)
    print("STRIPE DOCUMENTATION INDEXING ANALYSIS")
    print("=" * 60)

    # Connect to ChromaDB
    client = chromadb.Client(Settings(
        is_persistent=True,
        persist_directory='profiles/stripe/data/chroma'
    ))

    try:
        coll = client.get_collection(name="docs")
    except:
        print("ERROR: No 'docs' collection found. Has ingestion been run?")
        return

    # Get collection stats
    total_chunks = coll.count()
    print(f"\n1. COLLECTION STATS")
    print(f"   Total chunks indexed: {total_chunks}")

    # Sample some chunks to see structure
    sample = coll.peek(10)

    if sample['metadatas']:
        print(f"\n2. METADATA ANALYSIS")
        # Analyze metadata fields
        all_keys = set()
        for meta in sample['metadatas']:
            all_keys.update(meta.keys())
        print(f"   Metadata fields: {', '.join(sorted(all_keys))}")

        # Check categories if present
        if any('category' in m for m in sample['metadatas']):
            categories = [m.get('category', 'unknown') for m in sample['metadatas']]
            print(f"   Sample categories: {', '.join(set(categories))}")

    # Test critical queries
    print(f"\n3. QUERY QUALITY TEST")

    test_queries = [
        ("payment intents", "Should find Payment Intents API info"),
        ("webhooks endpoint", "Should find webhook setup docs"),
        ("create subscription", "Should find subscription API"),
        ("stripe.js card element", "Should find frontend integration"),
        ("3d secure authentication", "Should find SCA/3DS docs"),
        ("idempotency key", "Should find idempotency docs"),
    ]

    for query, description in test_queries:
        results = coll.query(
            query_texts=[query],
            n_results=5
        )

        print(f"\n   Query: '{query}'")
        print(f"   ({description})")

        if results['documents'][0]:
            # Analyze first result
            first_chunk = results['documents'][0][0]

            # Check if it contains relevant keywords
            relevant_keywords = {
                "payment intents": ["PaymentIntent", "payment_intent", "confirmPayment"],
                "webhooks endpoint": ["webhook", "endpoint", "stripe listen", "signature"],
                "create subscription": ["subscription", "subscribe", "billing", "recurring"],
                "stripe.js card element": ["Stripe.js", "CardElement", "PaymentElement", "Elements"],
                "3d secure authentication": ["3D Secure", "SCA", "authentication", "confirmCardPayment"],
                "idempotency key": ["idempotency", "Idempotency-Key", "duplicate", "retry"]
            }

            keywords_found = []
            for keyword in relevant_keywords.get(query.split()[0], []):
                if keyword.lower() in first_chunk.lower():
                    keywords_found.append(keyword)

            print(f"   ✓ Found chunk with {len(first_chunk)} chars")
            print(f"   Keywords found: {keywords_found if keywords_found else 'None'}")
            print(f"   Preview: {first_chunk[:150]}...")

            # Check metadata
            if results['metadatas'][0]:
                meta = results['metadatas'][0][0]
                if 'source_url' in meta:
                    print(f"   Source: {meta['source_url']}")
        else:
            print(f"   ✗ No results found!")

    # Analyze chunk distribution
    print(f"\n4. CONTENT COVERAGE ANALYSIS")

    # Sample more chunks to analyze content
    larger_sample = coll.get(limit=100)

    if larger_sample['documents']:
        # Look for critical Stripe concepts
        critical_concepts = {
            'payment_intents': r'payment[_\s]?intent',
            'webhooks': r'webhook',
            'customers': r'customer\.create|customers\.create',
            'subscriptions': r'subscription',
            'checkout': r'checkout\.session',
            'elements': r'stripe\.elements|payment[_\s]?element',
            'errors': r'stripe\.error|card[_\s]?error',
            'authentication': r'3d[_\s]?secure|sca|authentication',
        }

        concept_counts = {concept: 0 for concept in critical_concepts}

        for doc in larger_sample['documents']:
            for concept, pattern in critical_concepts.items():
                if re.search(pattern, doc, re.IGNORECASE):
                    concept_counts[concept] += 1

        print(f"   Coverage of critical concepts (out of {len(larger_sample['documents'])} sampled chunks):")
        for concept, count in concept_counts.items():
            percentage = (count / len(larger_sample['documents'])) * 100
            status = "✓" if percentage > 10 else "⚠️" if percentage > 5 else "✗"
            print(f"   {status} {concept}: {count} chunks ({percentage:.1f}%)")

    # Check chunk sizes
    print(f"\n5. CHUNK SIZE ANALYSIS")
    if larger_sample['documents']:
        chunk_sizes = [len(doc) for doc in larger_sample['documents']]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        min_size = min(chunk_sizes)
        max_size = max(chunk_sizes)

        print(f"   Average chunk size: {avg_size:.0f} chars")
        print(f"   Min size: {min_size} chars")
        print(f"   Max size: {max_size} chars")

        # Check if chunks are too small (might lose context)
        small_chunks = [s for s in chunk_sizes if s < 500]
        if small_chunks:
            print(f"   ⚠️ Warning: {len(small_chunks)} chunks are < 500 chars (may lack context)")

    # Diagnosis
    print(f"\n6. DIAGNOSIS")
    print("=" * 60)

    issues = []

    if total_chunks < 1000:
        issues.append("⚠️ Low chunk count - may not have ingested all documentation")

    if 'payment_intents' in concept_counts and concept_counts['payment_intents'] < 5:
        issues.append("⚠️ Payment Intents poorly covered - critical modern API missing")

    if 'webhooks' in concept_counts and concept_counts['webhooks'] < 5:
        issues.append("⚠️ Webhooks poorly covered - essential for production")

    if avg_size < 800:
        issues.append("⚠️ Chunks may be too small - losing important context")

    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("   ✓ Indexing appears healthy")

    print(f"\n7. RECOMMENDATIONS")
    print("=" * 60)
    print("   1. Check crawl depth - may need deeper crawling for API reference")
    print("   2. Verify allowed_paths includes /docs/api/*")
    print("   3. Consider larger chunk_size (1200-1500) for technical docs")
    print("   4. Ensure HTML-to-Markdown preserves code examples")
    print("   5. Check if navigation/menus are polluting content")

if __name__ == "__main__":
    analyze_stripe_indexing()