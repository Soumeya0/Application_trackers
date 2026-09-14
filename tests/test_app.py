import os
import re
import tempfile

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

import pytest  # noqa: E402

from app import create_app  # noqa: E402


def teardown_module(module):
    try:
        os.remove(_db_path)
    except FileNotFoundError:
        pass


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def extract_application_id(html_bytes, company):
    html = html_bytes.decode("utf-8")
    for row in re.findall(r'<tr class="[^"]*">.*?</tr>', html, re.DOTALL):
        if company in row:
            id_match = re.search(r"/applications/(\d+)/edit", row)
            assert id_match is not None
            return int(id_match.group(1))
    raise AssertionError(f"no table row found for {company!r}")


def test_index_shows_empty_state(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"No applications" in response.data


def test_add_application_via_form(client):
    response = client.post(
        "/applications/new",
        data={"company": "Acme", "role": "Backend Engineer", "status": "applied"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Acme" in response.data
    assert b"Backend Engineer" in response.data


def test_add_application_requires_company_and_role(client):
    response = client.post(
        "/applications/new",
        data={"company": "", "role": "", "status": "applied"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"required" in response.data.lower()


def test_edit_application_updates_status(client):
    client.post(
        "/applications/new",
        data={"company": "Globex", "role": "Data Engineer", "status": "applied"},
    )
    response = client.get("/")
    application_id = extract_application_id(response.data, "Globex")

    edit_response = client.post(
        f"/applications/{application_id}/edit",
        data={"company": "Globex", "role": "Data Engineer", "status": "interviewing"},
        follow_redirects=True,
    )
    assert edit_response.status_code == 200
    assert b"interviewing" in edit_response.data


def test_status_filter_narrows_results(client):
    client.post(
        "/applications/new",
        data={"company": "Umbrella Corp", "role": "SRE", "status": "rejected"},
    )
    response = client.get("/?status=rejected")
    assert b"Umbrella Corp" in response.data
    assert b"Acme" not in response.data


def test_delete_application_removes_it(client):
    client.post(
        "/applications/new",
        data={"company": "Initech", "role": "QA Engineer", "status": "applied"},
    )
    response = client.get("/")
    application_id = extract_application_id(response.data, "Initech")

    delete_response = client.post(f"/applications/{application_id}/delete", follow_redirects=True)
    assert delete_response.status_code == 200
    assert b"Initech" not in delete_response.data
