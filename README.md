# Regional Primary Care Availability Hub — Phase 2

**An independent, public-information-only map and staff directory for family physician and nurse practitioner practices within 75 km (straight-line) of 96 Tillson Avenue, Tillsonburg, Ontario.** No employer account, work device, private client address, or identifiable patient information is required.

## Current state and honest boundaries

- **Built and locally tested:** A standalone interactive clinic overview, one verified-status JSON database, generated DOCX/PDF directories, automated official-source change detection, broader news-based clinic discovery, optional AI review assistance, a review-notification workflow, and a manual approval form that republishes approved changes.
- **Not yet deployed:** These scheduled jobs cannot run daily until this folder is uploaded into a **new personal GitHub repository** and GitHub Pages is enabled. The available GitHub connector cannot create a new repository. Do not upload to a workplace repository or an unrelated personal project.
- **Current data:** 95 clinic/service listings from the **November 11, 2026 research baseline**. The directory is not a completed CPSO/CNO audit. Intake claims are historical public-source research, not real-time availability guarantees.
- **Geography:** Existing records are grouped at *community-centre map markers*, not verified street-level clinic pins. New clinic records must use a verified public clinic coordinate to check the 75 km radius. Never supply patient addresses.
- **Automatic updates:** The map and documents *automatically rebuild and deploy* when the database has an **explicitly reviewed, approved** status change. Automated search results are **review leads only**. This conservative policy prevents a changed/blocked website from being labelled an intake closure.
- **Optional API:** AI-assisted public-text triage is disabled until a separately billed `OPENAI_API_KEY` is added as a personal-repository secret. Daily public-source checks and no-key RSS discovery still operate without it. ChatGPT subscription and ChatGPT automations do **not** automatically modify this repository.

## Key project components

| Path | Function |
|---|---|
| `site/index.html` | Public static clinic overview, filters and source links; **no patient-address search** |
| `site/documents/primary-care-directory.docx` | Staff Word directory, generated from the approved JSON |
| `site/documents/primary-care-directory.pdf` | Print-friendly PDF, generated from the same JSON |
| `data/clinics.json` | **Only published source of clinic status** |
| `data/review_history.json` | History of approved new clinics and status changes |
| `data/review_queue.json` | Public clinic source-page changes needing review |
| `data/discovery_queue.json` | Previously unseen *possible* clinic/intake news leads; not verified |
| `data/source_state.json`, `data/discovery_state.json` | Monitor checkpoints and source fetch health |
| `data/triage_state.json` | Optional AI suggestions, never automatically published |
| `.github/workflows/daily-site.yml` | Schedule: daily at 8:17 a.m. America/Toronto, plus manual runs |
| `.github/workflows/approve-clinic-change.yml` | Manual approval form, updates DB, regenerates Word/PDF/map |
| `scripts/add_clinic.py` | Manual addition after verifying public clinic street coordinates |

## Deploy under a personal GitHub account — one-time setup

1. In your **personal** GitHub account create an **empty public repository** (suggested name: `regional-primary-care-availability`). Do not initialize with a README or other files, and do not connect workplace services.
2. Unzip the package, then commit the **contents** of this directory to that repository's default `main` branch. The hidden `.github` folder must be included. GitHub Desktop can add a local repository and publish it, or Git can push from the extracted folder:

   ```bash
   git init
   git branch -M main
   git add .
   git commit -m "Initial independent regional primary care availability hub"
   git remote add origin https://github.com/YOUR_USERNAME/regional-primary-care-availability.git
   git push -u origin main
   ```

3. In the repository, **Settings → Pages → Build and deployment → GitHub Actions**. Under **Settings → Actions**, enable Actions and allow GitHub Actions to write to the repository; the workflow declares required permissions. Enable **Issues** if you want automatic consolidated review notifications.
4. **Actions → Check public intake sources and publish vetted directory → Run workflow.** Verify a successful Pages deployment, then open the Pages URL. The Word/PDF links on the website are stable even after updates.
5. The scheduled workflow subsequently checks existing clinic source pages and rotates through public Google News RSS searches for clinic/intake discoveries. It records new leads, runs tests, rebuilds the site and documents, and optionally creates **one GitHub Issue per run** with newly queued items for verification. If GitHub Issues is disabled, leads still remain in the JSON queues.
6. **Optional AI**: to enable bounded AI review of public excerpts, add `OPENAI_API_KEY` as an **Actions repository secret** in this *personal* repository. The default model is `gpt-5.4` and at most six items are sent per daily run. This incurs API charges. No clinic statuses are ever changed by AI output. Do not place the key in files or commit history.

If a workflow cannot run because the repository's permissions or Pages settings prevent it, review the failed Actions job rather than assuming the directory is current. Scheduled GitHub workflows can be delayed or disabled after inactivity; periodically verify the latest successful run. The public website's `Generated` date is not proof of a successful intake confirmation.

## How a new intake or closure is handled

1. The source monitor notices a change in intake-related public text, preserving a limited before/after excerpt. It never treats a request timeout, blocked page, or disappearing button as proof of closure.
2. The broader discovery monitor finds possible new clinic/intake mentions from public search feeds. News mentions require an **original clinic source, exact street office location, and 75 km radius verification** before becoming published records. RSS is not exhaustive and may miss new practices.
3. Both monitors put items in a *review queue*, with source links. Optional AI adds **review-only** interpretation of the excerpts, never publication.
4. A human reviewer confirms the clinic's explicit dated statement, eligible patient population, active application link, location and any conflicting claims. When evidence is absent or contradictory, **use unknown / needs reconfirmation**, not accepting or closed.
5. A reviewer updates an existing clinic through **Actions → Apply a reviewed clinic intake change → Run workflow**. Enter the clinic ID (e.g. `c001`), reviewed status, evidence URL, intake details and review note. The process validates the change, updates review history and regenerates/deploys the **map, DOCX and PDF from the same approved database**.
6. If a completely new clinic was discovered, add it with `scripts/add_clinic.py` only after confirming an exact public office address and coordinates within 75 km. New communities are supported. Rebuild and commit to `main`; the site workflow publishes it.

Example local review of a **verified** existing practice:

```bash
python scripts/update_status.py \
  --id c001 --status accepting \
  --source 'https://www.grandriverchc.ca/your-health/new-clients/' \
  --detail 'Published new-client intake form available; eligibility and attachment require confirmation.' \
  --reviewer-note 'Official current clinic page checked; reviewed independently of automated suggestion.'
python scripts/validate.py
python scripts/build.py
```

Example adding a **verified public clinic building** (fictional example; **do not run with placeholders**):

```bash
python scripts/add_clinic.py --name 'VERIFIED CLINIC NAME' --community 'EXACT TOWN' \
  --address 'VERIFIED PUBLIC CLINIC ADDRESS' --clinic-type MD \
  --latitude 42.86 --longitude -80.72 --status unknown \
  --intake-detail 'No current intake statement found' \
  --source 'https://example.org/official-clinic-page' \
  --reviewer-note 'Verified public clinic address and coordinates within the boundary; no patient information.'
```

## Locally run validation and generate files

Requires Python 3.12+ and Node for the dependency-free UI test:

```bash
python -m pip install -r requirements.txt
python scripts/validate.py
python scripts/build.py
python tests/monitor_fixture_test.py
python tests/discovery_fixture_test.py
python tests/approval_fixture_test.py
node tests/site_js_smoke.cjs
```

An additional Playwright browser visual smoke test is included for machines that have Chromium/Playwright installed. It is **not** required in GitHub Actions, where it would otherwise need separate browser installation.

## Privacy and evidence safeguards

The public website requests **no patient address**, uses **no external maps, scripts, tracking pixels, cookies, API calls, logins or form submissions**, and does not ask for names or medical information. Research workflows fetch only publicly listed clinic pages and public news feeds. The optional API sends only short **public clinic** excerpts, never personal health information. Clinic website links open external pages only when actively clicked. A public repository and public GitHub Issues must contain **no private client data or workplace records**.

This design avoids the earlier geocoding disclosure, but it is **not a PHIPA certification**. Any organization should apply its own policies before recommending the public resource in clinical practice. Public clinic contact data and intake information can become stale; the site indicates review dates and downgrades old claims to "Needs reconfirmation". **Last webpage fetch does not mean intake re-verification.**

## Known limitations and next QA priorities

- No live deployment yet, so GitHub Actions network/permissions/Pages have **not** been end-to-end verified.
- RSS news monitoring is a discovery supplement, **not** a systematic CPSO/CNO provider census or a guarantee of finding every intake opening.
- The original 95 records have not all been independently reverified. Street-level clinic pin locations and any boundary-edge practices need an exact-address audit before the map can be treated as spatially complete.
- Patient acceptance can close between checks. Never promise that registration or attachment is guaranteed; clinic contact is the final confirmation.
- No unrestricted AI auto-publishing: intake changes require **explicit evidence and review**, to avoid accidental inaccurate referrals.
