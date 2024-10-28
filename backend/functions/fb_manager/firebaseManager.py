import threading

import firebase_admin
from firebase_admin import credentials, firestore, initialize_app


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
            cred = credentials.Certificate("creds.json")
            initialize_app(cred)

        self.firestore_client = firestore.client()
