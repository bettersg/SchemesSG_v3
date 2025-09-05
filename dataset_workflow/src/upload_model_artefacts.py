import firebase_admin
from firebase_admin import credentials, storage
import zipfile
import os
import time
import argparse
import sys
from loguru import logger
from uuid import uuid4

def zip_folder(folder_path, output_zip_path):
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Arcname makes sure folder structure inside zip starts from the folder
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    logger.info(f"Zipped folder '{folder_path}' into '{output_zip_path}'")

def upload_model_artefacts(creds_file, storage_bucket):
    zip_path = f"{int(time.time())}_models.zip"

    zip_folder(folder_path="dataset_worfklow/models", output_zip_path=zip_path)

    cred = credentials.Certificate(creds_file)
    firebase_admin.initialize_app(cred, {
        'storageBucket': storage_bucket
    })

    bucket = storage.bucket()
    blob = bucket.blob(zip_path)

    # Create new token
    new_token = uuid4()
    # Create new dictionary with the metadata
    metadata = {"firebaseStorageDownloadTokens": str(new_token)}
    # Set metadata to blob - make sure to convert UUID to string
    blob.metadata = metadata

    logger.info(f"Starting upload of {zip_path} to bucket {args.storage_bucket}...")
    # Add content_type and ensure metadata is uploaded
    blob.upload_from_filename(zip_path, timeout=300, content_type='application/zip')
    logger.info(f"Successfully uploaded {zip_path}")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )
    logger.info("Logger initialised")
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Zip model artefacts and upload to Firebase Storage.')
    parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
    parser.add_argument('storage_bucket', help='Name of the Firebase Storage bucket.')
    args = parser.parse_args()

    upload_model_artefacts(args.creds_file, args.storage_bucket)
