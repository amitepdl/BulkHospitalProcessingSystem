from flask import Blueprint, request, jsonify
from app.csv_upload.services import UploadService

csv_bp = Blueprint("csv_upload", __name__)


@csv_bp.route("/hospitals/bulk", methods=["post"])
def upload_csv():
    try:
        uploaded_file = request.files.get("file")
        batch_id = request.form.get("batch_id")
        resp, status_code = UploadService.upload_csv_file(
            uploaded_file=uploaded_file,
            batch_id=batch_id
        )
        return resp, status_code
    except Exception as e:
        return jsonify({
            "status": "Failed",
            "error": "Something went wrong while uploading your file",
        }), 400
