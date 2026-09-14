from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import reminders
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


def test_get_due_items_includes_overdue_and_soon(session):
    today = date(2026, 9, 14)
    crud.add_application(session, company="Overdue Co", role="Eng", deadline=today - timedelta(days=2))
    crud.add_application(session, company="Soon Co", role="Eng", follow_up_date=today + timedelta(days=2))
    crud.add_application(session, company="Later Co", role="Eng", deadline=today + timedelta(days=10))
    crud.add_application(session, company="No Dates Co", role="Eng")

    items = reminders.get_due_items(session, days_ahead=3, today=today)

    companies = {item["application"].company for item in items}
    assert companies == {"Overdue Co", "Soon Co"}


def test_get_due_items_excludes_closed_statuses(session):
    today = date(2026, 9, 14)
    crud.add_application(session, company="Rejected Co", role="Eng", status="rejected", deadline=today)
    crud.add_application(session, company="Withdrawn Co", role="Eng", status="withdrawn", follow_up_date=today)

    items = reminders.get_due_items(session, days_ahead=3, today=today)

    assert items == []


def test_get_due_items_sorted_by_urgency(session):
    today = date(2026, 9, 14)
    crud.add_application(session, company="A", role="Eng", deadline=today + timedelta(days=2))
    crud.add_application(session, company="B", role="Eng", deadline=today - timedelta(days=1))

    items = reminders.get_due_items(session, days_ahead=3, today=today)

    assert [item["application"].company for item in items] == ["B", "A"]


def test_format_email_body_returns_none_when_no_items():
    assert reminders.format_email_body([]) is None


def test_format_email_body_describes_overdue_items(session):
    today = date(2026, 9, 14)
    crud.add_application(session, company="Acme", role="Eng", deadline=today - timedelta(days=1))

    items = reminders.get_due_items(session, days_ahead=3, today=today)
    body = reminders.format_email_body(items)

    assert "Acme" in body
    assert "1 day overdue" in body


def test_run_skips_send_when_nothing_due(session):
    with patch.object(reminders, "send_email") as mock_send:
        sent = reminders.run(session=session)

    assert sent is False
    mock_send.assert_not_called()


def test_run_sends_email_when_items_due(session, monkeypatch):
    crud.add_application(session, company="Acme", role="Eng", deadline=date.today())
    monkeypatch.setenv("REMINDER_EMAIL_ADDRESS", "me@example.com")
    monkeypatch.setenv("REMINDER_EMAIL_APP_PASSWORD", "secret")
    monkeypatch.delenv("REMINDER_TO_EMAIL", raising=False)

    with patch.object(reminders, "send_email") as mock_send:
        sent = reminders.run(session=session)

    assert sent is True
    mock_send.assert_called_once()
    _, kwargs = mock_send.call_args
    assert kwargs["from_addr"] == "me@example.com"
    assert kwargs["to_addr"] == "me@example.com"
    assert "Acme" in kwargs["body"]


def test_run_raises_clear_error_when_credentials_missing(session, monkeypatch):
    crud.add_application(session, company="Acme", role="Eng", deadline=date.today())
    monkeypatch.delenv("REMINDER_EMAIL_ADDRESS", raising=False)
    monkeypatch.delenv("REMINDER_EMAIL_APP_PASSWORD", raising=False)

    with pytest.raises(SystemExit):
        reminders.run(session=session)
