from flask import Flask

from app.csv_upload.apis import csv_bp


def get_app():
    app = Flask(__name__)
    app.config["shared_batch_info"] = set()
    app.config["shared_hospital_info"] = {}
    app.register_blueprint(csv_bp)

    return app
