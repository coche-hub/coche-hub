import io
import os

from app import create_app


def setup_module(module):
    # ensure working dir is project root for predictable storage path
    os.environ.setdefault("WORKING_DIR", os.getcwd())


def teardown_module(module):
    # clean storage after tests
    storage = os.path.join(os.environ.get("WORKING_DIR", os.getcwd()), "app", "modules", "fakenodo", "storage.json")
    try:
        if os.path.exists(storage):
            os.remove(storage)
    except Exception:
        pass


def test_versions_endpoint_creates_and_lists_versions():
    app = create_app()

    # Register fakenodo blueprint explicitly to ensure endpoints present in tests
    try:
        from app.modules.fakenodo import fakenodo_bp

        app.register_blueprint(fakenodo_bp)
    except Exception:
        # If blueprint already registered, ignore
        pass

    app.config.update({"TESTING": True})

    storage_path = os.path.join(
        os.environ.get("WORKING_DIR", os.getcwd()), "app", "modules", "fakenodo", "storage.json"
    )
    # ensure clean state
    if os.path.exists(storage_path):
        os.remove(storage_path)

    with app.test_client() as client:
        # create deposition
        rv = client.post(
            "/fakenodo/api/deposit/depositions",
            json={"metadata": {"title": "Test deposition"}},
        )
        assert rv.status_code == 201
        dep = rv.get_json()
        dep_id = dep["id"]

        # upload a file
        data = {"file": (io.BytesIO(b"hello"), "a.txt"), "name": "a.txt"}
        rv = client.post(
            f"/fakenodo/api/deposit/depositions/{dep_id}/files", data=data, content_type="multipart/form-data"
        )
        assert rv.status_code == 201

        # publish -> creates version 1
        rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/actions/publish")
        assert rv.status_code == 202
        published = rv.get_json()
        assert published["version"] == 1

        # list versions -> should return one entry with version 1
        rv = client.get(f"/fakenodo/api/deposit/depositions/{dep_id}/versions")
        assert rv.status_code == 200
        versions = rv.get_json()
        assert isinstance(versions, list)
        assert len(versions) == 1
        assert versions[0]["version"] == 1

        # upload another file and publish -> creates version 2
        data = {"file": (io.BytesIO(b"world"), "b.txt"), "name": "b.txt"}
        rv = client.post(
            f"/fakenodo/api/deposit/depositions/{dep_id}/files", data=data, content_type="multipart/form-data"
        )
        assert rv.status_code == 201

        rv = client.post(f"/fakenodo/api/deposit/depositions/{dep_id}/actions/publish")
        assert rv.status_code == 202
        published2 = rv.get_json()
        assert published2["version"] == 2

        # list versions -> should return two entries
        rv = client.get(f"/fakenodo/api/deposit/depositions/{dep_id}/versions")
        assert rv.status_code == 200
        versions = rv.get_json()
        assert len(versions) == 2
        assert versions[-1]["version"] == 2
