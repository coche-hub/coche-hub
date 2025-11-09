import io
import os
import json

import pytest

from app import create_app


@pytest.fixture
def app():
    # create a testing app
    app = create_app(config_name="testing")

    # Ensure FAKENODO_URL points to local blueprint on test server
    # The ModuleManager registers the fakenodo blueprint at /fakenodo
    os.environ["FAKENODO_URL"] = "http://localhost:5000/fakenodo"
    os.environ["FAKENODO_DOI_PREFIX"] = "10.1234/fake"

    # use testing config
    app.config.update({"TESTING": True})

    # Ensure storage path is isolated for tests
    working_dir = os.getenv("WORKING_DIR", "")
    storage_dir = os.path.join(working_dir, "app", "modules", "fakenodo")
    os.makedirs(storage_dir, exist_ok=True)
    storage_file = os.path.join(storage_dir, "storage.json")
    # reset storage
    with open(storage_file, "w") as f:
        json.dump({"next_id": 1, "depositions": {}}, f)

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_create_upload_publish_flow(client, tmp_path):
    # Create deposition
    rv = client.post(
        "/fakenodo/api/deposit/depositions",
        json={"metadata": {"title": "Test deposition"}},
    )
    assert rv.status_code == 201
    dep = rv.get_json()
    dep_id = dep["id"]

    # Upload a file
    file_content = b"hello world"
    data = {
        "file": (io.BytesIO(file_content), "file1.txt"),
        "name": "file1.txt",
    }
    rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/files", data=data, content_type="multipart/form-data")
    assert rv.status_code == 201

    # Publish - first publish should create version 1
    rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/actions/publish")
    assert rv.status_code == 202
    dep = rv.get_json()
    assert dep["published"] is True
    assert dep["version"] == 1
    assert dep["doi"].endswith(".v1")

    # Publishing again without changes should not create a new version
    rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/actions/publish")
    assert rv.status_code == 200
    dep2 = rv.get_json()
    assert dep2["version"] == 1

    # Modify file (upload different file) and publish again -> new version
    file_content2 = b"new content"
    data = {"file": (io.BytesIO(file_content2), "file2.txt"), "name": "file2.txt"}
    rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/files", data=data, content_type="multipart/form-data")
    assert rv.status_code == 201

    rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/actions/publish")
    assert rv.status_code == 202
    dep3 = rv.get_json()
    assert dep3["version"] == 2
    assert dep3["doi"].endswith(".v2")


def test_list_get_doi_and_delete_flow(client):
    # Create deposition
    rv = client.post(
        "/fakenodo/api/deposit/depositions",
        json={"metadata": {"title": "List test deposition"}},
    )
    assert rv.status_code == 201
    dep = rv.get_json()
    dep_id = dep["id"]

    # List all depositions and ensure the new one is present
    rv = client.get("/fakenodo/api/deposit/depositions")
    assert rv.status_code == 200
    deps = rv.get_json()
    assert any(d.get("id") == dep_id for d in deps)

    # Upload and publish so a DOI is generated
    data = {"file": (io.BytesIO(b"content"), "z.txt"), "name": "z.txt"}
    rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/files", data=data, content_type="multipart/form-data")
    assert rv.status_code == 201

    rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/actions/publish")
    assert rv.status_code in (200, 202)

    # Get DOI
    rv = client.get(f"/fakenodo/api/deposit/depositions/{dep_id}/doi")
    assert rv.status_code == 200
    doi = rv.get_json().get("doi")
    assert doi is not None and ".v1" in doi

    # Delete deposition
    rv = client.delete(f"/fakenodo/api/deposit/depositions/{dep_id}")
    assert rv.status_code == 204

    # After deletion, listing should not include it and DOI endpoint returns 404
    rv = client.get("/fakenodo/api/deposit/depositions")
    assert rv.status_code == 200
    deps = rv.get_json()
    assert not any(d.get("id") == dep_id for d in deps)

    rv = client.get(f"/fakenodo/api/deposit/depositions/{dep_id}/doi")
    assert rv.status_code == 404
