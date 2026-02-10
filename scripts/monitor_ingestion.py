#!/usr/bin/env python
"""
Monitor ingestion progress in real-time with statistics
"""

import requests
import time
import sys
from datetime import datetime, timedelta

def monitor_ingestion():
    """Monitor active ingestion with detailed statistics"""

    BASE_URL = "http://localhost:8080"

    print("=" * 70)
    print("INGESTION MONITOR")
    print("=" * 70)

    # Check for active ingestion
    try:
        response = requests.get(f"{BASE_URL}/ingestion/active")
        data = response.json()

        if not data.get("active_task"):
            print("No active ingestion found.")
            return

        task = data["active_task"]
        task_id = task["id"]
        start_time = datetime.fromisoformat(task["start_time"]) if task["start_time"] else datetime.now()

        print(f"\nActive Task: {task['profile_name']}")
        print(f"Task ID: {task_id}")
        print(f"Started: {start_time.strftime('%H:%M:%S')}")
        print("-" * 70)

        # Monitor loop
        last_status = None
        last_files = 0
        last_chunks = 0
        stall_counter = 0

        while True:
            try:
                response = requests.get(f"{BASE_URL}/ingestion/status/{task_id}")
                if response.status_code == 200:
                    status = response.json()

                    # Calculate rates
                    elapsed = (datetime.now() - start_time).total_seconds()
                    files_per_min = (status['processed_files'] / elapsed * 60) if elapsed > 0 else 0
                    chunks_per_min = (status['indexed_chunks'] / elapsed * 60) if elapsed > 0 else 0

                    # Detect if progress stalled
                    if status['processed_files'] == last_files and status['indexed_chunks'] == last_chunks:
                        stall_counter += 1
                    else:
                        stall_counter = 0

                    last_files = status['processed_files']
                    last_chunks = status['indexed_chunks']

                    # Estimate time remaining
                    if status['total_files'] > 0 and files_per_min > 0:
                        files_remaining = status['total_files'] - status['processed_files']
                        eta_minutes = files_remaining / files_per_min
                        eta = datetime.now() + timedelta(minutes=eta_minutes)
                        eta_str = f"{int(eta_minutes)}m {int((eta_minutes % 1) * 60)}s"
                    else:
                        eta_str = "Calculating..."

                    # Clear previous lines and update
                    sys.stdout.write("\033[F" * 10)  # Move up 10 lines
                    sys.stdout.write("\033[K" * 10)  # Clear lines

                    print(f"\nStatus: {status['status'].upper()}")
                    print(f"Progress: {status['progress']*100:.1f}%")
                    print(f"\nFiles: {status['processed_files']}/{status['total_files']} ({files_per_min:.1f}/min)")
                    print(f"Chunks: {status['indexed_chunks']}/{status['total_chunks']} ({chunks_per_min:.1f}/min)")

                    if status['current_file']:
                        # Truncate long URLs for display
                        current = status['current_file']
                        if len(current) > 60:
                            current = "..." + current[-57:]
                        print(f"\nCurrent: {current}")

                    print(f"\nElapsed: {int(elapsed//60)}m {int(elapsed%60)}s")
                    print(f"ETA: {eta_str}")

                    # Show warnings if stalled
                    if stall_counter > 10:
                        print("\n⚠️  Progress appears stalled - may be processing large file")

                    # Show errors/warnings count
                    if status.get('errors'):
                        print(f"\n❌ Errors: {len(status['errors'])}")
                    if status.get('warnings'):
                        print(f"⚠️  Warnings: {len(status['warnings'])}")

                    # Check if complete
                    if status['status'] in ['completed', 'failed', 'cancelled']:
                        print("\n" + "=" * 70)

                        if status['status'] == 'completed':
                            print("✅ INGESTION COMPLETED!")

                            # Show category breakdown
                            if status.get('stats', {}).get('categories'):
                                print("\nDocument Categories:")
                                for cat, count in status['stats']['categories'].items():
                                    print(f"  {cat}: {count}")

                            total_time = elapsed
                            print(f"\nTotal time: {int(total_time//60)}m {int(total_time%60)}s")
                            print(f"Average: {total_time/status['processed_files']:.1f}s per file")

                        elif status['status'] == 'failed':
                            print("❌ INGESTION FAILED!")
                            if status.get('errors'):
                                print("\nErrors:")
                                for err in status['errors'][:5]:
                                    print(f"  - {err}")

                        elif status['status'] == 'cancelled':
                            print("⚠️  INGESTION CANCELLED")

                        break

                time.sleep(2)  # Poll every 2 seconds

            except KeyboardInterrupt:
                print("\n\nMonitoring stopped by user.")
                print("Ingestion continues in background.")
                break

    except Exception as e:
        print(f"Error: {e}")

def estimate_stripe_crawl():
    """Estimate how long Stripe documentation crawl will take"""

    print("\n" + "=" * 70)
    print("STRIPE CRAWL TIME ESTIMATES")
    print("=" * 70)

    # Based on the comprehensive profile settings
    estimates = {
        "depth_2_api_only": {
            "pages": 50-100,
            "time": "5-10 minutes",
            "size": "~50MB",
            "description": "API reference only (your original config)"
        },
        "depth_3_docs": {
            "pages": 200-400,
            "time": "15-30 minutes",
            "size": "~200MB",
            "description": "Main documentation sections"
        },
        "depth_5_comprehensive": {
            "pages": 500-1000,
            "time": "30-60 minutes",
            "size": "~500MB",
            "description": "Complete documentation (comprehensive profile)"
        },
        "depth_5_with_guides": {
            "pages": 1000-2000,
            "time": "60-120 minutes",
            "size": "~1GB",
            "description": "Everything including all guides and examples"
        }
    }

    print("\nExpected crawl times for Stripe docs:")
    for config, info in estimates.items():
        print(f"\n{config}:")
        print(f"  Pages: {info['pages']}")
        print(f"  Time: {info['time']}")
        print(f"  Storage: {info['size']}")
        print(f"  Coverage: {info['description']}")

    print("\n⚡ FACTORS AFFECTING SPEED:")
    print("  • Network speed (rate limited to be respectful)")
    print("  • HTML parsing and markdown conversion")
    print("  • Document categorization and smart chunking")
    print("  • Embedding generation (768-dim vectors)")
    print("  • ChromaDB indexing")

    print("\n🔄 SCHEDULING RECOMMENDATIONS:")
    print("  • Initial ingestion: Run manually and monitor")
    print("  • Weekly updates: Schedule for low-traffic hours")
    print("  • Incremental updates: Check for new pages only")
    print("  • Use webhook from Stripe for immediate updates")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "estimate":
        estimate_stripe_crawl()
    else:
        print("Monitoring active ingestion...")
        print("(Press Ctrl+C to stop monitoring)\n")
        monitor_ingestion()