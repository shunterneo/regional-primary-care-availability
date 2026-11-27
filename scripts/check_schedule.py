"""Watch scheduled runner starts separately from source coverage and publication."""
import datetime as dt
import json
import sys
from zoneinfo import ZoneInfo

TORONTO = ZoneInfo("America/Toronto")
UTC = dt.timezone.utc
GRACE = dt.timedelta(hours=2)


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo is not None else None


def assess(runs, now):
    now = now.astimezone(UTC)
    local = now.astimezone(TORONTO)
    due = local.replace(hour=8, minute=17, second=0, microsecond=0)
    if local < due:
        due -= dt.timedelta(days=1)
    deadline = (due + GRACE).astimezone(UTC)
    due_utc = due.astimezone(UTC)
    current = []
    for run in runs:
        if run.get("event") != "schedule":
            continue
        created = timestamp(run.get("created_at"))
        if created is not None and due_utc <= created <= now:
            current.append((created, run))
    created, latest = max(current, key=lambda item: item[0]) if current else (None, {})
    status = latest.get("status")
    started = timestamp(latest.get("run_started_at"))
    if (started is not None and
            (not created <= started <= now or status in {"queued", "requested", "waiting", "pending"})):
        started = None
    late = bool(started and started > deadline)
    problem = None
    if not latest and now >= deadline:
        problem = "No daily scheduled run observed after the expected start plus 2-hour grace period"
    elif latest and status == "completed" and latest.get("conclusion") != "success":
        problem = "Latest daily scheduled run did not succeed"
    elif latest and not started and now >= deadline:
        problem = "No verified runner start by the deadline; a queued run or deployment is not a completed scan"
    elif late:
        problem = "Daily scheduled runner started after the 2-hour grace period; eventual success does not establish on-time execution"
    elif started and now - started > GRACE and status != "completed":
        problem = "Daily scheduled run has not completed within 2 hours of its runner start"
    return {
        "queue_delay_minutes": round((created - due_utc).total_seconds()/60,2) if created else None,
        "start_delay_minutes": round((started - due_utc).total_seconds()/60,2) if started else None,
        "late_start": late,
        "queued_at": created.isoformat() if created else None,
        "runner_started_at": started.isoformat() if started else None,
        "checked_at": now.isoformat(),
        "expected_start": due.isoformat(),
        "grace_deadline": deadline.astimezone(TORONTO).isoformat(),
        "latest_scheduled_run": latest.get("html_url"),
        "healthy": problem is None,
        "problem": problem,
        "note": "Push/manual runs do not satisfy scheduled-run coverage. GitHub runner start is not the actual scan step or verified clinic intake. Scheduler delay cause is unknown.",
    }


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as file:
        result = assess(json.load(file)["workflow_runs"], dt.datetime.now(UTC))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["healthy"] else 1)
