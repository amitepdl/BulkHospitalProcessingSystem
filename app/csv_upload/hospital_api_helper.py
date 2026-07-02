import logging
from requests import request, Response

"""
hospital API Helper:
helps in calling the api endpoints provided in the assignment docs
"""


logger = logging.getLogger(__name__)


class HospitalApiHelper:

    @staticmethod
    def get_headers():
        headers = {
            "Accept": "application/json"
        }
        return headers

    @staticmethod
    def get_url(*, target="CreateHospital", **kwargs):
        base_url = "https://hospital-directory.onrender.com"
        if target == "CreateHospital":
            return f"{base_url}/hospitals/"
        elif target == "ActivateBatch":
            batch_id = kwargs["batch_id"]
            return f"{base_url}/hospitals/batch/{batch_id}/activate"
        else:
            raise NotImplementedError

    @staticmethod
    def handle_response(*, resp: Response, target="CreateHospital"):
        resp_dict = resp.json()
        print(resp_dict)
        if resp.status_code == 200:
            return True, resp_dict
        else:
            e = resp_dict.get("detail")
            if e and isinstance(e, str):
                error = e
            else:
                error = resp_dict.get("detail", [{}]).get("msg")

            if target == "CreateHospital":
                logger.error(f"Failed to create hospital")
            elif target == "ActivateBatch":
                logger.error(f"Failed to activate hospitals corresponding to the provided batch_id")
            return False, error

    @staticmethod
    def create_hospital(*, data):
        headers = HospitalApiHelper.get_headers()
        name = data.get("name")
        logger.info(f"Creating hospital record with {name=}")
        url = HospitalApiHelper.get_url()
        resp = request(url=url, method="POST", headers=headers, json=data)
        status, handled_resp = HospitalApiHelper.handle_response(resp=resp)
        return status, handled_resp

    @staticmethod
    def activate_batch(*, batch_id):
        target = "ActivateBatch"
        logger.info(f"Activating hospitals with {batch_id=}")
        headers = HospitalApiHelper.get_headers()
        url = HospitalApiHelper.get_url(target=target, batch_id=batch_id)
        resp = request(url=url, method="PATCH", headers=headers)
        handled_resp = HospitalApiHelper.handle_response(resp=resp, target=target)
        return handled_resp
