#!/usr/bin/env python
"""
Schedule regular ingestion updates for documentation
Can be run as a service or scheduled task
"""

import schedule
import time
import requests
import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys

class IngestionScheduler:
    """Manages scheduled ingestion tasks"""

    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.log_file = Path("ingestion_schedule.log")

    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        # Also write to file
        with open(self.log_file, 'a') as f:
            f.write(log_message + "\n")

    def check_for_updates(self, profile):
        """Check if documentation has updates (simplified check)"""
        # In production, you'd check:
        # - Last-Modified headers
        # - Sitemap changes
        # - RSS/changelog feeds
        # - Git commits for local files

        self.log(f"Checking for updates in {profile}...")

        # For now, return True to always update
        # In production, implement smart change detection
        return True

    def run_ingestion(self, profile, force=False):
        """Run ingestion for a profile"""

        # Check if already running
        try:
            response = requests.get(f"{self.base_url}/ingestion/active")
            active = response.json().get("active_task")

            if active:
                self.log(f"Ingestion already running for {active['profile_name']}, skipping...")
                return False
        except:
            self.log("Cannot connect to backend, skipping...")
            return False

        # Check for updates unless forced
        if not force:
            if not self.check_for_updates(profile):
                self.log(f"No updates detected for {profile}, skipping...")
                return False

        # Start ingestion
        self.log(f"Starting ingestion for {profile}...")

        try:
            response = requests.post(f"{self.base_url}/ingestion/start/{profile}")

            if response.status_code == 200:
                task_id = response.json()["task_id"]
                self.log(f"Ingestion started with task ID: {task_id}")

                # Wait for completion (with timeout)
                return self.wait_for_completion(task_id, timeout_minutes=120)
            else:
                self.log(f"Failed to start ingestion: {response.status_code}")
                return False

        except Exception as e:
            self.log(f"Error starting ingestion: {e}")
            return False

    def wait_for_completion(self, task_id, timeout_minutes=120):
        """Wait for ingestion to complete"""

        start_time = datetime.now()
        timeout_seconds = timeout_minutes * 60

        while True:
            elapsed = (datetime.now() - start_time).total_seconds()

            if elapsed > timeout_seconds:
                self.log(f"Timeout waiting for task {task_id}")
                return False

            try:
                response = requests.get(f"{self.base_url}/ingestion/status/{task_id}")
                status = response.json()

                if status['status'] == 'completed':
                    self.log(f"Ingestion completed successfully!")
                    self.log(f"  Processed: {status['processed_files']} files")
                    self.log(f"  Indexed: {status['indexed_chunks']} chunks")
                    return True

                elif status['status'] == 'failed':
                    self.log(f"Ingestion failed!")
                    if status.get('errors'):
                        self.log(f"  Errors: {status['errors'][:3]}")
                    return False

                elif status['status'] == 'cancelled':
                    self.log(f"Ingestion was cancelled")
                    return False

                # Still running, wait
                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.log(f"Error checking status: {e}")
                time.sleep(30)

    def incremental_update(self, profile):
        """Perform incremental update (future feature)"""
        self.log(f"Performing incremental update for {profile}")

        # TODO: Implement incremental updates:
        # 1. Track last ingestion timestamp
        # 2. Only fetch pages modified since then
        # 3. Update specific chunks rather than full re-index

        # For now, do full update
        return self.run_ingestion(profile, force=False)

    def schedule_profiles(self, profiles_config):
        """Schedule multiple profiles with different frequencies"""

        for profile, config in profiles_config.items():
            frequency = config.get("frequency", "weekly")
            time_of_day = config.get("time", "03:00")
            incremental = config.get("incremental", False)

            if frequency == "daily":
                schedule.every().day.at(time_of_day).do(
                    self.incremental_update if incremental else self.run_ingestion,
                    profile
                )
                self.log(f"Scheduled {profile}: Daily at {time_of_day}")

            elif frequency == "weekly":
                day = config.get("day", "sunday")
                getattr(schedule.every(), day).at(time_of_day).do(
                    self.incremental_update if incremental else self.run_ingestion,
                    profile
                )
                self.log(f"Scheduled {profile}: Weekly on {day} at {time_of_day}")

            elif frequency == "hourly":
                schedule.every().hour.do(
                    self.incremental_update if incremental else self.run_ingestion,
                    profile
                )
                self.log(f"Scheduled {profile}: Every hour")

    def run_scheduler(self):
        """Run the scheduler loop"""
        self.log("Scheduler started. Press Ctrl+C to stop.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.log("Scheduler stopped by user")

def create_default_schedule():
    """Create default scheduling configuration"""

    config = {
        "stripe": {
            "frequency": "weekly",
            "day": "sunday",
            "time": "03:00",
            "incremental": False,
            "description": "Full weekly update of Stripe documentation"
        },
        "stripe_incremental": {
            "frequency": "daily",
            "time": "06:00",
            "incremental": True,
            "description": "Daily incremental updates (when implemented)"
        },
        "mcpc": {
            "frequency": "daily",
            "time": "02:00",
            "incremental": False,
            "description": "Daily MCP documentation update"
        }
    }

    # Save config
    with open("schedule_config.json", 'w') as f:
        json.dump(config, f, indent=2)

    return config

def run_once(profile):
    """Run ingestion once for a profile"""
    scheduler = IngestionScheduler()
    success = scheduler.run_ingestion(profile, force=True)
    return success

def main():
    """Main entry point"""

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "run" and len(sys.argv) > 2:
            # Run once for specific profile
            profile = sys.argv[2]
            print(f"Running ingestion for {profile}...")
            success = run_once(profile)
            sys.exit(0 if success else 1)

        elif command == "schedule":
            # Run scheduler
            scheduler = IngestionScheduler()

            # Load or create config
            config_file = Path("schedule_config.json")
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)
            else:
                print("Creating default schedule configuration...")
                config = create_default_schedule()

            # Filter to enabled profiles only
            enabled = {k: v for k, v in config.items() if v.get("enabled", True)}

            scheduler.schedule_profiles(enabled)
            scheduler.run_scheduler()

        elif command == "config":
            # Create/show configuration
            config = create_default_schedule()
            print("Schedule configuration saved to schedule_config.json")
            print("\nConfiguration:")
            print(json.dumps(config, indent=2))

        else:
            print("Usage:")
            print("  python schedule_ingestion.py run <profile>  # Run once")
            print("  python schedule_ingestion.py schedule       # Run scheduler")
            print("  python schedule_ingestion.py config         # Create config")
    else:
        print("Usage:")
        print("  python schedule_ingestion.py run <profile>  # Run once")
        print("  python schedule_ingestion.py schedule       # Run scheduler")
        print("  python schedule_ingestion.py config         # Create config")

if __name__ == "__main__":
    main()