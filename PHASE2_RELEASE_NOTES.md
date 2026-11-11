# Phase 2 — Release notes (11 November 2026)

## Implemented

- Maintains the 95-listing baseline and public regional map with intake filters.
- Watches known clinic evidence pages for **text changes**, preserving short old/new evidence excerpts and a cautious possible-status label.
- Searches a rolling set of place-specific **public news RSS queries** to identify potentially missed clinics and new intakes. New leads are deduplicated and flagged for original-source and 75 km verification; they **never become public clinic listings automatically**.
- Optional OpenAI API triage of short *public-source* excerpts. It is disabled without an API secret, rate-limited, and cannot approve or publish any intake status.
- Scheduled GitHub Actions workflow rebuilds the map, Word, and PDF from one approved clinic database, then publishes through GitHub Pages once deployed.
- A second, manual GitHub Actions workflow accepts a reviewed clinic-status change and automatically regenerates and republishes map and directories.
- Consolidated issue notifications for **newly observed review leads** (if GitHub Issues is enabled).
- Validates all new exact public-clinic coordinates against the 75 km boundary; no private address or patient search.
- Automated tests for intake negation and contradictory statements, feed deduplication, timeout safety, change monitoring, approval, and website filters.

## Not yet active / verified

- Personal GitHub repository and Pages deployment have **not** been set up; no daily GitHub run has occurred.
- Optional OpenAI API integration is not active without a personal API secret (separate billing).
- The legacy 95-clinic baseline remains a starting directory, not an exhaustive up-to-date physician census.
- Exact individual clinic map pins and comprehensive full-radius discovery still need further source checks.

## Safe operating rule

No search result, stale link, RSS headline, AI inference or webpage failure automatically turns a clinic marker to **Accepting** or **Closed**. Only an explicit reviewed decision changes the published status. Older statuses gradually display **Needs reconfirmation**.

### Autonomous confirmation release
- Added deterministic first-party two-day intake confirmation; auto-publishes clinic-specific accepting and not-accepting statements while rejecting ambiguous, stale and shared team-level notices.
- Explicit permanent closures are archived only after confirmation on two separate days; removal from active map and documents preserves the audit record.
- Added automatic discovery of government-listed NP, FHT and CHC program sites through Ontario MOHSERLO; exact public coordinates required; added entries are labeled intake unknown and not presumed operational.
- Uncertain public search results still require human review. No third-party AI or news article can independently assert accepting patients.
- Added offline regression tests for safe closure, duplicate suppression, conflicting language and transient source failures.
