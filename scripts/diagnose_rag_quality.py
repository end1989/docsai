#!/usr/bin/env python
"""
Diagnose RAG quality issues - why are responses shallow?
"""

import requests
import json
from pathlib import Path

def diagnose_rag_quality(profile="stripe"):
    """Test RAG quality with increasingly complex questions"""

    BASE_URL = "http://localhost:8080"

    print("=" * 70)
    print(f"RAG QUALITY DIAGNOSIS FOR PROFILE: {profile}")
    print("=" * 70)

    # Test questions from simple to complex
    test_questions = [
        {
            "level": "BASIC",
            "question": "What is a payment intent?",
            "expected_concepts": ["PaymentIntent", "SCA", "payment flow", "confirmPayment"],
            "should_mention": "Payment Intent is the recommended way to collect payments"
        },
        {
            "level": "INTEGRATION",
            "question": "How do I implement a complete Stripe checkout flow with webhooks?",
            "expected_concepts": ["PaymentIntent.create", "Stripe.js", "confirmPayment", "webhook endpoint", "signature verification"],
            "should_mention": "both frontend and backend implementation"
        },
        {
            "level": "ADVANCED",
            "question": "How do I handle failed payments in a subscription with retry logic?",
            "expected_concepts": ["subscription", "invoice.payment_failed", "retry", "dunning", "payment_method"],
            "should_mention": "webhook handling and retry strategy"
        },
        {
            "level": "ARCHITECTURE",
            "question": "What's the difference between using Charges API vs Payment Intents and when should I use each?",
            "expected_concepts": ["Charges", "Payment Intents", "SCA", "3D Secure", "migration"],
            "should_mention": "Payment Intents is recommended for SCA compliance"
        },
        {
            "level": "SECURITY",
            "question": "What security measures should I implement for PCI compliance with Stripe?",
            "expected_concepts": ["PCI", "tokenization", "Stripe.js", "never store card", "HTTPS"],
            "should_mention": "use Stripe Elements or Payment Element"
        }
    ]

    print("\nTesting with increasingly complex questions...\n")

    scores = []

    for test in test_questions:
        print(f"\n{'='*70}")
        print(f"LEVEL: {test['level']}")
        print(f"Question: {test['question']}")
        print("-" * 70)

        try:
            # Make request
            response = requests.get(
                f"{BASE_URL}/ask",
                params={"q": test['question']}
            )

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                citations = data.get("citations", [])

                # Score the response
                score = 0
                max_score = 0
                feedback = []

                # Check for expected concepts (each worth 2 points)
                concepts_found = []
                concepts_missing = []
                for concept in test["expected_concepts"]:
                    max_score += 2
                    if concept.lower() in answer.lower():
                        score += 2
                        concepts_found.append(concept)
                    else:
                        concepts_missing.append(concept)

                # Check if key point is mentioned (worth 3 points)
                max_score += 3
                if test["should_mention"].lower() in answer.lower():
                    score += 3
                    feedback.append(f"✓ Key point mentioned")
                else:
                    feedback.append(f"✗ Missing key point: {test['should_mention']}")

                # Check answer length (1 point for substantial response)
                max_score += 1
                if len(answer) > 500:
                    score += 1
                    feedback.append(f"✓ Substantial response ({len(answer)} chars)")
                else:
                    feedback.append(f"⚠️  Short response ({len(answer)} chars)")

                # Check citations (1 point for having citations)
                max_score += 1
                if citations:
                    score += 1
                    feedback.append(f"✓ {len(citations)} citations provided")
                else:
                    feedback.append(f"✗ No citations")

                # Calculate percentage
                percentage = (score / max_score) * 100 if max_score > 0 else 0
                scores.append(percentage)

                # Display results
                print(f"\nSCORE: {score}/{max_score} ({percentage:.1f}%)")

                if concepts_found:
                    print(f"✓ Concepts found: {', '.join(concepts_found)}")
                if concepts_missing:
                    print(f"✗ Missing concepts: {', '.join(concepts_missing)}")

                for fb in feedback:
                    print(f"  {fb}")

                # Show answer preview
                print(f"\nAnswer preview (first 300 chars):")
                print(f"  {answer[:300]}...")

                if answer == "No relevant documentation found for your question. The database might be empty or need to be populated with 'python -m docsai.main ingest stripe'":
                    print("\n⚠️  WARNING: Database appears empty!")

            else:
                print(f"✗ Request failed: {response.status_code}")
                scores.append(0)

        except Exception as e:
            print(f"✗ Error: {e}")
            scores.append(0)

    # Overall diagnosis
    print(f"\n{'='*70}")
    print("OVERALL DIAGNOSIS")
    print("=" * 70)

    avg_score = sum(scores) / len(scores) if scores else 0

    print(f"\nAverage Score: {avg_score:.1f}%")

    if avg_score >= 80:
        print("✅ EXCELLENT: RAG system is working well")
    elif avg_score >= 60:
        print("⚠️  GOOD: RAG system works but could be improved")
    elif avg_score >= 40:
        print("⚠️  POOR: Significant gaps in knowledge base")
    else:
        print("❌ CRITICAL: RAG system is not providing useful responses")

    print("\nLIKELY ISSUES:")

    if avg_score < 40:
        print("  1. ❌ Incomplete crawling - only indexing subset of documentation")
        print("  2. ❌ Shallow depth - missing nested documentation pages")
        print("  3. ❌ Poor chunking - losing context between related sections")
    elif avg_score < 60:
        print("  1. ⚠️  Limited coverage - some documentation areas missing")
        print("  2. ⚠️  Chunk size may be too small - losing context")
        print("  3. ⚠️  Retrieval not finding most relevant chunks")
    elif avg_score < 80:
        print("  1. ⚠️  Good coverage but could improve chunk overlap")
        print("  2. ⚠️  May need to increase retrieval k values")

    print("\nRECOMMENDATIONS:")
    print("  1. Check allowed_paths in config - should include all doc sections")
    print("  2. Increase crawl depth to at least 4-5 for comprehensive coverage")
    print("  3. Use larger chunk_tokens (1200-1500) for technical documentation")
    print("  4. Increase chunk_overlap to preserve context across boundaries")
    print("  5. Ensure HTML-to-Markdown conversion preserves code blocks")
    print("  6. Consider category-specific chunking strategies")

    # Check current configuration
    config_path = Path(f"profiles/{profile}/config.yaml")
    if config_path.exists():
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        print(f"\nCURRENT CONFIGURATION:")
        print(f"  Allowed paths: {config.get('source', {}).get('allowed_paths', 'Not set')}")
        print(f"  Crawl depth: {config.get('source', {}).get('depth', 'Not set')}")
        print(f"  Chunk tokens: {config.get('ingest', {}).get('chunk_tokens', 'Not set')}")
        print(f"  Chunk overlap: {config.get('ingest', {}).get('chunk_overlap', 'Not set')}")

        # Specific diagnosis based on config
        if config.get('source', {}).get('allowed_paths') == ['/api']:
            print("\n❌ CRITICAL: Only crawling /api - missing guides, tutorials, best practices!")
            print("   This explains why responses lack integration details and context.")

if __name__ == "__main__":
    import sys
    profile = sys.argv[1] if len(sys.argv) > 1 else "stripe"

    # Check if backend is running
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code != 200:
            print("❌ Backend is not running!")
            print("   Start with: python -m docsai.main serve stripe")
            sys.exit(1)
    except:
        print("❌ Cannot connect to backend")
        print("   Start with: python -m docsai.main serve stripe")
        sys.exit(1)

    diagnose_rag_quality(profile)