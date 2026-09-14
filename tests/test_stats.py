from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src import crud
from src.database import Base
from src.stats import compute_stats


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db_session = TestingSessionLocal()
    yield db_session
    db_session.close()


def test_compute_stats_on_empty_tracker(session):
    result = compute_stats(session)

    assert result["total"] == 0
    assert result["response_rate"] is None
    assert result["avg_days_to_response"] is None
    assert all(count == 0 for count in result["by_status"].values())


def test_compute_stats_counts_by_status(session):
    crud.add_application(session, company="Acme", role="Eng", status="applied")
    crud.add_application(session, company="Globex", role="Eng", status="interviewing")
    crud.add_application(session, company="Initech", role="Eng", status="interviewing")

    result = compute_stats(session)

    assert result["total"] == 3
    assert result["by_status"]["applied"] == 1
    assert result["by_status"]["interviewing"] == 2
    assert result["by_status"]["offer"] == 0


def test_compute_stats_response_rate(session):
    crud.add_application(session, company="Acme", role="Eng", status="applied")
    crud.add_application(session, company="Globex", role="Eng", status="interviewing")
    crud.add_application(session, company="Initech", role="Eng", status="rejected")
    crud.add_application(session, company="Umbrella", role="Eng", status="applied")

    result = compute_stats(session)

    assert result["response_rate"] == 50.0


def test_compute_stats_avg_days_to_response(session):
    applied_date = date(2026, 1, 1)
    acme = crud.add_application(session, company="Acme", role="Eng", date_applied=applied_date)
    globex = crud.add_application(session, company="Globex", role="Eng", date_applied=applied_date)
    crud.add_application(session, company="Initech", role="Eng", date_applied=applied_date)  # still "applied"

    crud.update_application(session, acme.id, status="interviewing", responded_at=applied_date + timedelta(days=2))
    crud.update_application(session, globex.id, status="rejected", responded_at=applied_date + timedelta(days=8))

    result = compute_stats(session)

    assert result["avg_days_to_response"] == 5.0
