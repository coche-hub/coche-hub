import os
import uuid
from datetime import datetime, timezone
from venv import logger

from flask import current_app, jsonify, make_response, request, send_from_directory
from flask_login import current_user

from app.modules.hubfile import hubfile_bp
from app.modules.hubfile.models import HubfileDownloadRecord
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService


@hubfile_bp.route("/file/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    # Get dataset directly from file
    dataset = file.dataset

    directory_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path)

    # Get the cookie from the request or generate a new one if it does not exist
    user_cookie = request.cookies.get("file_download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    # Check if the download record already exists for this cookie
    existing_record = HubfileDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None, file_id=file_id, download_cookie=user_cookie
    ).first()

    if not existing_record:
        # Record the download in your database
        HubfileDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=file_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    # Save the cookie to the user's browser
    resp = make_response(send_from_directory(directory=file_path, path=filename, as_attachment=True))
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@hubfile_bp.route("/file/view/<int:file_id>", methods=["GET"])
def view_file(file_id):
    try:
        file = HubfileService().get_or_404(file_id)

        # Get dataset directly from file
        dataset = file.dataset  # Usa la relación backref definida en models.py

        # Construct file path
        directory_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"
        file_path = os.path.join(directory_path, file.name)

        if not os.path.exists(file_path):
            return jsonify({"message": f"File not found at {file_path}"}), 404

        # Read CSV file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Return as plain text with proper content type
            response = make_response(content)
            response.headers["Content-Type"] = "text/plain; charset=utf-8"
            return response

        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()

                response = make_response(content)
                response.headers["Content-Type"] = "text/plain; charset=latin-1"
                return response
            except Exception as e:
                logger.exception(f"Error reading file with alternative encoding: {e}")
                return jsonify({"message": "Error reading file - encoding issue"}), 500

    except Exception as e:
        logger.exception(f"Error viewing file {file_id}: {e}")
        return jsonify({"message": f"Error viewing file: {str(e)}"}), 500
