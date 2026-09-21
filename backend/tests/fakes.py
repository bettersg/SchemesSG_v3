"""Stateful fakes for backend handler and maintenance contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from google.cloud import firestore


class FakeDocumentSnapshot:
    def __init__(self, doc_id: str, data: dict[str, Any] | None):
        self.id = doc_id
        self.exists = data is not None
        self._data = deepcopy(data)

    def to_dict(self) -> dict[str, Any] | None:
        return deepcopy(self._data)


class FakeDocumentReference:
    def __init__(self, client: "FakeFirestore", collection_name: str, doc_id: str):
        self._client = client
        self._collection_name = collection_name
        self.id = doc_id

    def get(self) -> FakeDocumentSnapshot:
        return FakeDocumentSnapshot(
            self.id,
            self._client.get_document(self._collection_name, self.id),
        )

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        self._client._set_document(self._collection_name, self.id, data, merge=merge)

    def update(self, fields: dict[str, Any]) -> None:
        self._client._update_document(self._collection_name, self.id, fields)


class FakeCollectionReference:
    def __init__(self, client: "FakeFirestore", name: str):
        self._client = client
        self._name = name

    def document(self, doc_id: str | None = None) -> FakeDocumentReference:
        return FakeDocumentReference(self._client, self._name, doc_id or self._client._new_id())

    def add(self, data: dict[str, Any]):
        doc_ref = self.document()
        doc_ref.set(data)
        return None, doc_ref

    def stream(self) -> list[FakeDocumentSnapshot]:
        return [
            FakeDocumentSnapshot(doc_id, data)
            for doc_id, data in sorted(self._client.list_documents(self._name).items())
        ]


class FakeWriteBatch:
    def __init__(self, client: "FakeFirestore"):
        self._client = client
        self._operations: list[tuple[str, FakeDocumentReference, dict[str, Any] | None]] = []

    def update(self, doc_ref: FakeDocumentReference, fields: dict[str, Any]) -> None:
        self._operations.append(("update", doc_ref, deepcopy(fields)))

    def delete(self, doc_ref: FakeDocumentReference) -> None:
        self._operations.append(("delete", doc_ref, None))

    def commit(self) -> None:
        for _, doc_ref, _ in self._operations:
            self._client._ensure_write_allowed(doc_ref._collection_name)
        for operation, doc_ref, fields in self._operations:
            if operation == "update":
                self._client._update_document(doc_ref._collection_name, doc_ref.id, fields or {})
            else:
                self._client._delete_document(doc_ref._collection_name, doc_ref.id)


class FakeFirestore:
    """Minimal in-memory Firestore surface used by the covered public seams."""

    def __init__(self):
        self._documents: dict[str, dict[str, dict[str, Any]]] = {}
        self._id_counter = 0
        self.fail_writes_for: set[str] = set()

    def collection(self, name: str) -> FakeCollectionReference:
        return FakeCollectionReference(self, name)

    def batch(self) -> FakeWriteBatch:
        return FakeWriteBatch(self)

    def seed(self, collection_name: str, doc_id: str, data: dict[str, Any]) -> None:
        self._documents.setdefault(collection_name, {})[doc_id] = deepcopy(data)

    def get_document(self, collection_name: str, doc_id: str) -> dict[str, Any] | None:
        data = self._documents.get(collection_name, {}).get(doc_id)
        return deepcopy(data) if data is not None else None

    def list_documents(self, collection_name: str) -> dict[str, dict[str, Any]]:
        return deepcopy(self._documents.get(collection_name, {}))

    def _new_id(self) -> str:
        self._id_counter += 1
        return f"fake-{self._id_counter}"

    def _ensure_write_allowed(self, collection_name: str) -> None:
        if collection_name in self.fail_writes_for:
            raise RuntimeError(f"Deterministic write failure for {collection_name}")

    def _set_document(
        self,
        collection_name: str,
        doc_id: str,
        data: dict[str, Any],
        *,
        merge: bool,
    ) -> None:
        self._ensure_write_allowed(collection_name)
        collection = self._documents.setdefault(collection_name, {})
        if not merge or doc_id not in collection:
            collection[doc_id] = deepcopy(data)
            return
        collection[doc_id].update(deepcopy(data))

    def _update_document(self, collection_name: str, doc_id: str, fields: dict[str, Any]) -> None:
        self._ensure_write_allowed(collection_name)
        collection = self._documents.setdefault(collection_name, {})
        if doc_id not in collection:
            raise KeyError(f"Missing document {collection_name}/{doc_id}")
        document = collection[doc_id]
        for field_path, value in fields.items():
            self._apply_field(document, field_path, value)

    def _delete_document(self, collection_name: str, doc_id: str) -> None:
        self._ensure_write_allowed(collection_name)
        self._documents.get(collection_name, {}).pop(doc_id, None)

    @staticmethod
    def _apply_field(document: dict[str, Any], field_path: str, value: Any) -> None:
        parts = field_path.split(".")
        target = document
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        if value is firestore.DELETE_FIELD:
            target.pop(parts[-1], None)
        else:
            target[parts[-1]] = deepcopy(value)


class FakeSlackClient:
    def __init__(self, reviewer_email: str = "reviewer@example.com"):
        self.reviewer_email = reviewer_email
        self.posted_messages: list[dict[str, Any]] = []
        self.updated_messages: list[dict[str, Any]] = []
        self.opened_views: list[dict[str, Any]] = []

    def users_info(self, *, user: str) -> dict[str, Any]:
        return {
            "ok": True,
            "user": {"id": user, "profile": {"email": self.reviewer_email}},
        }

    def chat_postMessage(self, **payload) -> dict[str, Any]:
        self.posted_messages.append(deepcopy(payload))
        return {"ok": True, "ts": f"posted-{len(self.posted_messages)}"}

    def chat_update(self, **payload) -> dict[str, Any]:
        self.updated_messages.append(deepcopy(payload))
        return {"ok": True}

    def views_open(self, **payload) -> dict[str, Any]:
        self.opened_views.append(deepcopy(payload))
        return {"ok": True}
