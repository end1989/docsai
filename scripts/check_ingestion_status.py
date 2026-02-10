#!/usr/bin/env python
"""
Quick status checker for ingestion - shows what's actually happening
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"

def check_status():
    """Check current ingestion status"""

    print("\n" + "="*70)
    print("INGESTION STATUS CHECK")
    print("="*70)

    try:
        # Check active task
        response = requests.get(f"{BASE_URL}/ingestion/active")
        data = response.json()

        if not data.get("active_task"):
            print("\n❌ No active ingestion task found!")
            print("\nPossible reasons:")
            print("  1. Ingestion completed")
            print("  2. Ingestion failed")
            print("  3. Not started yet")
            return

        task = data["active_task"]

        print(f"\n✅ Active Ingestion Found!")
        print(f"\nProfile: {task['profile_name']}")
        print(f"Task ID: {task['id']}")
        print(f"Status: {task['status']}")
        print(f"\nProgress: {task['progress']*100:.1f}%")
        print(f"Files: {task['processed_files']}/{task['total_files']}")
        print(f"Chunks: {task['indexed_chunks']}/{task['total_chunks']}")

        if task.get('current_file'):
            print(f"\nCurrently Processing:")
            print(f"  {task['current_file'][:80]}...")

        # Check if it's actually moving
        print("\n⏱️  Checking if progress is moving...")
        time.sleep(5)

        response2 = requests.get(f"{BASE_URL}/ingestion/active")
        task2 = response2.json().get("active_task")

        if task2:
            if task2['processed_files'] > task['processed_files']:
                print(f"✅ Progress IS moving! Now at {task2['processed_files']} files")
            elif task2['indexed_chunks'] > task['indexed_chunks']:
                print(f"✅ Chunks being indexed! Now at {task2['indexed_chunks']} chunks")
            elif task2['current_file'] != task.get('current_file'):
                print(f"✅ Processing new file: {task2['current_file'][:50]}...")
            else:
                print(f"⚠️  No visible progress in 5 seconds")
                print("    (May be processing a large file or waiting for response)")

        # Show any errors
        if task.get('errors'):
            print(f"\n❌ Errors detected: {len(task['errors'])}")
            for err in task['errors'][:3]:
                print(f"  - {err}")

        if task.get('warnings'):
            print(f"\n⚠️  Warnings: {len(task['warnings'])}")
            for warn in task['warnings'][:3]:
                print(f"  - {warn}")

        # Estimate time
        if task.get('start_time'):
            start = datetime.fromisoformat(task['start_time'])
            elapsed = (datetime.now() - start).total_seconds()
            print(f"\nTime Elapsed: {int(elapsed//60)}m {int(elapsed%60)}s")

            if task['processed_files'] > 0 and task['total_files'] > 0:
                rate = task['processed_files'] / elapsed
                remaining = (task['total_files'] - task['processed_files']) / rate if rate > 0 else 0
                print(f"Estimated Time Remaining: {int(remaining//60)}m")

    except Exception as e:
        print(f"\n❌ Error checking status: {e}")
        print("\nTroubleshooting:")
        print("  1. Is the backend running?")
        print("  2. Check the backend console for errors")
        print("  3. Try: curl http://localhost:8080/ingestion/active")

def continuous_monitor():
    """Continuously monitor with simple updates"""

    print("\nCONTINUOUS MONITORING (Ctrl+C to stop)")
    print("-" * 50)

    last_files = 0
    last_chunks = 0
    stalled_count = 0

    while True:
        try:
            response = requests.get(f"{BASE_URL}/ingestion/active")
            task = response.json().get("active_task")

            if not task:
                print("\n❌ No active task!")
                break

            # Check if progress changed
            files_changed = task['processed_files'] != last_files
            chunks_changed = task['indexed_chunks'] != last_chunks

            if files_changed or chunks_changed:
                stalled_count = 0
                timestamp = datetime.now().strftime("%H:%M:%S")

                print(f"\n[{timestamp}] Status: {task['status']}")
                print(f"  Files: {task['processed_files']}/{task['total_files']} "
                      f"({task['progress']*100:.1f}%)")
                print(f"  Chunks: {task['indexed_chunks']}/{task['total_chunks']}")

                if task.get('current_file'):
                    print(f"  Current: ...{task['current_file'][-60:]}")

                last_files = task['processed_files']
                last_chunks = task['indexed_chunks']
            else:
                stalled_count += 1
                if stalled_count == 1:
                    print(".", end="", flush=True)
                elif stalled_count % 10 == 0:
                    print(f" [{stalled_count*5}s stalled]", end="", flush=True)

            if task['status'] in ['completed', 'failed', 'cancelled']:
                print(f"\n\n🏁 Ingestion {task['status'].upper()}!")
                break

            time.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(5)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        continuous_monitor()
    else:
        check_status()
        print("\n💡 Tip: Run 'python check_ingestion_status.py watch' for continuous monitoring")