#!/usr/bin/env python
"""
Test script to verify ingestion works with fixed metadata handling
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_ingestion():
    """Test ingestion with proper error handling."""
    print("Testing ingestion with fixed metadata handling...")

    # Start ingestion for stripe profile
    try:
        response = requests.post(f"{BASE_URL}/ingestion/start/stripe")
        if response.status_code == 200:
            data = response.json()
            task_id = data["task_id"]
            print(f"✅ Ingestion started with task ID: {task_id}")

            # Monitor progress
            print("Monitoring progress...")
            prev_status = None
            error_count = 0

            for i in range(300):  # Monitor for up to 5 minutes
                try:
                    status_response = requests.get(f"{BASE_URL}/ingestion/status/{task_id}")
                    if status_response.status_code == 200:
                        status = status_response.json()

                        # Check for errors
                        if status.get('errors'):
                            print(f"❌ Errors detected: {status['errors'][:3]}")
                            error_count = len(status['errors'])

                        # Only print if status changed
                        if status['status'] != prev_status or i % 10 == 0:
                            print(f"Status: {status['status']} | "
                                  f"Progress: {status['progress']*100:.1f}% | "
                                  f"Files: {status['processed_files']}/{status['total_files']} | "
                                  f"Chunks: {status['indexed_chunks']}/{status['total_chunks']} | "
                                  f"Errors: {error_count}")
                            prev_status = status['status']

                        if status['status'] in ['completed', 'failed', 'cancelled']:
                            if status['status'] == 'completed':
                                print(f"✅ Ingestion completed successfully!")
                                print(f"   Total chunks indexed: {status['indexed_chunks']}")

                                # Show category breakdown if available
                                if status.get('stats', {}).get('categories'):
                                    print("   Document categories:")
                                    for cat, count in status['stats']['categories'].items():
                                        print(f"     - {cat}: {count}")

                                # Test a query to ensure it works
                                test_query()

                            elif status['status'] == 'failed':
                                print(f"❌ Ingestion failed!")
                                if status.get('errors'):
                                    print("   Errors:")
                                    for err in status['errors'][:5]:
                                        print(f"     - {err}")
                            else:
                                print(f"⚠️ Ingestion cancelled")
                            break

                    time.sleep(2)

                except KeyboardInterrupt:
                    print("\nStopping monitoring...")
                    break
                except Exception as e:
                    print(f"Error monitoring: {e}")
                    break

        else:
            print(f"❌ Failed to start ingestion: {response.text}")

    except Exception as e:
        print(f"❌ Error during ingestion: {e}")

def test_query():
    """Test a query after ingestion."""
    print("\nTesting query functionality...")

    test_question = "What are webhooks?"

    try:
        response = requests.get(f"{BASE_URL}/ask", params={"q": test_question})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query successful!")
            print(f"   Question: {test_question}")
            print(f"   Answer preview: {data['answer'][:150]}...")
            if data.get('citations'):
                print(f"   Citations: {len(data['citations'])} sources")
                for cite in data['citations'][:3]:
                    print(f"     - {cite}")
        else:
            print(f"❌ Query failed: {response.text}")

    except Exception as e:
        print(f"❌ Error during query: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING INGESTION WITH FIXED METADATA")
    print("=" * 60)
    print("\nMake sure the backend is running on port 8080")
    print("Start with: python -m docsai.main serve stripe")

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Backend is not running!")
            exit(1)
    except:
        print("❌ Cannot connect to backend at http://localhost:8080")
        print("   Please start the backend first: python -m docsai.main serve stripe")
        exit(1)

    print("✅ Backend is running\n")

    # Run the test
    test_ingestion()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)