"""
Entry-point: starts APScheduler to run discovery hourly.

Usage:
    python main.py          # runs forever (Ctrl-C to stop)
    python main.py --once   # run discovery once (for cron/manual)
"""

import argparse
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from poll_discovery import discover

def job():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] running discover()")
    discover()

def run_scheduler():
    sched = BlockingScheduler(timezone="America/Recife")
    sched.add_job(job, IntervalTrigger(hours=1))
    print("Scheduler started – discovery will run every hour.")
    sched.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="run discovery once and exit")
    args = parser.parse_args()

    if args.once:
        job()
    else:
        run_scheduler()