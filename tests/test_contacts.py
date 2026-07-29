import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


module_path = Path(__file__).resolve().parents[1] / "my-first-api" / "main.py"
spec = importlib.util.spec_from_file_location("contacts_api", module_path)
contacts_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contacts_api)


@pytest.fixture(autouse=True)
def reset_contacts():
    contacts_api.contacts.clear()
    contacts_api.contacts.extend([
        {"id": 1, "name": "Juan", "tlf": "123456789"},
        {"id": 2, "name": "María", "tlf": "987654321"},
    ])
    yield


@pytest.fixture()
def client():
    return TestClient(contacts_api.app)


def test_create_contact_generates_id(client):
    response = client.post("/contacts", json={"name": "Ana", "tlf": "111222333"})

    assert response.status_code == 201
    assert response.json()["id"] == 3
    assert response.json()["name"] == "Ana"
    assert response.json()["tlf"] == "111222333"


def test_put_rejects_id_change(client):
    response = client.put(
        "/contacts/1",
        json={"id": 999, "name": "Juan", "tlf": "123456789"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "id no permitido"


def test_patch_rejects_id_change(client):
    response = client.patch(
        "/contacts/1",
        json={"id": 999, "tlf": "555666777"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "id no permitido"


def test_docs_and_openapi_endpoints_are_available(client):
    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "API de Contactos"
