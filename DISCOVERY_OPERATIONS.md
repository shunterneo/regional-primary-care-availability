# Independent discovery — operating guide

This public-data system runs without any client information, account connections to an employer, patient-address input, or automatic scraping of practitioner registers.

## Daily independent searches

1. **Known practice websites:** check publicly stated intake notices for changes. Strict first-party, location-specific statements may be auto-published only after two separate successful checks and only if the existing evidence safeguards pass.
2. **Regional intake and clinic directories:** read published lists from the London & District Academy of Medicine, Brant Community Healthcare System, Doctors4Cambridge, Southwest Healthline, Oxford Ontario Health Team, and Woodstock municipal news. New listing candidates, changed excerpts, and removals create **review-only** queue items in `data/directory_queue.json`; they never directly change accepted/closed labels. A vanished directory item does not prove a practice closed.
3. **Google News / municipal news discovery:** rotate through 31 queries (16 daily), including city-specific and physician recruitment searches. News articles lead to investigation, not publication.
4. **Ontario Ministry of Health open facility register:** after an independent office review recorded in `publication_approvals` and two observations, qualifying FHT/CHC/NP-led entries may be added with `registry_listed` operational status and **intake unknown**. A government directory does not prove operating status or patient acceptance.
5. **CPSO/CNO:** there is no integrated, authorized comprehensive bulk extraction in this project. A weekly rotating **manual cross-check task** covers Oxford, Elgin/Norfolk, Middlesex, and Brant/Waterloo/Perth. Public register links are provided in a review issue. Official registration proves only registration/practice-location details, not whether patients are being accepted.

## Where results go

- `data/directory_queue.json`: new or changed entries from curated sources, including possible removed/renamed entries.
- `data/directory_state.json`: prior directory snapshots, last-success timestamps, and source errors. A failed fetch preserves the prior snapshot.
- `data/discovery_queue.json`: news-lead queue.
- `data/registry_audit_queue.json`: human register cross-check tasks.
- `data/review_queue.json`: monitored clinic-page changes.
- GitHub Issues: one consolidated issue containing at most 80 newly queued findings per run. Unsent findings remain queued for a later run.

## Safeguards

- **Nothing from third-party directory lists, CPSO/CNO, or news is automatically labelled “accepting.”** A directory item could describe episodic walk-in care, a waitlist, a roster from an old announcement, or a clinic outside the exact 75 km circle.
- An office **cannot be declared permanently closed** because one directory dropped it or because a website times out.
- A named practice and its verified public location must be checked for clinic model (ongoing, both, walk-in only), within-radius geography, and new-patient eligibility before a reviewer adds it.
- The public site does not submit client data or accept client address queries.
- Source uptime is monitored; a failed or blocked page is *not* treated as an empty directory.

## QA and audit

```sh
python scripts/validate.py
python tests/discovery_fixture_test.py
python tests/directory_discovery_fixture_test.py
python tests/auto_publication_test.py
node tests/site_js_smoke.cjs
```

Even after these improvements, searches are not exhaustive. Individual family physicians can open or close rosters without publishing a notice; clinic verification remains necessary for referrals.

## Verified execution — 12 November 2026 UTC

Run 43150063574 executed the real network pipeline and deployed successfully. It retrieved 55 of 74 clinic-source URLs, three of six curated directories, and 40 government records. Nineteen source fetches failed (mostly HTTP 403; one certificate error); these are not closures. The government list includes administrative and community-program sites, so repeated registry presence alone can no longer publish a clinic. See `data/registry_review_2026-11-12.json` for all 40 dispositions.

A push whose commit message includes `[full-audit]` runs and persists network monitoring as well as normal validation and deployment. Optional AI triage and issue notifications remain restricted to scheduled/manual runs. Monitoring and display dates use UTC consistently.
