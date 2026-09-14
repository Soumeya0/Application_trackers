from statistics import mean

from .models import Application

STATUS_ORDER = ["applied", "interviewing", "offer", "rejected", "withdrawn"]


def compute_stats(session):
    applications = session.query(Application).all()
    total = len(applications)

    by_status = {status: 0 for status in STATUS_ORDER}
    for application in applications:
        by_status[application.status] = by_status.get(application.status, 0) + 1

    responded_count = sum(1 for application in applications if application.status != "applied")
    response_rate = round(responded_count / total * 100, 1) if total else None

    response_times = [
        (application.responded_at - application.date_applied).days
        for application in applications
        if application.responded_at is not None
    ]
    avg_days_to_response = round(mean(response_times), 1) if response_times else None

    return {
        "total": total,
        "by_status": by_status,
        "response_rate": response_rate,
        "avg_days_to_response": avg_days_to_response,
    }
