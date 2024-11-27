import os
import threading

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app


load_dotenv()


class FirebaseManager:
    """Singleton-patterned class for initialising Firebase Admin SDK and accessing firestore"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FirebaseManager, cls).__new__(cls)
                cls._instance._initialize_app()

            return cls._instance

    def _initialize_app(self):
        """Initialize Firebase App only once"""

        if not firebase_admin._apps:
            # Replace newlines in private key
            # private_key = os.getenv("FB_PRIVATE_KEY").replace("\\n", "\n")
            path_to_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

            if not path_to_creds or not os.path.exists(path_to_creds):
                raise ValueError(f"Invalid certificate path: {path_to_creds}. Make sure GOOGLE_APPLICATION_CREDENTIALS is set properly.")

            cred = credentials.Certificate(path_to_creds)  # Adjust path as needed

            # cred = credentials.Certificate(
            #     {
            #         "type": os.getenv("FB_TYPE"),
            #         "project_id": os.getenv("FB_PROJECT_ID"),
            #         "private_key_id": os.getenv("FB_PRIVATE_KEY_ID"),
            #         "private_key": private_key,  # Use the processed private key
            #         "client_email": os.getenv("FB_CLIENT_EMAIL"),
            #         "client_id": os.getenv("FB_CLIENT_ID"),
            #         "auth_uri": os.getenv("FB_AUTH_URI"),
            #         "token_uri": os.getenv("FB_TOKEN_URI"),
            #         "auth_provider_x509_cert_url": os.getenv("FB_AUTH_PROVIDER_X509_CERT_URL"),
            #         "client_x509_cert_url": os.getenv("FB_CLIENT_X509_CERT_URL"),
            #         "universe_domain": os.getenv("FB_UNIVERSE_DOMAIN"),
            #     }
            # )
            initialize_app(cred)

        self.firestore_client = firestore.client()
