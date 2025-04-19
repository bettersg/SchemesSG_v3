import firebase_admin
from firebase_admin import credentials, storage
import zipfile
import os
import time

def zip_folder(folder_path, output_zip_path):
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Arcname makes sure folder structure inside zip starts from the folder
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    print(f"Zipped folder '{folder_path}' into '{output_zip_path}'")



if __name__ == "__main__":
    zip_path = f"{int(time.time())}_models.zip"
    
    zip_folder(folder_path="models", output_zip_path=zip_path)
    
    cred = credentials.Certificate("backend/functions/creds.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'schemessg-v3-dev.firebasestorage.app'
    })

    bucket = storage.bucket()
    blob = bucket.blob(zip_path)
    blob.upload_from_filename(zip_path)
    print("File uploaded")
