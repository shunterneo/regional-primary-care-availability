"""Pending source queue consolidation must preserve evidence and human decisions."""
import copy
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from review_queue_policy import consolidate_pending, record_change

def event(ident, stamp, url="https://clinic.example/intake", status="pending"):
    return {"id": ident, "url": url, "review_status": status,
            "detected_at": stamp, "old_hash": "a", "new_hash": ident,
            "current_excerpt": "Public page changed to " + ident,
            "possible_claim": "unconfirmed"}

queue = {"items": [
    event("one", "2026-11-19T00:00:00Z"),
    event("two", "2026-11-20T00:00:00Z"),
    event("resolved", "2026-11-18T00:00:00Z", status="resolved"),
    event("three", "2026-11-21T00:00:00Z"),
    event("other", "2026-11-21T00:00:00Z", url="https://other.example/"),
]}
original = copy.deepcopy(queue)
assert consolidate_pending(queue) == 2
assert consolidate_pending(queue) == 0  # idempotent
pending = [e for e in queue["items"] if e["review_status"] == "pending"]
assert len(pending) == 2
active = next(e for e in pending if e["url"].endswith("/intake"))
assert active["id"] == "one"
assert active["new_hash"] == "three"
assert len(active["transition_history"]) == 2
assert {e["id"] for e in active["transition_history"]} == {"two", "three"}
assert next(e for e in queue["items"] if e["id"] == "resolved") == original["items"][2]
assert record_change(queue, event("four", "2026-11-22T00:00:00Z")) is False
assert len(queue["items"]) == 5
assert active["new_hash"] == "four"
assert len(active["transition_history"]) == 3
assert record_change(queue, event("fresh", "2026-11-23T00:00:00Z",
                                 url="https://fresh.example/")) is True
assert len([e for e in queue["items"] if e["review_status"] == "pending"]) == 3
print("PASS: historic transitions retained, duplicate source notices consolidated, no resolved review reopened")
