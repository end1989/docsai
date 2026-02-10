#!/usr/bin/env python
"""
Simple ingestion status checker - Windows compatible (no emojis)
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"

def check_now():
    """Check current status once"""

    print("\n" + "="*70)
    print("INGESTION STATUS")
    print("="*70)

    try:
        response = requests.get(f"{BASE_URL}/ingestion/active")
        data = response.json()

        if not data.get("active_task"):
            print("\n[X] No active ingestion task")

            # Try to check the last task
            print("\nChecking for completed/failed tasks...")
            return

        task = data["active_task"]

        print(f"\n[OK] Active Ingestion Found!")
        print(f"\nProfile: {task['profile_name']}")
        print(f"Task ID: {task['id']}")
        print(f"Status: {task['status'].upper()}")

        # Progress bar
        progress = task['progress'] * 100
        bar_length = 40
        filled = int(bar_length * task['progress'])
        bar = '#' * filled + '-' * (bar_length - filled)

        print(f"\nProgress: [{bar}] {progress:.1f}%")
        print(f"Files: {task['processed_files']}/{task['total_files']}")
        print(f"Chunks: {task['indexed_chunks']}/{task['total_chunks']}")

        if task.get('current_file'):
            # Show last part of URL
            current = task['current_file']
            if len(current) > 70:
                current = "..." + current[-67:]
            print(f"\nProcessing: {current}")

        # Time stats
        if task.get('start_time'):
            start = datetime.fromisoformat(task['start_time'])
            elapsed = (datetime.now() - start).total_seconds()
            print(f"\nElapsed: {int(elapsed//60)}m {int(elapsed%60)}s")

            # Estimate
            if task['processed_files'] > 0 and task['total_files'] > 0:
                rate = task['processed_files'] / elapsed * 60  # files per minute
                remaining_files = task['total_files'] - task['processed_files']
                eta_minutes = remaining_files / rate if rate > 0 else 0
                print(f"Rate: {rate:.1f} files/min")
                print(f"ETA: ~{int(eta_minutes)}m remaining")

        # Errors and warnings
        if task.get('errors'):
            print(f"\n[ERROR] {len(task['errors'])} errors found:")
            for err in task['errors'][:3]:
                print(f"  - {err[:100]}...")

        if task.get('warnings'):
            print(f"\n[WARN] {len(task['warnings'])} warnings:")
            for warn in task['warnings'][:3]:
                print(f"  - {warn[:100]}...")

    except Exception as e:
        print(f"\n[ERROR] Cannot check status: {e}")
        print("\nTry checking the backend console directly")

def watch():
    """Watch continuously with updates every 10 seconds"""

    print("\nWATCHING INGESTION (Ctrl+C to stop)")
    print("Updates every 10 seconds...")
    print("-" * 50)

    last_files = 0
    last_chunks = 0
    no_change_count = 0

    while True:
        try:
            response = requests.get(f"{BASE_URL}/ingestion/active")
            task = response.json().get("active_task")

            if not task:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] No active task")
                break

            # Detect changes
            files_delta = task['processed_files'] - last_files
            chunks_delta = task['indexed_chunks'] - last_chunks

            if files_delta > 0 or chunks_delta > 0:
                no_change_count = 0

                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{timestamp}] UPDATE:")
                print(f"  Status: {task['status']}")
                print(f"  Progress: {task['progress']*100:.1f}%")
                print(f"  Files: {task['processed_files']}/{task['total_files']} (+{files_delta})")
                print(f"  Chunks: {task['indexed_chunks']}/{task['total_chunks']} (+{chunks_delta})")

                if task.get('current_file'):
                    current = task['current_file']
                    if len(current) > 60:
                        current = "..." + current[-57:]
                    print(f"  Now processing: {current}")

                last_files = task['processed_files']
                last_chunks = task['indexed_chunks']

            else:
                no_change_count += 1
                if no_change_count == 1:
                    print(".", end="", flush=True)
                elif no_change_count % 6 == 0:  # Every minute
                    print(f" [No change for {no_change_count*10}s]", end="", flush=True)

            # Check if finished
            if task['status'] in ['completed', 'failed', 'cancelled']:
                print(f"\n\n[DONE] Ingestion {task['status'].upper()}")

                if task['status'] == 'completed':
                    print(f"  Total files: {task['processed_files']}")
                    print(f"  Total chunks: {task['indexed_chunks']}")
                break

            time.sleep(10)  # Check every 10 seconds

        except KeyboardInterrupt:
            print("\n\n[STOPPED] Monitoring stopped by user")
            print("Ingestion continues in background")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            time.sleep(10)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        watch()
    else:
        check_now()
        print("\nRun 'python ingestion_status.py watch' for continuous monitoring")