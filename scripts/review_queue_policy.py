"""One active source-review case per URL; retain every historical observation.

Only source review queue metadata is modified; no clinic status or intake evidence
is automatically approved. Existing closed reviews are never reopened.
"""
from __future__ import annotations

import copy
from collections import defaultdict


def _transition(item):
    return {
        "id": item.get("id"),
        "detected_at": item.get("detected_at"),
        "old_hash": item.get("old_hash"),
        "new_hash": item.get("new_hash"),
        "prior_excerpt": item.get("prior_excerpt"),
        "current_excerpt": item.get("current_excerpt"),
        "possible_claim": item.get("possible_claim"),
        "matched_excerpts": item.get("matched_excerpts"),
        "extraction_version": item.get("extraction_version"),
    }


def consolidate_pending(queue):
    """Collapse unresolved duplicates without deleting evidence or prior decisions.

    The earliest pending ID is retained for dashboard and notification stability.
    Superseded records stay in the queue, with a link to their active case.
    """
    grouped = defaultdict(list)
    for entry in queue.get("items", []):
        if entry.get("review_status") == "pending" and entry.get("url"):
            grouped[entry["url"]].append(entry)
    collapsed = 0
    for url, rows in grouped.items():
        if len(rows) < 2:
            continue
        rows.sort(key=lambda x: (x.get("detected_at", ""), x.get("id", "")))
        primary = rows[0]
        for duplicate in rows[1:]:
            primary.setdefault("transition_history", []).append(_transition(duplicate))
            for field in ("new_hash", "current_excerpt", "possible_claim",
                          "matched_excerpts", "assessment_version", "extraction_version"):
                if field in duplicate:
                    primary[field] = copy.deepcopy(duplicate[field])
            primary["last_detected_at"] = duplicate.get("detected_at")
            duplicate["review_status"] = "superseded"
            duplicate["superseded_by"] = primary["id"]
            collapsed += 1
    return collapsed


def record_change(queue, new_item):
    """Append only if no pending case for the same source URL exists."""
    matches = [item for item in queue["items"]
               if item.get("url") == new_item.get("url")
               and item.get("review_status") == "pending"]
    if not matches:
        queue["items"].append(new_item)
        return True
    primary = min(matches, key=lambda x: (x.get("detected_at", ""), x.get("id", "")))
    # Record transition even if a page alternates between earlier versions.
    primary.setdefault("transition_history", []).append(_transition(new_item))
    for field in ("new_hash", "current_excerpt", "possible_claim",
                  "matched_excerpts", "assessment_version", "extraction_version"):
        if field in new_item:
            primary[field] = copy.deepcopy(new_item[field])
    primary["last_detected_at"] = new_item.get("detected_at")
    primary["observations_count"] = len(primary["transition_history"]) + 1
    return False
