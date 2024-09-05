import json
import os


QUERY_RECORDS_FP = "data/query_records.json"

def update_query_records(query_id: str, schemes) -> None:
    """
    Updates Json file with query records
    """

    # Creates the file if it doesn't exist
    if not os.path.exists(QUERY_RECORDS_FP):
        os.makedirs("data", exist_ok=True)
        with open(QUERY_RECORDS_FP, "w") as file:
            json.dump({}, file, indent=4)

    # Load existing data, append new data, and write back to the file
    with open(QUERY_RECORDS_FP, "r+") as file:
        data = json.load(file)
        data[query_id] = schemes
        file.seek(0)
        json.dump(data, file, indent=4)

def read_query_records(query_id: str) -> dict:
    with open(QUERY_RECORDS_FP, "r") as rec_files:
        entry = json.load(rec_files)[query_id]

    return entry
