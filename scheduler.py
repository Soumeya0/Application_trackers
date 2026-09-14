"""Runs the reminder check once a day, for local/background use.

    python scheduler.py

Keep this process running (e.g. in a terminal, tmux, or a background service).
Set REMINDER_TIME ("HH:MM", 24h, default "08:00") to change when it fires.

If you're deployed on Railway, a Cron Job that runs `python reminders.py`
directly on a schedule is simpler than keeping this process alive — use this
script only where nothing else can trigger it on a timer.
"""

import os
import time

import schedule

import reminders

REMINDER_TIME = os.environ.get("REMINDER_TIME", "08:00")


def job():
    reminders.init_db()
    reminders.run()


schedule.every().day.at(REMINDER_TIME).do(job)

if __name__ == "__main__":
    print(f"Reminder scheduler running — checking daily at {REMINDER_TIME}. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)
