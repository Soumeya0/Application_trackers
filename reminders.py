"""Daily digest email for upcoming/overdue deadlines and follow-ups.

Required environment variables:
    REMINDER_EMAIL_ADDRESS       Gmail address to send from.
    REMINDER_EMAIL_APP_PASSWORD  Gmail app password (not your account password) —
                                  create one at https://myaccount.google.com/apppasswords.

Optional environment variables:
    REMINDER_TO_EMAIL       Recipient address (defaults to REMINDER_EMAIL_ADDRESS).
    REMINDER_DAYS_AHEAD     How many days ahead counts as "soon" (default 3).
    SMTP_HOST               Default smtp.gmail.com.
    SMTP_PORT               Default 465 (SSL).

Run directly for a one-off check: `python reminders.py`
Run on a schedule with `python scheduler.py`, or via a Railway/cron job.
"""

import os
import smtplib
from datetime import date
from email.mime.text import MIMEText

from src import crud
from src.database import SessionLocal, init_db

CLOSED_STATUSES = {"rejected", "withdrawn"}
DEFAULT_DAYS_AHEAD = 3


def get_due_items(session, days_ahead=DEFAULT_DAYS_AHEAD, today=None):
    today = today or date.today()
    items = []
    for application in crud.list_applications(session):
        if application.status in CLOSED_STATUSES:
            continue
        for field, label in (("deadline", "Deadline"), ("follow_up_date", "Follow-up")):
            due_date = getattr(application, field)
            if due_date is None:
                continue
            days = (due_date - today).days
            if days <= days_ahead:
                items.append(
                    {"application": application, "label": label, "due_date": due_date, "days": days}
                )
    items.sort(key=lambda item: item["days"])
    return items


def format_email_body(items):
    if not items:
        return None
    lines = ["Here's what needs attention in your application tracker:", ""]
    for item in items:
        application = item["application"]
        days = item["days"]
        if days < 0:
            when = f"{abs(days)} day{'s' if abs(days) != 1 else ''} overdue"
        elif days == 0:
            when = "due today"
        else:
            when = f"in {days} day{'s' if days != 1 else ''}"
        lines.append(
            f"- {application.company} ({application.role}) — {item['label']} "
            f"{item['due_date'].isoformat()}, {when} [{application.status}]"
        )
    return "\n".join(lines)


def send_email(subject, body, *, to_addr, from_addr, app_password, host="smtp.gmail.com", port=465):
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = to_addr

    with smtplib.SMTP_SSL(host, port) as server:
        server.login(from_addr, app_password)
        server.sendmail(from_addr, [to_addr], message.as_string())


def _required_env(name):
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def run(session=None, days_ahead=None):
    own_session = session is None
    session = session or SessionLocal()
    try:
        if days_ahead is None:
            days_ahead = int(os.environ.get("REMINDER_DAYS_AHEAD", DEFAULT_DAYS_AHEAD))

        items = get_due_items(session, days_ahead=days_ahead)
        body = format_email_body(items)
        if body is None:
            print("No upcoming deadlines or follow-ups. Nothing to send.")
            return False

        from_addr = _required_env("REMINDER_EMAIL_ADDRESS")
        app_password = _required_env("REMINDER_EMAIL_APP_PASSWORD")
        to_addr = os.environ.get("REMINDER_TO_EMAIL", from_addr)
        host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        port = int(os.environ.get("SMTP_PORT", 465))

        send_email(
            subject=f"Application Tracker: {len(items)} item(s) need attention",
            body=body,
            to_addr=to_addr,
            from_addr=from_addr,
            app_password=app_password,
            host=host,
            port=port,
        )
        print(f"Sent reminder email with {len(items)} item(s) to {to_addr}.")
        return True
    finally:
        if own_session:
            session.close()


def main():
    init_db()
    run()


if __name__ == "__main__":
    main()
