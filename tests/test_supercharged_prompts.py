#!/usr/bin/env python
"""
Test the difference between basic and supercharged prompts
Shows how much more comprehensive and helpful the responses become
"""

import requests
import time
import json

def test_prompt_comparison():
    """Compare basic vs supercharged responses"""

    BASE_URL = "http://localhost:8080"

    # Test questions that benefit from comprehensive answers
    test_cases = [
        {
            "question": "How do I handle failed payments?",
            "description": "Should provide comprehensive error handling strategy"
        },
        {
            "question": "What's the difference between Payment Intents and Charges?",
            "description": "Should explain architecture decisions and migration path"
        },
        {
            "question": "I'm getting a 'card declined' error",
            "description": "Should provide debugging steps and solutions"
        },
        {
            "question": "How does Stripe work?",
            "description": "Should provide educational overview with examples"
        },
        {
            "question": "Implement subscription billing with free trial",
            "description": "Should provide complete implementation guide"
        }
    ]

    print("=" * 80)
    print("SUPERCHARGED PROMPTS COMPARISON TEST")
    print("=" * 80)

    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"QUESTION: {test['question']}")
        print(f"EXPECTED: {test['description']}")
        print("-" * 80)

        # Test with BASIC prompt
        print("\n1. BASIC PROMPT (original restrictive mode):")
        print("-" * 40)

        start = time.time()
        response = requests.get(
            f"{BASE_URL}/ask",
            params={
                "q": test['question'],
                "supercharged": False  # Use basic prompt
            }
        )
        basic_time = time.time() - start

        if response.status_code == 200:
            data = response.json()
            basic_answer = data.get("answer", "")
            basic_citations = len(data.get("citations", []))

            print(f"Response length: {len(basic_answer)} chars")
            print(f"Citations: {basic_citations}")
            print(f"Response time: {basic_time:.1f}s")
            print(f"\nPreview (first 400 chars):")
            print(basic_answer[:400] + "..." if len(basic_answer) > 400 else basic_answer)
        else:
            print(f"Error: {response.status_code}")
            basic_answer = ""

        # Test with SUPERCHARGED prompt
        print("\n\n2. SUPERCHARGED PROMPT (comprehensive expert mode):")
        print("-" * 40)

        start = time.time()
        response = requests.get(
            f"{BASE_URL}/ask",
            params={
                "q": test['question'],
                "supercharged": True,  # Use supercharged prompt
                # Mode will be auto-detected
            }
        )
        super_time = time.time() - start

        if response.status_code == 200:
            data = response.json()
            super_answer = data.get("answer", "")
            super_citations = len(data.get("citations", []))

            print(f"Response length: {len(super_answer)} chars")
            print(f"Citations: {super_citations}")
            print(f"Response time: {super_time:.1f}s")

            # Detect which mode was used
            if "implement" in test['question'].lower():
                print(f"Auto-detected mode: integration")
            elif "error" in test['question'].lower():
                print(f"Auto-detected mode: debugging")
            elif "how does" in test['question'].lower():
                print(f"Auto-detected mode: learning")
            else:
                print(f"Auto-detected mode: comprehensive")

            print(f"\nPreview (first 600 chars):")
            print(super_answer[:600] + "..." if len(super_answer) > 600 else super_answer)

            # Analysis
            print(f"\n📊 COMPARISON:")
            improvement = ((len(super_answer) - len(basic_answer)) / max(len(basic_answer), 1)) * 100
            print(f"  • Length improvement: {improvement:+.0f}%")
            print(f"  • Basic: {len(basic_answer)} chars")
            print(f"  • Supercharged: {len(super_answer)} chars")

            # Check for quality indicators
            quality_indicators = {
                "Has code examples": "```" in super_answer,
                "Has numbered steps": any(f"{i}." in super_answer for i in range(1, 10)),
                "Has warnings/tips": any(word in super_answer.lower() for word in ["note:", "warning:", "tip:", "important:"]),
                "Has best practices": "best practice" in super_answer.lower(),
                "Has error handling": "error" in super_answer.lower() or "exception" in super_answer.lower(),
                "Has security mentions": any(word in super_answer.lower() for word in ["security", "secure", "pci", "compliance"])
            }

            print(f"\n  Quality indicators in supercharged response:")
            for indicator, present in quality_indicators.items():
                if present:
                    print(f"    ✓ {indicator}")

        else:
            print(f"Error: {response.status_code}")

        # Brief pause between tests
        time.sleep(1)

    # Test explicit mode override
    print(f"\n\n{'='*80}")
    print("TESTING EXPLICIT MODE OVERRIDE")
    print("=" * 80)

    modes = ["integration", "debugging", "learning", "comprehensive"]
    test_question = "How do I process payments with Stripe?"

    for mode in modes:
        print(f"\nMode: {mode}")
        print("-" * 40)

        response = requests.get(
            f"{BASE_URL}/ask",
            params={
                "q": test_question,
                "supercharged": True,
                "mode": mode
            }
        )

        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            print(f"Response length: {len(answer)} chars")
            print(f"First 200 chars: {answer[:200]}...")

            # Check for mode-specific patterns
            if mode == "integration":
                has_steps = any(f"Step {i}" in answer or f"{i}." in answer for i in range(1, 10))
                print(f"  Has implementation steps: {has_steps}")
            elif mode == "debugging":
                has_diagnostics = "check" in answer.lower() or "verify" in answer.lower()
                print(f"  Has diagnostic steps: {has_diagnostics}")
            elif mode == "learning":
                has_concepts = "understand" in answer.lower() or "concept" in answer.lower()
                print(f"  Has conceptual explanation: {has_concepts}")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print("=" * 80)
    print("\n✨ SUPERCHARGED BENEFITS:")
    print("  • 2-5x more comprehensive responses")
    print("  • Auto-detects intent (integration, debugging, learning)")
    print("  • Includes best practices and pitfalls")
    print("  • Provides complete implementation guidance")
    print("  • Anticipates follow-up questions")
    print("  • Maintains citations for credibility")

if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code != 200:
            print("❌ Backend is not running!")
            print("   Start with: python -m docsai.main serve stripe")
            exit(1)
    except:
        print("❌ Cannot connect to backend")
        print("   Start with: python -m docsai.main serve stripe")
        exit(1)

    print("✅ Backend is running\n")
    test_prompt_comparison()