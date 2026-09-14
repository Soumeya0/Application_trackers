from datetime import datetime

from src import crud
from src.database import SessionLocal, init_db

STATUS_CHOICES = ["applied", "interviewing", "offer", "rejected", "withdrawn"]

MENU = """
== Application Tracker ==
1) Add application
2) List applications
3) Update status
4) Delete application
5) Exit
"""


def prompt_date(label):
    raw = input(f"{label} (YYYY-MM-DD, blank to skip): ").strip()
    if not raw:
        return None
    return datetime.strptime(raw, "%Y-%m-%d").date()


def add_application_flow(session):
    company = input("Company: ").strip()
    role = input("Role: ").strip()
    date_applied = prompt_date("Date applied")
    deadline = prompt_date("Deadline")
    follow_up_date = prompt_date("Follow-up date")
    job_link = input("Job link (blank to skip): ").strip() or None
    tech_tags = input("Tech tags, comma-separated (blank to skip): ").strip() or None
    notes = input("Notes (blank to skip): ").strip() or None

    application = crud.add_application(
        session,
        company=company,
        role=role,
        date_applied=date_applied,
        deadline=deadline,
        follow_up_date=follow_up_date,
        job_link=job_link,
        tech_tags=tech_tags,
        notes=notes,
    )
    print(f"Added application #{application.id}: {application.company} - {application.role}")


def list_applications_flow(session):
    status_filter = input("Filter by status (blank for all): ").strip() or None
    applications = crud.list_applications(session, status=status_filter)
    if not applications:
        print("No applications found.")
        return
    for application in applications:
        print(
            f"[{application.id}] {application.company} - {application.role} "
            f"| status={application.status} | applied={application.date_applied} "
            f"| deadline={application.deadline} | follow_up={application.follow_up_date}"
        )


def update_status_flow(session):
    application_id = int(input("Application ID: ").strip())
    print(f"Status choices: {', '.join(STATUS_CHOICES)}")
    new_status = input("New status: ").strip()
    application = crud.update_status(session, application_id, new_status)
    if application is None:
        print("Application not found.")
    else:
        print(f"Updated #{application.id} to status '{application.status}'.")


def delete_application_flow(session):
    application_id = int(input("Application ID: ").strip())
    deleted = crud.delete_application(session, application_id)
    print("Deleted." if deleted else "Application not found.")


def main():
    init_db()
    session = SessionLocal()
    actions = {
        "1": add_application_flow,
        "2": list_applications_flow,
        "3": update_status_flow,
        "4": delete_application_flow,
    }
    try:
        while True:
            print(MENU)
            choice = input("Choose an option: ").strip()
            if choice == "5":
                break
            action = actions.get(choice)
            if action is None:
                print("Invalid choice.")
                continue
            action(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
