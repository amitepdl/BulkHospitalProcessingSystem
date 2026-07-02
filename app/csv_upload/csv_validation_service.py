import csv
import io

"""
Service to validate the CSV file and it's column formats,
the format of the csv file should be as it is defined in the sample csv file.

It validates all the rows of the csv file, and attaches key <is_valid> to the hospital data
 and return list of hospital data 
"""


class CSVValidationService:

    @staticmethod
    def validate_file_meta(*, uploaded_file):
        if not uploaded_file:
            return False, "No file uploaded"

        filename = uploaded_file.filename
        if not filename or "." not in filename:
            return False, "Invalid file name"

        ext = filename.rsplit(".", 1)[1].lower()
        if ext not in ["csv"]:
            return False, "Only CSV files are allowed"

        MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
        if uploaded_file.content_length and uploaded_file.content_length > MAX_FILE_SIZE:
            return False, "File size exceeds 2MB"

        return True, None

    @staticmethod
    def validate_hospital_csv(*, uploaded_file):

        file_meta_status, resp = CSVValidationService.validate_file_meta(uploaded_file=uploaded_file)
        if not file_meta_status:
            return file_meta_status, resp

        required_columns = {"name", "address", "phone"}

        # Read uploaded file
        stream = io.StringIO(uploaded_file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)

        # Validate columns
        if set(reader.fieldnames) != required_columns:
            error = f"Invalid columns. Expected {required_columns}, found {reader.fieldnames}"
            return False, error

        rows = list(reader)

        # Validate max records
        if len(rows) > 20:
            error = f"Maximum 20 hospital records allowed, found {len(rows)}"
            return False, error

        # Validate row values
        validated_hospitals = []
        for idx, row in enumerate(rows, start=1):
            row_data = {
                "row": idx,
                "is_valid": True
            }
            row_errors = []
            for col in required_columns:
                value = row.get(col)
                if col != "phone" and (not value or not value.strip()):
                    row_data["is_valid"] = False
                    row_errors.append(f"'{col}' cannot be empty")

                row_data[col] = value.strip() if value else value

            validated_hospitals.append(row_data)
        return True, validated_hospitals
