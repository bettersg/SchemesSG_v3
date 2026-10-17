import argparse

import firebase_admin
from firebase_admin import firestore
from firebase_functions import options, scheduler_fn
from loguru import logger

from batch_jobs.run_link_check_and_reindex import get_slack_channel, get_slack_client


#### Functions


def client(project_id):
    try:
        app = firebase_admin.get_app(project_id)
    except ValueError:
        app = firebase_admin.initialize_app(options={"projectId": project_id}, name=project_id)
    return firestore.client(app)


def retrieve_firebase_collection(project, collection_name):
    docs = {d.id: d.to_dict() for d in project.collection(collection_name).stream()}
    logger.info(f"Retrieved {len(docs)} docs from {project.project}/{collection_name}")
    return docs


def upsert_firebase_collection(client, collection_name, docs):
    """Overwrite each doc in `docs` ({doc_id: data}) into `collection`, creating any that don't exist."""
    if client.project != "schemessg-v3-dev":
        raise ValueError(f"Refusing to write to {client.project}; only schemessg-v3-dev is allowed")

    bw = client.bulk_writer()
    for doc_id, data in docs.items():
        bw.set(client.collection(collection_name).document(doc_id), data)  # full overwrite, not merge
    bw.close()  # waits for all writes to finish

    # Verify that dev has all the scheme IDs in production
    dev_ids = {ref.id for ref in client.collection(collection_name).list_documents()}
    missing = docs.keys() - dev_ids
    if missing:
        raise ValueError(
            f"Upserted {len(docs)} docs; {collection_name} now has {len(dev_ids)}; missing: {len(missing)}"
        )


def prune_firebase_collection(client, collection_name, docs, dry_run=True):
    """Delete docs in `collection` whose IDs aren't keys in `docs`."""
    if client.project != "schemessg-v3-dev":
        raise ValueError(f"Refusing to write to {client.project}; only schemessg-v3-dev is allowed")

    if not docs:
        raise ValueError("docs is missing or empty. Aborting prune")

    refs = client.collection(collection_name).list_documents()
    to_delete = [ref for ref in refs if ref.id not in docs]
    logger.info(f"{len(to_delete)} docs in {collection_name} not in source")

    if dry_run:
        return [ref.id for ref in to_delete]

    bw = client.bulk_writer()
    for ref in to_delete:
        bw.delete(ref)
    bw.close()  # waits for all deletes to finish

    remaining = {ref.id for ref in client.collection(collection_name).list_documents()}
    logger.info(f"Deleted {len(to_delete)}; {collection_name} now has {len(remaining)} docs")
    return [ref.id for ref in to_delete]


def diff_collections(prod_docs, dev_docs):
    """Doc IDs a sync would add to, delete from, and overwrite in dev."""
    missing = sorted(prod_docs.keys() - dev_docs.keys())
    extra = sorted(dev_docs.keys() - prod_docs.keys())
    changed = sorted(k for k in prod_docs.keys() & dev_docs.keys() if prod_docs[k] != dev_docs[k])
    return missing, extra, changed


def validate(dev_project, prod_docs, collection_name):
    """Raise if dev's `collection_name` doesn't exactly match `prod_docs`."""
    dev_docs = retrieve_firebase_collection(dev_project, collection_name)

    missing, extra, changed = diff_collections(prod_docs, dev_docs)
    if missing or extra or changed:
        raise ValueError(
            f"{collection_name}: dev does not match prod after sync "
            f"(missing {len(missing)}, extra {len(extra)}, changed {len(changed)})"
        )


### Run it


def sync_collection(collection_name="schemes", dry_run=True):
    # This is a small cloud function which upserts and then prunes the contents of the production firestore database collection "schemes" to its dev equivalent.
    # https://github.com/bettersg/SchemesSG_v3/issues/446
    # Dry run by default: only report what would change. Pass dry_run=False to write to dev.

    prod_project = client("schemessg")
    dev_project = client("schemessg-v3-dev")

    prod_docs = retrieve_firebase_collection(prod_project, collection_name)

    if dry_run:
        dev_docs = retrieve_firebase_collection(dev_project, collection_name)
        missing, extra, changed = diff_collections(prod_docs, dev_docs)
        if not prod_docs:
            logger.warning(f"Prod {collection_name} is empty; a real run would abort without changing dev")
        logger.info(
            f"Dry run, nothing written. Would add {len(missing)}, overwrite {len(changed)}, delete {len(extra)} "
            f"in dev {collection_name}. add={missing[:20]} overwrite={changed[:20]} delete={extra[:20]}"
        )
        return missing, extra, changed

    upsert_firebase_collection(dev_project, collection_name, prod_docs)
    prune_firebase_collection(dev_project, collection_name, prod_docs, dry_run=False)
    validate(dev_project, prod_docs, collection_name)


@scheduler_fn.on_schedule(
    schedule="0 9 1,15 * *",  # 9am SGT on the 1st and 15th of each month
    timezone=scheduler_fn.Timezone("Asia/Singapore"),
    region="asia-southeast1",
    memory=options.MemoryOption.GB_2,
    timeout_sec=540,
    retry_count=1,
    service_account="collections-sync@schemessg-v3-dev.iam.gserviceaccount.com",
)
def scheduled_firebase_collection_sync(event: scheduler_fn.ScheduledEvent) -> None:
    try:
        sync_collection("schemes", dry_run=False)
    except Exception as e:
        logger.exception("Prod -> dev sync failed")
        try:
            get_slack_client().chat_postMessage(
                channel=get_slack_channel(),
                text=f":x: Prod -> dev `schemes` sync failed: {e}",
            )
        except Exception:
            logger.exception("Failed to post sync failure to Slack")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make dev's schemes collection an exact copy of prod's.")
    parser.add_argument(
        "--apply", action="store_true", help="Write to dev. Without it, only report what would change."
    )
    sync_collection("schemes", dry_run=not parser.parse_args().apply)
