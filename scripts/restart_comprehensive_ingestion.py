#!/usr/bin/env python
"""
Restart ingestion with comprehensive documentation access
Now includes ALL important documentation trees, not just API reference
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8080"

def check_and_restart_ingestion():
    """Check current ingestion and restart with comprehensive config"""

    print("=" * 70)
    print("COMPREHENSIVE STRIPE DOCUMENTATION INGESTION")
    print("=" * 70)

    print("\n📋 NEW COVERAGE INCLUDES:")
    print("  ✅ /api - API Reference (what you had)")
    print("  ✅ /payments - Payment implementation guides")
    print("  ✅ /webhooks - Webhook integration")
    print("  ✅ /stripe-js - Frontend integration")
    print("  ✅ /testing - Test cards and scenarios")
    print("  ✅ /billing - Subscriptions")
    print("  ✅ /security - Best practices")
    print("  ✅ /development - Quickstart guides")
    print("  ... and much more!")

    # Check if ingestion is currently running
    try:
        response = requests.get(f"{BASE_URL}/ingestion/active")
        active = response.json().get("active_task")

        if active:
            print(f"\n⚠️ Current ingestion running: {active['profile_name']}")
            print(f"   Status: {active['status']}")
            print(f"   Progress: {active['progress']*100:.1f}%")

            # Ask if should cancel
            response = input("\nCancel current and start comprehensive? (y/n): ")
            if response.lower() == 'y':
                # Cancel current
                cancel_response = requests.post(
                    f"{BASE_URL}/ingestion/cancel/{active['id']}"
                )
                if cancel_response.status_code == 200:
                    print("✅ Cancelled current ingestion")
                    time.sleep(2)  # Give it time to clean up
            else:
                print("Keeping current ingestion running.")
                return

    except Exception as e:
        print(f"Error checking active ingestion: {e}")

    # Start comprehensive ingestion
    print("\n🚀 Starting comprehensive ingestion...")
    print("This will crawl ALL important documentation sections")
    print("Expected time: 45-90 minutes for complete coverage")

    try:
        response = requests.post(f"{BASE_URL}/ingestion/start/stripe_comprehensive")

        if response.status_code == 200:
            data = response.json()
            task_id = data["task_id"]
            print(f"\n✅ Comprehensive ingestion started!")
            print(f"   Task ID: {task_id}")
            print("\nWhat's happening now:")
            print("  1. Crawling all documentation sections (not just /api)")
            print("  2. Processing implementation guides and tutorials")
            print("  3. Extracting code examples and best practices")
            print("  4. Building comprehensive knowledge base")

            print("\n📊 Monitor progress with:")
            print(f"   python monitor_ingestion.py")

            print("\n💡 Once complete, your questions will get:")
            print("  • Step-by-step implementation guides")
            print("  • Complete code examples")
            print("  • Best practices and security guidance")
            print("  • Testing strategies")
            print("  • Real architectural decisions")

            # Optional: Monitor for a bit
            monitor = input("\nMonitor progress now? (y/n): ")
            if monitor.lower() == 'y':
                monitor_progress(task_id)

        else:
            print(f"❌ Failed to start: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

def monitor_progress(task_id):
    """Monitor ingestion progress"""
    print("\nMonitoring progress (Ctrl+C to stop)...")
    print("-" * 50)

    try:
        while True:
            response = requests.get(f"{BASE_URL}/ingestion/status/{task_id}")
            if response.status_code == 200:
                status = response.json()

                # Clear and rewrite line
                print(f"\rStatus: {status['status']} | "
                      f"Progress: {status['progress']*100:.1f}% | "
                      f"Files: {status['processed_files']}/{status['total_files']} | "
                      f"Chunks: {status['indexed_chunks']}/{status['total_chunks']}",
                      end='', flush=True)

                if status['status'] in ['completed', 'failed', 'cancelled']:
                    print(f"\n\nFinal status: {status['status']}")
                    break

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped. Ingestion continues in background.")

if __name__ == "__main__":
    # Check backend is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Backend not running. Start with:")
            print("   python -m docsai.main serve stripe_comprehensive")
            sys.exit(1)
    except:
        print("❌ Cannot connect to backend. Start with:")
        print("   python -m docsai.main serve stripe_comprehensive")
        sys.exit(1)

    check_and_restart_ingestion()