from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src import crud
from src.database import Base


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db_session = TestingSessionLocal()
    yield db_session
    db_session.close()


def test_add_application_sets_defaults(session):
    application = crud.add_application(session, company="Acme", role="Backend Engineer")

    assert application.id is not None
    assert application.status == "applied"
    assert application.date_applied == date.today()


def test_add_application_with_explicit_fields(session):
    application = crud.add_application(
        session,
        company="Globex",
        role="Data Engineer",
        status="interviewing",
        deadline=date(2026, 1, 15),
        tech_tags="python,sql",
    )

    assert application.status == "interviewing"
    assert application.deadline == date(2026, 1, 15)
    assert application.tech_tags == "python,sql"


def test_list_applications_returns_all(session):
    crud.add_application(session, company="Acme", role="Backend Engineer")
    crud.add_application(session, company="Globex", role="Data Engineer")

    applications = crud.list_applications(session)

    assert len(applications) == 2


def test_list_applications_filters_by_status(session):
    crud.add_application(session, company="Acme", role="Backend Engineer", status="applied")
    crud.add_application(session, company="Globex", role="Data Engineer", status="interviewing")

    applications = crud.list_applications(session, status="interviewing")

    assert len(applications) == 1
    assert applications[0].company == "Globex"


def test_update_status_changes_existing_application(session):
    application = crud.add_application(session, company="Acme", role="Backend Engineer")

    updated = crud.update_status(session, application.id, "offer")

    assert updated.status == "offer"
    assert crud.get_application(session, application.id).status == "offer"


def test_update_status_returns_none_for_missing_application(session):
    assert crud.update_status(session, 999, "offer") is None


def test_update_status_sets_responded_at_on_first_response(session):
    application = crud.add_application(session, company="Acme", role="Backend Engineer")
    assert application.responded_at is None

    updated = crud.update_status(session, application.id, "interviewing")

    assert updated.responded_at == date.today()


def test_update_status_does_not_overwrite_responded_at(session):
    application = crud.add_application(session, company="Acme", role="Backend Engineer")
    crud.update_status(session, application.id, "interviewing")
    first_responded_at = crud.get_application(session, application.id).responded_at

    updated = crud.update_status(session, application.id, "offer")

    assert updated.responded_at == first_responded_at


def test_update_application_sets_responded_at_on_status_change(session):
    application = crud.add_application(session, company="Acme", role="Backend Engineer")

    updated = crud.update_application(session, application.id, status="rejected")

    assert updated.responded_at == date.today()


def test_update_application_leaves_responded_at_alone_without_status_change(session):
    application = crud.add_application(session, company="Acme", role="Backend Engineer")

    updated = crud.update_application(session, application.id, notes="called recruiter")

    assert updated.responded_at is None


def test_delete_application_removes_existing_application(session):
    application = crud.add_application(session, company="Acme", role="Backend Engineer")

    deleted = crud.delete_application(session, application.id)

    assert deleted is True
    assert crud.list_applications(session) == []


def test_delete_application_returns_false_for_missing_application(session):
    assert crud.delete_application(session, 999) is False
