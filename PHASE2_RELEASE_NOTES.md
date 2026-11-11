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
