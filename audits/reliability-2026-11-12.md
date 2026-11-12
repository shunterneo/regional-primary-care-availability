# Monitoring reliability review, 12 November 2026

## Observed, not inferred

Production HEAD at inspection: `20e3aded074917ebab8672fb57d562a1d59da8a9`.
Run 43265835599 deployed successfully with source monitoring skipped. Network monitoring last persisted at 04:35 UTC. GitHub returned zero schedule and zero workflow_dispatch runs; the workflow itself is active. Official GitHub documentation supports its `America/Toronto` timezone syntax. The reason a schedule has not fired is not established. Do not present configuration as proof of execution.

## This branch

- Adds a separate six-hour, no-publication heartbeat with a deduplicated GitHub issue and a failing health check for missing/old scans, uncovered sources, failures or old per-source success timestamps.
- Separates source attempt health from intake certainty. Public build report contains monitoring health; site warns about incomplete or old monitoring.
- Rejects empty and common HTTP-200 challenge/login shells without changing clinic status.
- Preserves intake's own date during unrelated editor corrections; expiry does not inherit a new phone/address edit date.
- Emits an exclusive evidence-expiry date and downgrades expired client-side status before showing filters, counts, maps and dynamic exports, even if no build has occurred. Rechecks when an open tab becomes visible. This never upgrades a record.
- Does not change acceptance/closure evidence thresholds or enable auto-updates for any clinic.

## Verification / remaining operational steps

Run project validation, build, all offline fixtures and Node UI tests. Browser tests require a permitted Chromium runtime. The environment used for this audit denied Chromium socket creation even after an escalated attempt; a test failure before browser launch is not an application failure or a pass.

The health watcher is not an independent external uptime monitor: a total GitHub scheduler outage also prevents this watcher. An external scheduled check should inspect `report.json` and workflow history. Verify the first heartbeat issue and next actual daily invocation after deployment. A manual full-audit is appropriate to cover the new evidence URLs, but is not proof that the daily scheduler works.

Saved Word/PDF exports are dated snapshots and cannot expire after download. The website's dynamic exports use the current downgraded data, while prebuilt downloads retain their generation-date caveats. No client addresses, patient records or work-system integrations are introduced.

## Independent-review follow-through

Additional offline regressions now cover a continuously visible tab (one-minute expiry recheck), expiry at each filter/export call, and actual CSV/PDF/DOCX encoding after expiry. Python now ages secondary-source fallbacks before they can appear in newly built documents. JavaScript-only shell pages are rejected without rejecting valid short notices or ordinary prose containing “just a moment”. The separate browser regression adds an actual CSV-download assertion; it remains unexecuted because browser launch is unavailable here. Saved files are still static snapshots, not continuously updated documents.
