import json
import os
import time
from datetime import datetime
from typing import Dict, Any

from flask import request, jsonify

from app.modules.fakenodo import fakenodo_bp


WORKING_DIR = os.getenv("WORKING_DIR") or os.getcwd()
STORAGE_PATH = os.path.join(WORKING_DIR, "app", "modules", "fakenodo", "storage.json")
DOI_PREFIX = os.getenv("FAKENODO_DOI_PREFIX", "10.1234/fake")


def _ensure_storage():
    folder = os.path.dirname(STORAGE_PATH)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(STORAGE_PATH):
        with open(STORAGE_PATH, "w") as f:
            json.dump({"next_id": 1, "depositions": {}}, f)


def _load_storage() -> Dict[str, Any]:
    _ensure_storage()
    with open(STORAGE_PATH, "r") as f:
        return json.load(f)


def _save_storage(data: Dict[str, Any]):
    _ensure_storage()
    with open(STORAGE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _now_iso():
    return datetime.utcnow().isoformat() + "Z"


def _generate_doi(deposition_id: int, version: int):
    return f"{DOI_PREFIX}.{deposition_id}.v{version}"


@fakenodo_bp.route("/fakenodo/api/deposit/depositions", methods=["POST"])
def create_deposition():
    storage = _load_storage()
    body = request.get_json() or {}
    dep_id = storage["next_id"]

    deposition = {
        "id": dep_id,
        "metadata": body.get("metadata", {}),
        "files": [],
        "published": False,
        "doi": None,
        "version": 0,
        "versions": [],
        "files_modified": False,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "last_published_files_count": 0,
    }

    storage["depositions"][str(dep_id)] = deposition
    storage["next_id"] = dep_id + 1
    _save_storage(storage)

    return jsonify(deposition), 201


@fakenodo_bp.route("/fakenodo/api/deposit/depositions", methods=["GET"])
def list_depositions():
    storage = _load_storage()
    deps = list(storage.get("depositions", {}).values())
    return jsonify(deps), 200


@fakenodo_bp.route("/fakenodo/api/deposit/depositions/<int:deposition_id>", methods=["GET", "PUT"])
def deposition_detail(deposition_id):
    storage = _load_storage()
    dep = storage.get("depositions", {}).get(str(deposition_id))
    if not dep:
        return jsonify({"message": "Not found"}), 404

    if request.method == "GET":
        return jsonify(dep), 200

    # PUT: update metadata
    body = request.get_json() or {}
    if "metadata" in body:
        dep["metadata"] = body["metadata"]
        dep["updated_at"] = _now_iso()
        # metadata-only changes do not mark files as modified
        _save_storage(storage)
        return jsonify(dep), 200

    return jsonify({"message": "No supported changes provided"}), 400


@fakenodo_bp.route("/fakenodo/api/deposit/depositions/<int:deposition_id>/files", methods=["POST"])
def upload_file(deposition_id):
    storage = _load_storage()
    dep = storage.get("depositions", {}).get(str(deposition_id))
    if not dep:
        return jsonify({"message": "Not found"}), 404

    if "file" not in request.files:
        return jsonify({"message": "No file provided"}), 400

    f = request.files["file"]
    name = request.form.get("name") or f.filename

    # save file under module storage folder
    files_folder = os.path.join(os.path.dirname(STORAGE_PATH), "files", str(deposition_id))
    os.makedirs(files_folder, exist_ok=True)
    file_path = os.path.join(files_folder, name)
    f.save(file_path)

    dep_entry = {"name": name, "path": file_path, "uploaded_at": _now_iso()}
    # replace if exists
    existing = next((x for x in dep["files"] if x["name"] == name), None)
    if existing:
        dep["files"].remove(existing)
    dep["files"].append(dep_entry)
    dep["files_modified"] = True
    dep["updated_at"] = _now_iso()
    _save_storage(storage)

    return jsonify(dep_entry), 201


@fakenodo_bp.route("/fakenodo/api/deposit/depositions/<int:deposition_id>/actions/publish", methods=["POST"])
def publish_deposition(deposition_id):
    storage = _load_storage()
    dep = storage.get("depositions", {}).get(str(deposition_id))
    if not dep:
        return jsonify({"message": "Not found"}), 404

    # If never published before -> create version 1
    if not dep["published"]:
        dep["published"] = True
        dep["version"] = 1
        dep["doi"] = _generate_doi(deposition_id, 1)
        dep["versions"].append({"version": 1, "doi": dep["doi"], "published_at": _now_iso()})
        dep["last_published_files_count"] = len(dep["files"])
        dep["files_modified"] = False
        dep["updated_at"] = _now_iso()
        _save_storage(storage)
        return jsonify(dep), 202

    # Already published: if files were modified since last publish -> new version
    if dep.get("files_modified") and len(dep["files"]) > dep.get("last_published_files_count", 0):
        dep["version"] = dep.get("version", 1) + 1
        dep["doi"] = _generate_doi(deposition_id, dep["version"])
        dep["versions"].append({"version": dep["version"], "doi": dep["doi"], "published_at": _now_iso()})
        dep["last_published_files_count"] = len(dep["files"])
        dep["files_modified"] = False
        dep["updated_at"] = _now_iso()
        _save_storage(storage)
        return jsonify(dep), 202

    # No files changed since last publish: publishing again does not create new DOI/version
    dep["updated_at"] = _now_iso()
    _save_storage(storage)
    return jsonify(dep), 200


@fakenodo_bp.route("/fakenodo/api/deposit/depositions/<int:deposition_id>/versions", methods=["GET"])
def list_versions(deposition_id):
    storage = _load_storage()
    dep = storage.get("depositions", {}).get(str(deposition_id))
    if not dep:
        return jsonify({"message": "Not found"}), 404
    return jsonify(dep.get("versions", [])), 200


@fakenodo_bp.route("/fakenodo/api/deposit/depositions/<int:deposition_id>", methods=["DELETE"])
def delete_deposition(deposition_id):
    """Delete a deposition and its files. Returns 204 on success."""
    storage = _load_storage()
    key = str(deposition_id)
    if key not in storage.get("depositions", {}):
        return jsonify({"message": "Not found"}), 404

    # remove files folder if exists
    files_folder = os.path.join(os.path.dirname(STORAGE_PATH), "files", key)
    try:
        if os.path.exists(files_folder):
            # remove files inside then folder
            for fname in os.listdir(files_folder):
                try:
                    os.remove(os.path.join(files_folder, fname))
                except Exception:
                    pass
            try:
                os.rmdir(files_folder)
            except Exception:
                pass
    except Exception:
        pass

    # remove deposition entry
    storage.get("depositions", {}).pop(key, None)
    _save_storage(storage)
    return ("", 204)


@fakenodo_bp.route("/fakenodo/api/deposit/depositions/<int:deposition_id>/doi", methods=["GET"])
def get_deposition_doi(deposition_id):
    """Return the current DOI for a deposition (or null if not published)."""
    storage = _load_storage()
    dep = storage.get("depositions", {}).get(str(deposition_id))
    if not dep:
        return jsonify({"message": "Not found"}), 404
    return jsonify({"doi": dep.get("doi")}), 200
