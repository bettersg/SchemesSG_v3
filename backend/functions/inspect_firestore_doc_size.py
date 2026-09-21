import json

with open("firestore_doc.json", "r") as f:
    doc = json.load(f)

# find keys and size of each field
for key, value in doc.items():
    size = len(json.dumps(value))
    print(f"Key: {key}, Size: {size} bytes")

