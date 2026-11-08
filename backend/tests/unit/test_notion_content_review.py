"""Unit tests for the Notion content review queue: monthly push and hourly sweep (#407)."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from batch_jobs import notion_content_review as review
from batch_jobs.notion_client import NotionClient, decode_row

from tests.fakes import FakeFirestore


CFG = {"token": "secret", "data_source": "ds-review"}
NOW = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
LINK = "https://example.org/carefund"
C = review.FIELD_TO_COLUMN  # Firestore field -> Notion column name (with emoji)
NEW_PAGES = [{"url": LINK, "hash": "new-hash", "contacts": ["67654321"]}]


class FakeNotion(NotionClient):
    """In-memory Notion behind the real client's request seam (page size 2 to exercise pagination)."""

    def __init__(self):
        self.pages = {}
        self.children = {}
        self.schema = {}
        self.trashed = []
        self.calls = []

    def _call(self, method, path, body=None):
        self.calls.append((method, path))
        parts = path.split("?")[0].split("/")
        if path.endswith("/query"):
            rows = [p for p in self.pages.values() if p["parent"] == parts[2] and p["id"] not in self.trashed]
            if body.get("filter"):
                wanted = {f["select"]["equals"] for f in body["filter"]["or"]}
                rows = [p for p in rows if decode_row(p).get("Status") in wanted]
            start = int(body.get("start_cursor") or 0)
            more = start + 2 < len(rows)
            return {
                "results": deepcopy(rows[start : start + 2]),
                "has_more": more,
                "next_cursor": str(start + 2) if more else None,
            }
        if method == "PATCH" and parts[1] == "data_sources":
            self.schema.update(deepcopy(body["properties"]))
            return {}
        if method == "POST" and path == "/pages":
            page_id = f"page-{len(self.pages) + 1}"
            self.pages[page_id] = {"id": page_id, "parent": body["parent"]["data_source_id"], "properties": {}}
            self.children[page_id] = deepcopy(body.get("children") or [])
            self._apply(page_id, body["properties"])
            return deepcopy(self.pages[page_id])
        if method == "PATCH" and parts[1] == "pages":
            if body.get("in_trash"):
                self.trashed.append(parts[2])
            else:
                self._apply(parts[2], body["properties"])
            return deepcopy(self.pages[parts[2]])
        if parts[1] == "blocks":
            page_id = parts[2]
            if method == "GET":
                blocks = [{"id": f"{page_id}-b{i}"} for i, _ in enumerate(self.children.get(page_id, []))]
                return {"results": blocks, "has_more": False}
            if method == "DELETE":
                owner = page_id.rsplit("-b", 1)[0]
                self.children[owner] = self.children[owner][1:]
                return {}
            if method == "PATCH":
                self.children[page_id].extend(deepcopy(body["children"]))
                return {}
        raise AssertionError(f"Unexpected Notion call {method} {path}")

    def _apply(self, page_id, properties):
        """Store a write the way Notion returns it on read."""
        for name, payload in properties.items():
            kind = next(iter(payload))
            value = payload[kind]
            if kind in ("title", "rich_text"):
                value = [{"plain_text": piece["text"]["content"]} for piece in value]
            self.pages[page_id]["properties"][name] = {"type": kind, kind: value}

    def row(self, page_id):
        return decode_row(self.pages[page_id])

    def set_values(self, page_id, **values):
        """A volunteer editing the row in Notion."""
        types = {**review.COLUMN_TYPES, "Reviewer": "people"}
        for name, value in values.items():
            if types[name] == "people":
                self.pages[page_id]["properties"][name] = {"type": "people", "people": [{"id": "u1", "name": value}]}
            else:
                from batch_jobs.notion_client import encode_properties

                self._apply(page_id, encode_properties({name: value}, types))

    def body_text(self, page_id):
        return "".join(
            piece.get("text", {}).get("content", "")
            for block in self.children[page_id]
            for piece in block["callout"]["rich_text"]
        )


def scheme(**overrides):
    data = {
        "scheme": "Care Fund",
        "link": LINK,
        "llm_description": "Monthly cash help for seniors.",
        "description": "Old legacy description.",
        "summary": "Up to $300 a month.",
        "eligibility": "Citizens aged 65 and above.",
        "how_to_apply": "Apply online.",
        "who_is_it_for": ["Seniors", "Legacy tag"],
        "what_it_gives": ["Financial assistance (general)"],
        "scheme_type": ["Financial Assistance"],
        "agency": "Care FSC",
        "address": "1 Sample Street",
        "phone": "6123 4567",
        "email": "help@example.org",
        "service_area": "Toa Payoh",
        "search_booster": "elderly cash aid",
        "planning_area": "Toa Payoh",
        "content_pages": [{"url": LINK, "hash": "old-hash", "contacts": ["61234567"]}],
    }
    data.update(overrides)
    return data


def flag(db, check_id="check-1", scheme_id="s1", suggestions=None, contact_check=None, **extra):
    db.seed(
        "contentChecks",
        check_id,
        {
            "scheme_id": scheme_id,
            "status": "pending",
            "suggestions": suggestions
            if suggestions is not None
            else [
                {
                    "field": "eligibility",
                    "new_value": "Citizens and PRs aged 60 and above.",
                    "quote": "open to Citizens and PRs aged 60 and above",
                    "page_url": LINK,
                }
            ],
            "contact_check": contact_check or [],
            "new_pages": NEW_PAGES,
            **extra,
        },
    )


def setup(**scheme_overrides):
    db = FakeFirestore()
    db.seed("schemes", "s1", scheme(**scheme_overrides))
    return db, FakeNotion()


def push(db, notion, check_ids=("check-1",), now=NOW):
    return review.push_flagged(list(check_ids), db=db, notion=notion, cfg=CFG, now=now)


def sweep(db, notion, now=NOW + timedelta(days=3)):
    return review.sweep_decided(db=db, notion=notion, cfg=CFG, now=now)


#### Monthly push


def test_push_creates_row_with_new_value_prefilled_and_new_and_old_in_box():
    db, notion = setup()
    flag(db)
    assert push(db, notion) == {"created": 1, "updated": 0, "skipped_decided": 0, "failed": 0}

    row = notion.row("page-1")
    assert row[C["eligibility"]] == "Citizens and PRs aged 60 and above."  # AI's new value
    assert row[C["summary"]] == "Up to $300 a month."  # unchanged field = stored value
    assert row[C["llm_description"]] == "Monthly cash help for seniors."  # llm_description, not legacy
    assert row[C["who_is_it_for"]] == ["Seniors"]  # tag no longer on the allowed list is not shown
    assert row["Changed by AI"] == ["Eligibility"]
    assert (row["Status"], row["Scheme ID"], row["Check ID"]) == ("Pending", "s1", "check-1")
    assert row[review.DIFF_COLUMN] == ""
    body = notion.body_text("page-1")
    assert body.startswith("Fields marked ✏️")  # how-to note first, right under the fields
    assert "🎯 Eligibility: changed by AI" in body and LINK in body
    assert (
        "🆕 New: Citizens and PRs aged 60 and above.\n\n↩️ Old: Citizens aged 65 and above.\n\n"
        '💬 Quote: "open to Citizens and PRs aged 60 and above"\n\n🔗 Source: '
    ) in body
    record = db.get_document("contentChecks", "check-1")
    assert (record["notion_page_id"], record["pushed_at"]) == ("page-1", NOW)


def test_push_populates_text_diff_column_when_present():
    db, notion = setup()
    diff_text = "Page: https://example.org/carefund\n+ Citizens and PRs aged 60 and above.\n- Citizens aged 65 and above."
    flag(db, diff=diff_text)
    push(db, notion)

    row = notion.row("page-1")
    assert row[review.DIFF_COLUMN] == diff_text
    assert notion.schema[review.DIFF_COLUMN] == {"rich_text": {}}


def test_push_populates_text_diff_column_from_text_diff_key():
    db, notion = setup()
    diff_text = "Page: https://example.org/carefund\n+ New text line"
    flag(db, text_diff=diff_text)
    push(db, notion)

    row = notion.row("page-1")
    assert row[review.DIFF_COLUMN] == diff_text


def test_push_shows_old_vocabulary_tags_translated():
    db, notion = setup(scheme_type=["Financial Assistance", "Legal Aid"])
    flag(db)
    push(db, notion)

    row = notion.row("page-1")
    assert row[C["scheme_type"]] == ["Financial Assistance"]
    assert row[C["what_it_gives"]] == ["Financial assistance (general)", "Legal aid and services"]  # moved field


def test_push_shows_when_the_listing_was_last_updated_in_either_stored_form():
    db, notion = setup(last_scraped_update=datetime(2025, 3, 4, 2, 0, tzinfo=timezone.utc))
    db.seed("schemes", "s2", scheme(last_scraped_update={"_seconds": 1700000000, "_nanoseconds": 0}))  # old import
    flag(db)
    flag(db, "check-2", scheme_id="s2")
    push(db, notion, ["check-1", "check-2"])

    assert notion.row("page-1")["Last updated"] == "2025-03-04"  # listing date, not the push date
    assert notion.row("page-2")["Last updated"] == "2023-11-14"


def test_push_sets_tag_dropdowns_to_the_allowed_lists_without_commas():
    db, notion = setup()
    flag(db)
    push(db, notion)

    for field, allowed in review.TAG_OPTIONS.items():
        options = [o["name"] for o in notion.schema[C[field]]["multi_select"]["options"]]
        assert options == [review.notion_option(tag) for tag in allowed]
        assert not any("," in option for option in options)  # Notion rejects commas in option names


def test_comma_tag_shows_with_slashes_in_notion_and_saves_with_commas():
    tag = "Benefits and perks for PWDs (transport, discounts, facilities)"
    db, notion = setup(what_it_gives=[tag])
    flag(db)
    push(db, notion)
    assert notion.row("page-1")[C["what_it_gives"]] == [
        "Benefits and perks for PWDs (transport / discounts / facilities)"
    ]

    notion.set_values("page-1", Status="Approved")
    sweep(db, notion)
    assert db.get_document("schemes", "s1")["what_it_gives"] == [tag]


def test_push_refreshes_pending_row_and_deletes_replaced_check():
    db, notion = setup()
    flag(db)
    push(db, notion)
    flag(db, "check-2", suggestions=[{"field": "summary", "new_value": "Up to $400 a month.", "page_url": LINK}])

    assert push(db, notion, ["check-2"])["updated"] == 1
    assert list(notion.pages) == ["page-1"]  # same row, no duplicate
    row = notion.row("page-1")
    assert (row[C["summary"]], row[C["eligibility"]], row["Check ID"]) == (
        "Up to $400 a month.",
        "Citizens aged 65 and above.",
        "check-2",
    )
    assert row["Changed by AI"] == ["Summary"]
    assert "💡 Summary: changed by AI" in notion.body_text("page-1")
    assert "🎯 Eligibility: changed by AI" not in notion.body_text("page-1")  # old box replaced
    assert db.get_document("contentChecks", "check-1") is None  # replaced check deleted
    assert db.get_document("contentChecks", "check-2")["notion_page_id"] == "page-1"


@pytest.mark.parametrize("status", ["Approved", "Rejected"])
def test_push_leaves_decided_row_for_the_sweep(status):
    db, notion = setup()
    flag(db)
    push(db, notion)
    notion.set_values("page-1", Status=status, **{C["eligibility"]: "Volunteer text"})
    flag(db, "check-2")

    assert push(db, notion, ["check-2"])["skipped_decided"] == 1
    assert notion.row("page-1")["Status"] == status
    assert notion.row("page-1")[C["eligibility"]] == "Volunteer text"
    assert "notion_page_id" not in db.get_document("contentChecks", "check-2")


def test_push_and_sweep_do_nothing_without_notion_settings(monkeypatch):
    monkeypatch.delenv("NOTION_API_TOKEN", raising=False)
    monkeypatch.delenv("NOTION_CONTENT_CHECK_DATA_SOURCE_ID", raising=False)
    assert review.push_flagged(["check-1"]) == {"skipped": "notion not configured"}
    assert review.sweep_decided() == {"skipped": "notion not configured"}


def test_push_failure_for_one_check_does_not_stop_the_others():
    db, notion = setup()
    flag(db)
    assert push(db, notion, ["missing", "check-1"])["failed"] == 1
    assert notion.row("page-1")["Scheme ID"] == "s1"


def test_push_pending_finds_a_record_saved_by_the_monthly_job():
    db, notion = setup()
    # Every field check_scheme saves; its status is lowercase while Notion's is "Pending".
    flag(
        db,
        scheme="Care Fund",
        link=LINK,
        created_at=NOW,
        pages=[{"url": LINK, "change": "changed"}],
        diff="- old\n+ new",
        text_diff="- old\n+ new",
        review_input_truncated=False,
        model="test-model",
        prompt_version="test-prompt",
    )

    result = review.push_pending(db=db, notion=notion, cfg=CFG, now=NOW)

    assert result["created"] == 1
    assert notion.row("page-1")["Status"] == "Pending"
    assert db.get_document("contentChecks", "check-1")["notion_page_id"] == "page-1"


def test_push_pending_skips_records_already_in_notion():
    db, notion = setup()
    flag(db, notion_page_id="page-9")
    assert review.push_pending(db=db, notion=notion, cfg=CFG, now=NOW)["created"] == 0
    assert notion.pages == {}


def test_contact_gone_from_site_replaces_phone():
    db, notion = setup()
    gone = [{"contact": "61234567", "pages": [LINK + "/contact"], "replacements": ["6765 4321"]}]
    flag(db, suggestions=[], contact_check=gone)
    push(db, notion)
    row = notion.row("page-1")
    assert (row[C["phone"]], row["Changed by AI"]) == ("6765 4321", ["Phone"])
    body = notion.body_text("page-1")
    assert "6123 4567" in body  # previous value in the box
    assert "💬 Quote" not in body  # the contact check gives no quote


def test_contact_gone_keeps_the_whole_1800_replacement():
    changes = review.contact_changes(
        {"phone": "+65 6123 4567"},
        [{"contact": "61234567", "pages": [LINK], "replacements": ["1800 123 4567"]}],
    )
    assert changes["phone"]["new_value"] == "1800 123 4567"


def test_gone_1800_number_matches_the_stored_phone():
    changes = review.contact_changes(
        {"phone": "1800 123 4567, 6222 3333"},
        [{"contact": "18001234567", "pages": [LINK], "replacements": ["6765 4321"]}],
    )
    assert changes["phone"]["new_value"] == "6222 3333, 6765 4321"


def test_replacement_already_on_the_scheme_is_not_added_twice():
    changes = review.contact_changes(
        {"phone": "6123 4567, 6765-4321"},
        [{"contact": "61234567", "pages": [LINK], "replacements": ["+65 6765 4321", "6765 4321"]}],
    )
    assert changes["phone"]["new_value"] == "6765-4321"


def test_contact_gone_that_is_not_in_the_fields_gets_a_note():
    db, notion = setup()
    flag(db, suggestions=[], contact_check=[{"contact": "old@example.org", "pages": [LINK], "replacements": []}])
    push(db, notion)
    assert notion.row("page-1")["Changed by AI"] == []
    assert "No longer on the website: old@example.org" in notion.body_text("page-1")


def test_long_description_survives_the_round_trip():
    long_text = "Monthly cash help. " * 300  # > 2000 chars, Notion's limit per text piece
    db, notion = setup()
    flag(db, suggestions=[{"field": "llm_description", "new_value": long_text, "page_url": LINK}])
    push(db, notion)
    notion.set_values("page-1", Status="Approved")
    sweep(db, notion)
    saved = db.get_document("schemes", "s1")
    assert saved["llm_description"] == long_text.strip() and saved["description"] == long_text.strip()


#### Hourly sweep


@pytest.fixture
def warnings():
    """Warning messages loguru logs during the test."""
    messages = []
    sink = review.logger.add(lambda m: messages.append(m.record["message"]), level="WARNING")
    yield messages
    review.logger.remove(sink)


def test_push_saves_the_scheme_as_stored_before_tags_are_translated():
    db, notion = setup(scheme_type=["Financial Assistance", "Legal Aid"], planning_area=["BEDOK", "TAMPINES"])
    flag(db)
    push(db, notion)

    pushed = db.get_document("contentChecks", "check-1")["pushed_values"]
    assert set(pushed) == set(review.FIELD_COLUMNS.values())
    assert pushed["scheme_type"] == ["Financial Assistance", "Legal Aid"]  # raw, not translated
    assert pushed["eligibility"] == "Citizens aged 65 and above."  # Firestore's value, not the AI's
    assert pushed["planning_area"] == ["BEDOK", "TAMPINES"]


def test_approved_row_writes_ai_and_volunteer_changes_and_new_hashes_then_trashes_row():
    db, notion = setup()
    flag(db)
    push(db, notion)
    notion.set_values(
        "page-1",
        Status="Approved",
        Reviewer="Alex Tan",
        **{
            C["summary"]: "Up to $350 a month.",  # a fix the AI did not suggest
            C["llm_description"]: "New description.",
            C["who_is_it_for"]: ["Seniors", "Legacy tag", "Made-up tag", "Caregivers"],
            C["service_area"]: "Islandwide",
        },
    )

    assert sweep(db, notion) == {"approved": 1, "rejected": 0, "skipped": 0, "already_applied": 0, "failed": 0}
    saved = db.get_document("schemes", "s1")
    assert saved["eligibility"] == "Citizens and PRs aged 60 and above."
    assert saved["summary"] == "Up to $350 a month."
    assert saved["llm_description"] == saved["description"] == "New description."
    assert saved["who_is_it_for"] == ["Seniors", "Caregivers"]  # tags not on the allowed list dropped
    assert saved["service_area"] == "Islandwide"
    assert saved["content_pages"] == NEW_PAGES
    assert saved["last_scraped_update"] == NOW + timedelta(days=3)  # website "Last updated" = approval time
    record = db.get_document("contentChecks", "check-1")
    assert (record["status"], record["decided_by"]) == ("approved", "Alex Tan")
    assert record["expires_at"] > record["decided_at"]
    assert notion.trashed == ["page-1"]


def test_approve_keeps_firestore_changes_made_after_the_push(warnings):
    db, notion = setup(who_is_it_for=["Seniors"])  # only allowed tags, so the row shows them unchanged
    flag(db)
    push(db, notion)
    db.seed("schemes", "s1", scheme(agency="New FSC", who_is_it_for=["Caregivers"]))  # e.g. console edit, re-tag
    notion.set_values("page-1", Status="Approved")

    sweep(db, notion)
    saved = db.get_document("schemes", "s1")
    assert saved["agency"] == "New FSC"  # untouched in Notion: newer Firestore value kept
    assert saved["who_is_it_for"] == ["Caregivers"]
    assert saved["eligibility"] == "Citizens and PRs aged 60 and above."  # AI's change still saved
    assert warnings == []


def test_volunteer_wins_when_firestore_changed_the_same_field(warnings):
    db, notion = setup()
    flag(db)
    push(db, notion)
    db.seed("schemes", "s1", scheme(summary="Console summary."))
    notion.set_values("page-1", Status="Approved", **{C["summary"]: "Volunteer summary."})

    sweep(db, notion)
    assert db.get_document("schemes", "s1")["summary"] == "Volunteer summary."
    assert any("summary changed in Firestore since the push" in m for m in warnings)


def test_approve_copying_the_old_value_back_keeps_it():
    db, notion = setup()
    flag(db)
    push(db, notion)
    notion.set_values("page-1", Status="Approved", **{C["eligibility"]: "Citizens aged 65 and above."})

    sweep(db, notion)
    assert db.get_document("schemes", "s1")["eligibility"] == "Citizens aged 65 and above."


def test_missing_column_is_skipped_not_blanked(warnings):
    db, notion = setup()
    flag(db, suggestions=[{"field": "llm_description", "new_value": "AI description.", "page_url": LINK}])
    push(db, notion)
    del notion.pages["page-1"]["properties"][C["llm_description"]]  # column renamed in Notion
    notion.set_values("page-1", Status="Approved", **{C["summary"]: "Up to $350 a month."})

    sweep(db, notion)
    saved = db.get_document("schemes", "s1")
    assert saved["llm_description"] == "Monthly cash help for seniors."
    assert saved["description"] == "Old legacy description."
    assert saved["summary"] == "Up to $350 a month."  # rest of the row still saved
    assert any(C["llm_description"] in m and "missing" in m for m in warnings)


def test_untouched_list_planning_area_stays_a_list():
    db, notion = setup(planning_area=["BEDOK", "TAMPINES"])
    flag(db)
    push(db, notion)
    assert notion.row("page-1")[C["planning_area"]] == "BEDOK, TAMPINES"
    notion.set_values("page-1", Status="Approved")

    sweep(db, notion)
    assert db.get_document("schemes", "s1")["planning_area"] == ["BEDOK", "TAMPINES"]


def test_edited_list_planning_area_is_saved_as_a_list():
    db, notion = setup(planning_area=["BEDOK", "TAMPINES"])
    flag(db)
    push(db, notion)
    notion.set_values("page-1", Status="Approved", **{C["planning_area"]: "BEDOK,  PASIR RIS, "})

    sweep(db, notion)
    assert db.get_document("schemes", "s1")["planning_area"] == ["BEDOK", "PASIR RIS"]


def test_edited_text_planning_area_stays_text():
    db, notion = setup()
    flag(db)
    push(db, notion)
    notion.set_values("page-1", Status="Approved", **{C["planning_area"]: "Toa Payoh, Bishan"})

    sweep(db, notion)
    assert db.get_document("schemes", "s1")["planning_area"] == "Toa Payoh, Bishan"


def test_approve_saves_translated_tags_even_when_untouched():
    db, notion = setup(scheme_type=["Financial Assistance", "Legal Aid"])
    flag(db)
    push(db, notion)
    notion.set_values("page-1", Status="Approved")

    sweep(db, notion)
    saved = db.get_document("schemes", "s1")
    assert saved["scheme_type"] == ["Financial Assistance"]
    assert saved["what_it_gives"] == ["Financial assistance (general)", "Legal aid and services"]
    assert saved["who_is_it_for"] == ["Seniors"]  # "Legacy tag" is not on the allowed list


def test_record_without_pushed_values_compares_with_the_scheme_now():
    db, notion = setup()
    flag(db)
    push(db, notion)
    record = db.get_document("contentChecks", "check-1")
    del record["pushed_values"]  # pushed before pushed_values existed
    db.seed("contentChecks", "check-1", record)
    notion.set_values("page-1", Status="Approved", **{C["summary"]: "Up to $350 a month."})

    sweep(db, notion)
    saved = db.get_document("schemes", "s1")
    assert saved["summary"] == "Up to $350 a month."
    assert saved["eligibility"] == "Citizens and PRs aged 60 and above."
    assert saved["address"] == "1 Sample Street"


def test_rejected_row_keeps_fields_but_saves_new_hashes():
    db, notion = setup()
    flag(db)
    push(db, notion)
    notion.set_values("page-1", Status="Rejected")

    assert sweep(db, notion)["rejected"] == 1
    saved = db.get_document("schemes", "s1")
    assert saved["eligibility"] == "Citizens aged 65 and above."  # AI's value not applied
    assert saved["content_pages"] == NEW_PAGES  # same change won't flag again
    assert saved["last_scraped_update"] == NOW + timedelta(days=3)  # reviewed: listing confirmed as is
    assert db.get_document("contentChecks", "check-1")["status"] == "rejected"
    assert notion.trashed == ["page-1"]


def test_retired_scheme_is_not_written_and_row_is_removed():
    db, notion = setup()
    flag(db)
    push(db, notion)
    db.seed("schemes", "s1", scheme(status="retired"))
    notion.set_values("page-1", Status="Approved")

    assert sweep(db, notion)["skipped"] == 1
    assert db.get_document("schemes", "s1") == scheme(status="retired")
    record = db.get_document("contentChecks", "check-1")
    assert (record["status"], record["skip_reason"]) == ("skipped", "scheme retired")
    assert notion.trashed == ["page-1"]


def test_scheme_replaced_in_slack_after_push_is_not_written():
    db, notion = setup()
    flag(db)
    push(db, notion)
    db.seed("schemes", "s1", scheme(approved_at=NOW + timedelta(days=1)))
    notion.set_values("page-1", Status="Approved")

    assert sweep(db, notion)["skipped"] == 1
    assert db.get_document("schemes", "s1")["eligibility"] == "Citizens aged 65 and above."
    assert notion.trashed == ["page-1"]


def test_firestore_failure_keeps_row_for_next_run():
    db, notion = setup()
    flag(db)
    push(db, notion)
    notion.set_values("page-1", Status="Approved")
    db.fail_writes_for = {"schemes"}

    assert sweep(db, notion)["failed"] == 1
    assert notion.trashed == []
    assert db.get_document("contentChecks", "check-1")["status"] == "pending"

    db.fail_writes_for = set()
    assert sweep(db, notion)["approved"] == 1
    assert notion.trashed == ["page-1"]


@pytest.mark.parametrize("status", ["Approved", "Rejected"])
def test_retry_after_failed_trash_only_trashes_the_row(status):
    db, notion = setup()
    flag(db)
    push(db, notion)
    notion.set_values("page-1", Status=status)
    real_trash = notion.trash_page
    notion.trash_page = lambda page_id: (_ for _ in ()).throw(RuntimeError("Notion down"))

    assert sweep(db, notion)["failed"] == 1
    first_scheme = db.get_document("schemes", "s1")
    first_record = db.get_document("contentChecks", "check-1")
    assert first_record["status"] == status.lower()
    db.seed("schemes", "s1", {**first_scheme, "summary": "Edited after the decision."})

    notion.trash_page = real_trash
    assert sweep(db, notion, now=NOW + timedelta(days=4))["already_applied"] == 1
    assert notion.trashed == ["page-1"]
    saved = db.get_document("schemes", "s1")
    assert saved["summary"] == "Edited after the decision."  # not overwritten by the retry
    assert saved["last_scraped_update"] == first_scheme["last_scraped_update"]  # not moved forward
    assert db.get_document("contentChecks", "check-1") == first_record


def test_sweep_ignores_pending_rows():
    db, notion = setup()
    flag(db)
    push(db, notion)
    assert sweep(db, notion) == {"approved": 0, "rejected": 0, "skipped": 0, "already_applied": 0, "failed": 0}
    assert notion.trashed == []
