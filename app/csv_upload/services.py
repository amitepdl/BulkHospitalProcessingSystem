import time
import uuid
import logging
from flask import jsonify

from app.csv_upload.csv_validation_service import CSVValidationService
from app.csv_upload.hospital_api_helper import HospitalApiHelper
from app.csv_upload.persistent_data_service import PersistentDataService, AsyncHandlerService

logger = logging.getLogger(__name__)

"""
Service Description:
upload_csv_file function flow:

Step 1: Validates the csv file

STep 2: Using the PersistentDataService, 
we'll check if that hospital record, with this particular batch id has been processed or not.
If yes, swap the existing data details with the details present in the storage

Step 3:
Iterate through the validated hospitals, 
if the hospital data is valid and if it has not been processed yet, 
after that call the create hospital API,
at each step track how many hospitals has been created,

Step 4:
If freshly created hospitals are more than 0, call the activate batch API

Step 5:
Prepare the API response, and set corresponding status etc

Step 6:
Call the sync_batch_and_hospitals to give the support of Resume Capability      

"""


class UploadService:

    @staticmethod
    def upload_csv_file(*, uploaded_file, batch_id=None):
        processing_start_time = time.time()
        validation_status, validated_resp = CSVValidationService.validate_hospital_csv(
            uploaded_file=uploaded_file
        )
        if not validation_status:
            return jsonify({
                "status": "failed",
                "error": validated_resp
            }), 400

        validated_hospitals = validated_resp

        batch_id = str(uuid.uuid4()) if not batch_id else batch_id
        data_service = PersistentDataService()
        # print(f"{data_service.shared_batch_info}")
        # print(f"{data_service.shared_hospital_info}")
        # print(validated_hospitals)
        data_service.update_processed_hospitals(batch_id=batch_id, validated_hospitals=validated_hospitals)
        # print(validated_hospitals)

        processed_hospitals_ct = 0
        failed_hospitals_ct = 0
        already_processed_hospitals_ct = 0

        for hospital_data in validated_hospitals:
            is_valid = hospital_data["is_valid"]
            if not is_valid:
                failed_hospitals_ct += 1
                continue

            if hospital_data.get("is_processed", False):
                already_processed_hospitals_ct += 1
                continue

            hospital_data["creation_batch_id"] = batch_id
            status, resp = HospitalApiHelper.create_hospital(data=hospital_data)
            if status:
                processed_hospitals_ct += 1
                hospital_data["is_processed"] = True
                hospital_data["hospital_id"] = resp["id"]
                hospital_data["created_at"] = resp["created_at"]
            else:
                failed_hospitals_ct += 1
                error = hospital_data.get("error", [])
                error.append(resp)

        batch_activated, batch_activation_resp = False, None
        if processed_hospitals_ct > 0:
            batch_activated, batch_activation_resp = HospitalApiHelper.activate_batch(batch_id=batch_id)
            if batch_activated:
                print(f"Batch activated successfully")

        if not batch_activated and failed_hospitals_ct == 0 and already_processed_hospitals_ct > 0:
            batch_activated = True

        processing_end_time = time.time()
        processing_time = int(processing_end_time - processing_start_time)
        final_resp = UploadService.prepare_response(
            batch_id=batch_id,
            hospitals=validated_hospitals,
            processed_hospitals_ct=processed_hospitals_ct,
            failed_hospitals_ct=failed_hospitals_ct,
            already_processed_hospitals_ct=already_processed_hospitals_ct,
            processing_time_seconds=processing_time,
            batch_activation=batch_activated
        )

        return jsonify(final_resp), 200

    @staticmethod
    def prepare_response(
            *,
            batch_id,
            hospitals,
            processed_hospitals_ct,
            failed_hospitals_ct,
            already_processed_hospitals_ct,
            processing_time_seconds,
            batch_activation
    ):
        hospital_list = []
        for h in hospitals:
            h["status"] = "failed_to_create"
            if h["is_valid"]:
                h["status"] = "created_but_inactive"
                if (not h.get("error") and batch_activation) or h.get("is_processed"):
                    h["is_active"] = True
                    h["status"] = "created_and_activated"

            t = {
                "row": h["row"],
                "hospital_id": h.get("hospital_id"),
                "name": h["name"],
                "status": h["status"]
            }
            hospital_list.append(t)

        resp = {
            "batch_id": batch_id,
            "total_hospitals": processed_hospitals_ct + failed_hospitals_ct,
            "processed_hospitals": processed_hospitals_ct,
            "failed_hospitals": failed_hospitals_ct,
            "previously_processed_hospitals": already_processed_hospitals_ct,
            "processing_time_seconds": processing_time_seconds,
            "batch_activated": batch_activation,
            "hospitals": hospital_list,
        }

        AsyncHandlerService.sync_batch_and_hospitals(batch_id=batch_id, hospitals=hospitals)
        return resp
