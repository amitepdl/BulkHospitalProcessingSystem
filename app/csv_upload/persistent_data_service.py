import base64
import threading
from flask import current_app

"""
Persistent data layer:
1. For very processed hospital of a batch, it adds the hospital data in a dictionary for
with key being combination of batch_id, name and address

2. Additionally keeps a set of batch_ids processed so far for data consistency  
"""


class PersistentDataService:

    def __init__(self):
        self.shared_batch_info = current_app.config["shared_batch_info"]
        self.shared_hospital_info = current_app.config["shared_hospital_info"]

    @staticmethod
    def encode(*, text):
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")

    @staticmethod
    def decode(*, encoded_text):
        return base64.b64decode(encoded_text).decode("utf-8")

    @staticmethod
    def get_batch_hospital_identifier(*, batch_id, name, address):
        identifier = f"{batch_id}@__@{name}@__@{address}"
        encoded_identifier = PersistentDataService.encode(text=identifier)
        return encoded_identifier

    def add_batch_hospital(self, batch_id, hospital):
        name = hospital["name"]
        address = hospital["address"]
        encoded_identifier = PersistentDataService.get_batch_hospital_identifier(
            batch_id=batch_id, name=name, address=address
        )
        self.shared_batch_info.add(batch_id)
        # if encoded_identifier not in self.shared_hospital_info:
        self.shared_hospital_info[encoded_identifier] = hospital

    def check_hospital_in_batch(self, batch_id, hospital):
        name = hospital["name"]
        address = hospital["address"]
        encoded_identifier = PersistentDataService.get_batch_hospital_identifier(
            batch_id=batch_id, name=name, address=address
        )
        return batch_id in self.shared_batch_info and encoded_identifier in self.shared_hospital_info

    def get_batch_hospital(self, batch_id, hospital):
        name = hospital["name"]
        address = hospital["address"]
        encoded_identifier = PersistentDataService.get_batch_hospital_identifier(
            batch_id=batch_id, name=name, address=address
        )
        if batch_id not in self.shared_batch_info:
            return None

        return self.shared_hospital_info.get(encoded_identifier)

    def update_processed_hospitals(self, batch_id, validated_hospitals):
        if batch_id not in self.shared_batch_info:
            return

        hl = len(validated_hospitals)
        for i in range(hl):
            h = validated_hospitals[i]
            temp = self.get_batch_hospital(batch_id=batch_id, hospital=h)
            validated_hospitals[i] = temp or h


class AsyncHandlerService:

    @staticmethod
    def fire_and_forget(func):
        def wrapped(*args, **kwargs):
            app = current_app._get_current_object()

            def run():
                with app.app_context():
                    func(*args, **kwargs)

            threading.Thread(target=run).start()
        return wrapped

    @staticmethod
    @fire_and_forget
    def sync_batch_and_hospitals(*, batch_id, hospitals):
        print(f"Sync task triggered for {batch_id=}")
        data_service = PersistentDataService()
        for h in hospitals:
            if h.get("is_processed"):
                data_service.add_batch_hospital(batch_id=batch_id, hospital=h)

        print(f"{data_service.shared_batch_info}")
        print(f"{data_service.shared_hospital_info}")
