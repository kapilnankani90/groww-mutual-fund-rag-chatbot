"""
scheduler.py - Schedules the daily ingestion pipeline (scraper -> enricher -> embedder)
to run at 10:00 AM IST (04:30 AM UTC).
"""
import sys
import os
import time
import subprocess
import argparse
from datetime import datetime, timedelta, timezone

# Ensure stdout uses UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(backend_dir)

def run_pipeline():
    """Runs the full three-step data ingestion and embedding pipeline."""
    print(f"\n========================================================")
    print(f"[{datetime.now().isoformat()}] Starting Ingestion Pipeline Run...")
    print(f"========================================================\n")
    
    # 1. Scrape
    print("Step 1: Running Scraper...")
    scrape_proc = subprocess.run([sys.executable, "backend/scraper.py"], cwd=base_dir)
    if scrape_proc.returncode != 0:
        print("❌ Scraper failed. Aborting pipeline.")
        return False

    # 2. Enrich
    print("\nStep 2: Running Enricher...")
    enrich_proc = subprocess.run([sys.executable, "backend/enrich_corpus.py"], cwd=base_dir)
    if enrich_proc.returncode != 0:
        print("❌ Enricher failed. Aborting pipeline.")
        return False

    # 3. Embed
    print("\nStep 3: Running Embedder...")
    embed_proc = subprocess.run([sys.executable, "backend/embedder.py"], cwd=base_dir)
    if embed_proc.returncode != 0:
        print("❌ Embedder failed.")
        return False
        
    print(f"\n========================================================")
    print(f"[{datetime.now().isoformat()}] Pipeline Run Completed Successfully!")
    print(f"========================================================\n")
    return True

def get_next_run_time() -> datetime:
    """Calculates the next occurrence of 10:00 AM IST (04:30 UTC) in UTC time."""
    # IST is UTC + 5.5 hours
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_tz)
    
    # Target is today at 10:00 AM IST
    target_ist = now_ist.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # If 10:00 AM IST has already passed today, target tomorrow
    if now_ist >= target_ist:
        target_ist += timedelta(days=1)
        
    return target_ist.astimezone(timezone.utc)

def start_scheduler():
    """Starts the continuous loop scheduler."""
    print("Starting Mutual Fund FAQ Ingestion Pipeline Scheduler...")
    print("Pipeline is scheduled to run daily at 10:00 AM IST (04:30 AM UTC).")
    
    while True:
        next_run = get_next_run_time()
        # Convert next run to local timezone for console print readability
        local_next_run = next_run.astimezone()
        print(f"Next pipeline run scheduled at: {local_next_run.strftime('%Y-%m-%d %I:%M:%S %p %Z')} (UTC: {next_run.strftime('%H:%M:%S')})")
        
        # Calculate seconds to sleep
        now_utc = datetime.now(timezone.utc)
        sleep_seconds = (next_run - now_utc).total_seconds()
        
        # Sleep in smaller increments to allow exit or signals
        while sleep_seconds > 0:
            sleep_chunk = min(sleep_seconds, 60.0)
            time.sleep(sleep_chunk)
            now_utc = datetime.now(timezone.utc)
            sleep_seconds = (next_run - now_utc).total_seconds()
            
        print("\nScheduled run triggered!")
        run_pipeline()

def main():
    parser = argparse.ArgumentParser(description="Mutual Fund FAQ Ingestion Scheduler")
    parser.add_argument("--run-now", action="store_true", help="Run the full pipeline immediately and exit")
    args = parser.parse_args()
    
    if args.run_now:
        success = run_pipeline()
        sys.exit(0 if success else 1)
        
    start_scheduler()

if __name__ == "__main__":
    main()
