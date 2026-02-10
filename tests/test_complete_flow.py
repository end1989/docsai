#!/usr/bin/env python
"""
Test script to verify the complete system flow:
1. Create a new profile via API
2. Start ingestion for the profile
3. Monitor ingestion progress
4. Switch profiles
5. Query the system
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8080"

def test_create_profile():
    """Test creating a new profile."""
    print("\n1. Testing profile creation...")

    # Create a test profile
    profile_data = {
        "name": "test_mixed",
        "sourceType": "mixed",
        "webDomains": ["https://docs.python.org"],
        "localPaths": ["/path/to/documents"],
        "fileTypes": ["pdf", "txt", "md"],
        "crawlDepth": 1,
        "chunkSize": 800,
        "description": "Test profile with mixed sources"
    }

    try:
        response = requests.post(f"{BASE_URL}/profiles/create", json=profile_data)
        if response.status_code == 200:
            print("✅ Profile created successfully")
            return True
        elif response.status_code == 409:
            print("⚠️ Profile already exists")
            return True
        else:
            print(f"❌ Failed to create profile: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating profile: {e}")
        return False

def test_list_profiles():
    """Test listing profiles."""
    print("\n2. Testing profile listing...")

    try:
        response = requests.get(f"{BASE_URL}/profiles/list")
        if response.status_code == 200:
            profiles = response.json()["profiles"]
            print(f"✅ Found {len(profiles)} profiles:")
            for p in profiles:
                print(f"   - {p['name']} ({p['source_type']})")
            return True
        else:
            print(f"❌ Failed to list profiles: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error listing profiles: {e}")
        return False

def test_ingestion(profile_name="stripe"):
    """Test starting and monitoring ingestion."""
    print(f"\n3. Testing ingestion for profile '{profile_name}'...")

    # Start ingestion
    try:
        response = requests.post(f"{BASE_URL}/ingestion/start/{profile_name}")
        if response.status_code == 200:
            data = response.json()
            task_id = data["task_id"]
            print(f"✅ Ingestion started with task ID: {task_id}")

            # Monitor progress
            print("   Monitoring progress (press Ctrl+C to skip)...")
            prev_status = None

            for i in range(60):  # Monitor for up to 60 seconds
                try:
                    status_response = requests.get(f"{BASE_URL}/ingestion/status/{task_id}")
                    if status_response.status_code == 200:
                        status = status_response.json()

                        # Only print if status changed
                        if status['status'] != prev_status:
                            print(f"   Status: {status['status']} | "
                                  f"Progress: {status['progress']*100:.1f}% | "
                                  f"Files: {status['processed_files']}/{status['total_files']} | "
                                  f"Chunks: {status['indexed_chunks']}/{status['total_chunks']}")
                            prev_status = status['status']

                        if status['status'] in ['completed', 'failed', 'cancelled']:
                            if status['status'] == 'completed':
                                print(f"✅ Ingestion completed successfully!")
                                if status.get('stats', {}).get('categories'):
                                    print("   Document categories found:")
                                    for cat, count in status['stats']['categories'].items():
                                        print(f"     - {cat}: {count}")
                            elif status['status'] == 'failed':
                                print(f"❌ Ingestion failed: {status.get('errors', [])}")
                            else:
                                print(f"⚠️ Ingestion cancelled")
                            break

                    time.sleep(1)

                except KeyboardInterrupt:
                    print("\n   Skipping monitoring...")
                    break

            return True
        else:
            print(f"❌ Failed to start ingestion: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return False

def test_profile_switch():
    """Test switching profiles."""
    print("\n4. Testing profile switching...")

    try:
        response = requests.post(f"{BASE_URL}/profile/switch/stripe")
        if response.status_code == 200:
            print(f"✅ Successfully switched to profile 'stripe'")
            return True
        else:
            print(f"❌ Failed to switch profile: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error switching profile: {e}")
        return False

def test_query():
    """Test querying the system."""
    print("\n5. Testing query functionality...")

    questions = [
        "What is the OAuth flow?",
        "How do webhooks work?",
        "Tell me about rate limiting"
    ]

    for question in questions[:1]:  # Test with first question
        try:
            response = requests.get(f"{BASE_URL}/ask", params={"q": question})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Query successful for: '{question}'")
                print(f"   Answer preview: {data['answer'][:100]}...")
                if data.get('citations'):
                    print(f"   Citations: {len(data['citations'])} sources")
                return True
            else:
                print(f"❌ Query failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error during query: {e}")
            return False

def test_active_ingestion():
    """Test checking for active ingestion."""
    print("\n6. Testing active ingestion check...")

    try:
        response = requests.get(f"{BASE_URL}/ingestion/active")
        if response.status_code == 200:
            data = response.json()
            if data["active_task"]:
                print(f"✅ Active ingestion found: {data['active_task']['profile_name']}")
            else:
                print("✅ No active ingestion (as expected)")
            return True
        else:
            print(f"❌ Failed to check active ingestion: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error checking active ingestion: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING COMPLETE SYSTEM FLOW")
    print("=" * 60)
    print("\nMake sure the backend is running on port 8080")
    print("Start with: python -m docsai.main serve stripe")
    input("\nPress Enter to start tests...")

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Backend is not running!")
            return
    except:
        print("❌ Cannot connect to backend at http://localhost:8080")
        print("   Please start the backend first: python -m docsai.main serve stripe")
        return

    print("✅ Backend is running")

    # Run tests
    tests = [
        ("List Profiles", test_list_profiles),
        ("Create Profile", test_create_profile),
        ("Switch Profile", test_profile_switch),
        ("Check Active Ingestion", test_active_ingestion),
        ("Start Ingestion", lambda: test_ingestion("stripe")),
        ("Query System", test_query),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()