# inspect firestore for debugging purposes

from integrations import FirebaseManager
from google.cloud import firestore
import json

if __name__ == "__main__":
    firebase_manager = FirebaseManager()
    firestore_client = firebase_manager.firestore_client

    # Example: List all collections
    collections = firestore_client.collections()
    print("Collections in Firestore:")
    for collection in collections:
        print(f"- {collection.id}")

    chat_history_ref = firestore_client.collection("chatHistory")
    get_doc = firestore_client.collection("llmQuery").document("Arwq78F1MZUDS5J2twXg").get()
    print("Document data for llmQuery/Arwq78F1MZUDS5J2twXg:")
    print(len(get_doc.to_dict().get("schemes_response", [])))
    # test_docs = firestore_client.collection("chatHistory").limit(10).stream()
    # latest_docs = chat_history_ref.order_by("last_updated", direction=firestore.Query.DESCENDING).limit(10).stream()
    # print("Inspecting document fields:")
    # for doc in latest_docs:
    #     print(f"ID: {doc.id} -> Fields: {list(doc.to_dict().keys())}")

    # doc = chat_history_ref.document("test-emission-de22").get()
    # with open("firestore_doc.json", "w") as f:
    #     json.dump(doc.to_dict(), f, indent=2)
