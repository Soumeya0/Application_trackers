from datetime import date

from .models import Application


def add_application(
    session,
    company,
    role,
    date_applied=None,
    status="applied",
    deadline=None,
    follow_up_date=None,
    notes=None,
    job_link=None,
    tech_tags=None,
):
    application = Application(
        company=company,
        role=role,
        date_applied=date_applied or date.today(),
        status=status,
        deadline=deadline,
        follow_up_date=follow_up_date,
        notes=notes,
        job_link=job_link,
        tech_tags=tech_tags,
    )
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def get_application(session, application_id):
    return session.get(Application, application_id)


def list_applications(session, status=None):
    query = session.query(Application)
    if status is not None:
        query = query.filter(Application.status == status)
    return query.order_by(Application.date_applied.desc()).all()


def update_status(session, application_id, new_status):
    application = session.get(Application, application_id)
    if application is None:
        return None
    application.status = new_status
    session.commit()
    session.refresh(application)
    return application


def delete_application(session, application_id):
    application = session.get(Application, application_id)
    if application is None:
        return False
    session.delete(application)
    session.commit()
    return True
