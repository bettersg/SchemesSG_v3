"""Unit tests for the dev-only prod -> dev Firestore collection sync."""

import pytest
from batch_jobs import firebase_collection_sync as sync

from tests.fakes import FakeCollectionReference, FakeFirestore


PROD = "schemessg"
DEV = "schemessg-v3-dev"


class SyncCollection(FakeCollectionReference):
    def list_documents(self):
        return [self.document(doc_id) for doc_id in sorted(self._client.list_documents(self._name))]


class SyncBulkWriter:
    """Like Firestore's BulkWriter, a write that keeps failing is dropped, not raised."""

    def __init__(self, client):
        self._client = client

    def set(self, doc_ref, data, merge=False):
        self._attempt(doc_ref.set, data, merge=merge)

    def delete(self, doc_ref):
        self._attempt(self._client._delete_document, doc_ref._collection_name, doc_ref.id)

    def close(self):
        pass

    @staticmethod
    def _attempt(write, *args, **kwargs):
        try:
            write(*args, **kwargs)
        except RuntimeError:
            pass


class SyncFirestore(FakeFirestore):
    """FakeFirestore plus the project id and bulk-write surface the sync uses."""

    def __init__(self, project):
        super().__init__()
        self.project = project

    def collection(self, name):
        return SyncCollection(self, name)

    def bulk_writer(self):
        return SyncBulkWriter(self)


def _scheme(name, **extra):
    return {"scheme": name, "agency": "Agency", "link": f"https://example.org/{name}", **extra}


@pytest.fixture
def prod():
    return SyncFirestore(PROD)


@pytest.fixture
def dev():
    return SyncFirestore(DEV)


@pytest.fixture(autouse=True)
def clients(mocker, prod, dev):
    mocker.patch.object(sync, "client", side_effect={PROD: prod, DEV: dev}.__getitem__)


def test_sync_makes_dev_an_exact_copy_of_prod(prod, dev):
    prod.seed("schemes", "a", _scheme("A"))
    prod.seed("schemes", "b", _scheme("B", agency="New Agency"))
    dev.seed("schemes", "b", _scheme("B", agency="Old Agency", dev_only_field="stale"))
    dev.seed("schemes", "c", _scheme("C"))
    prod_before = prod.list_documents("schemes")

    sync.sync_collection("schemes", dry_run=False)

    # Missing docs are added, changed docs are fully overwritten (not merged), extra docs are deleted.
    assert dev.list_documents("schemes") == prod_before
    assert prod.list_documents("schemes") == prod_before


def test_rerunning_the_sync_is_safe(prod, dev):
    prod.seed("schemes", "a", _scheme("A"))
    dev.seed("schemes", "c", _scheme("C"))

    sync.sync_collection("schemes", dry_run=False)
    after_first_run = dev.list_documents("schemes")
    sync.sync_collection("schemes", dry_run=False)

    assert dev.list_documents("schemes") == after_first_run == prod.list_documents("schemes")


@pytest.mark.parametrize(
    "write",
    [
        lambda db, docs: sync.upsert_firebase_collection(db, "schemes", docs),
        lambda db, docs: sync.prune_firebase_collection(db, "schemes", docs, dry_run=False),
    ],
    ids=["upsert", "prune"],
)
def test_never_writes_to_prod(write, prod):
    prod.seed("schemes", "a", _scheme("A"))
    prod_before = prod.list_documents("schemes")

    with pytest.raises(ValueError, match="only schemessg-v3-dev is allowed"):
        write(prod, {"b": _scheme("B")})

    assert prod.list_documents("schemes") == prod_before


def test_empty_prod_read_never_wipes_dev(dev):
    dev.seed("schemes", "a", _scheme("A"))
    dev.seed("schemes", "b", _scheme("B"))
    dev_before = dev.list_documents("schemes")

    with pytest.raises(ValueError, match="empty"):
        sync.sync_collection("schemes", dry_run=False)

    assert dev.list_documents("schemes") == dev_before


def test_dropped_writes_alert_slack_and_fail_the_run(mocker, prod, dev, fake_slack_client):
    prod.seed("schemes", "b", _scheme("B", agency="New Agency"))
    dev.seed("schemes", "b", _scheme("B", agency="Old Agency"))
    dev.seed("schemes", "c", _scheme("C"))
    dev.fail_writes_for.add("schemes")
    mocker.patch.object(sync, "get_slack_client", return_value=fake_slack_client)
    mocker.patch.object(sync, "get_slack_channel", return_value="C-sync")

    # Re-raising matters: the scheduler wrapper turns it into an HTTP 500, which triggers the retry.
    with pytest.raises(ValueError, match="dev does not match prod"):
        sync.scheduled_firebase_collection_sync.__wrapped__(mocker.MagicMock())

    [alert] = fake_slack_client.posted_messages
    assert alert["channel"] == "C-sync"
    assert "sync failed" in alert["text"]
    assert "extra 1, changed 1" in alert["text"]


def test_dry_run_reports_extra_docs_without_deleting(dev):
    dev.seed("schemes", "a", _scheme("A"))
    dev.seed("schemes", "c", _scheme("C"))
    dev_before = dev.list_documents("schemes")

    extra = sync.prune_firebase_collection(dev, "schemes", {"a": _scheme("A")}, dry_run=True)

    assert extra == ["c"]
    assert dev.list_documents("schemes") == dev_before


def test_sync_is_a_dry_run_unless_told_otherwise(prod, dev):
    prod.seed("schemes", "a", _scheme("A"))
    prod.seed("schemes", "b", _scheme("B", agency="New Agency"))
    dev.seed("schemes", "b", _scheme("B", agency="Old Agency"))
    dev.seed("schemes", "c", _scheme("C"))
    dev_before = dev.list_documents("schemes")

    missing, extra, changed = sync.sync_collection("schemes")

    assert (missing, extra, changed) == (["a"], ["c"], ["b"])
    assert dev.list_documents("schemes") == dev_before
