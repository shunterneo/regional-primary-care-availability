# Regional Primary Care Availability Hub — Phase 2

## Automatic status publication paused (November 16, 2026)

Automatic intake-status and permanent-closure writes are temporarily paused while evidence-context safeguards are strengthened. Public-source checking, discovery, candidate observations, review alerts, existing records, and explicitly reviewed manual updates continue. No clinic status was changed by this safety pause. `auto_publish.py` now defaults to no writes, and the daily workflow explicitly sets `AUTO_PUBLICATION_ENABLED: 'false'`. Do not re-enable it until the context-preserving rules have passed independent review and fresh, versioned observations have been collected. The automatic-publication descriptions below document the paused capability, not an active guarantee.

**An independent, public-information-only map and staff directory for family physician and nurse practitioner practices within 75 km (straight-line) of 96 Tillson Avenue, Tillsonburg, Ontario.** No employer account, work device, private client address, or identifiable patient information is required.


## Paused safety hardening: evidence and new profiles

The automatic intake writer remains disabled. Passing offline tests is not permission to re-enable it or a claim that arbitrary clinic webpages can be interpreted safely.

- Automatic candidates now use a separate complete-context extractor instead of truncated change-notification snippets. The bounded adapter supports **static text-only HTML**. Executable scripts, CSS-dependent rendering, images/embedded media, collapsed content and ambiguous notices require a separately reviewed adapter or manual review. Dates, qualifications, quotations and contradictions are review-only; unsupported text is not an intake decision.
- Each eligible source needs an independently recorded `auto_publication_scope`: version 1, exact clinic/source identity hash, single-office scope, review date/method/evidence, and approved full non-claim context template hash. The template also binds DOM structure and attributes. Only an exact bounded intake sentence can vary without a new context review. **No existing record is automatically granted this approval.**
- Observations carry `context-v2`, complete-context/template hashes and scope fingerprints. Legacy observations, changed context/scope, invalid or repeated/future dates, failed latest fetches, non-HTTPS or different-path redirects cannot reuse prior confirmation days. New reviews require fresh observations; two sightings are stability evidence, not independent corroboration.
- New government profiles require an exact schema-version/candidate-hash approval, public source, explicit office/duplicate review, care-model evidence and a review no more than 30 days old. Bare historical booleans are rejected. Intake remains unknown; no missing fact is invented. Registry failure/malformed-response health is retained separately from previous facts.
- Manual additions now accept **unknown intake only** and require `--coordinate-source`. Apply any later sourced intake change through the existing reviewed-update workflow. Both manual and registry profiles retain coordinate provenance; validation rejects nonfinite/out-of-range coordinates and enforces the 75 km boundary using the emitted office point, without a rounding buffer.
- Name alone, a shared building, or an address prefix is not an office identity. Distinct addresses/suites remain distinct candidates; unresolved possible duplicates still need review.

These controls reduce specific demonstrated risks. They do not resolve all inaccessible sources, prove clinic capacity, provide a complete provider census, or certify PHIPA compliance. Real source-specific pilots and independent review are still required before any future enablement.

## November 11 source-integrity audit and limitations

The November 11 audit reviewed **all 96 records in that historical baseline for consistency and source attribution**. The automated audit generates `site/documents/quality-audit.csv` so that unresolved items are visible. It is **not** a claim that every office was checked by telephone, or that every recorded address and clinician roster is current. That initial audited baseline had **14 clinic-published application pathways**, **14 regional reports**, **5 limited**, **6 waitlist**, **4 explicitly not accepting**, and **53 unknown**. 70 of those 96 records had at least one follow-up flag, frequently because no direct intake statement or recent independently verified office information is available.

Hard gates on every GitHub build now reject a first-party/program link pointing to a different organization's site, reject source/evidence mismatches, require a source-checked civic address for green status, and prevent unverified walk-in intake from being classified as ongoing primary-care attachment. The user-facing site labels regional sources as such instead of deceptively calling them clinic intake evidence. If a webpage is inaccessible, status is not changed to closed; uncertainty remains visible.

The optional automated publishing workflow cannot guarantee future site accuracy. Confirm with clinics before advising someone that a roster space exists. See `AUDIT_REPORT.md` for specific corrected cases.


## Current state and honest boundaries

- **Built and locally tested:** A standalone interactive clinic overview, one verified-status JSON database, generated DOCX/PDF directories, automated official-source change detection, broader news-based clinic discovery, optional AI review assistance, a review-notification workflow, and a manual approval form that republishes approved changes.
- **Hosting:** The independent project is published from the personal GitHub repository `shunterneo/regional-primary-care-availability`; check GitHub Actions for the latest successful scheduled run. Publishing an updated package or changing files does not itself confirm a successful deployment.
- **Current data (checked November 18, 2026):** `data/clinics.json` contains **223 clinic/service listings** and has `data_as_of: 2026-11-18`. This is an inventory count, not a count of clinics accepting patients or independently confirmed current intakes. The dated November 11 audit above is historical. The directory is not a completed CPSO/CNO audit; individual source dates, evidence and limitations apply, and public intake notices are not real-time availability guarantees.
- **Geography:** Existing records are grouped at *community-centre map markers*, not verified street-level clinic pins. New clinic records must use a verified public clinic coordinate to check the 75 km radius. Never supply patient addresses.
- **Automatic updates:** Automatic intake-status and permanent-closure publication remains **paused**; `.github/workflows/daily-site.yml` sets `AUTO_PUBLICATION_ENABLED: 'false'`. Source monitoring and discovery collect observations and review leads; explicitly reviewed manual updates can still be published. Two daily sightings alone do not authorize publication or independently corroborate intake. Third-party directories, news reports, and CPSO/CNO registration remain **review leads only**. See the safety-pause and hardening sections above and `DISCOVERY_OPERATIONS.md` for the source-by-source policy.
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
| `data/directory_queue.json`, `data/directory_state.json` | Candidate and change detection from curated regional physician lists |
| `data/registry_audit_queue.json` | Rotating CPSO/CNO human verification tasks; no bulk registry scraping |
| `DISCOVERY_OPERATIONS.md` | Independent discovery source matrix and evidence safeguards |
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
5. The scheduled workflow subsequently checks known clinic pages, curated regional physician directories, the Ontario public clinic registry, and rotating public news/municipal sources. It records new leads, runs tests, rebuilds the site and documents, and optionally creates **one GitHub Issue per run** with newly queued items for verification. If GitHub Issues is disabled, leads still remain in the JSON queues.
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
  --address 'VERIFIED PUBLIC CLINIC ADDRESS' --clinic-type MD --care-model unverified \
  --latitude 42.86 --longitude -80.72 --status unknown \
  --coordinate-source 'https://example.org/verified-public-office-coordinate' \
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
python tests/directory_discovery_fixture_test.py
python tests/approval_fixture_test.py
node tests/site_js_smoke.cjs
```

An additional Playwright browser visual smoke test is included for machines that have Chromium/Playwright installed. It is **not** required in GitHub Actions, where it would otherwise need separate browser installation.

## Privacy and evidence safeguards

The public website requests **no patient address**, uses **no external maps, scripts, tracking pixels, cookies, API calls, logins or form submissions**, and does not ask for names or medical information. Research workflows fetch only publicly listed clinic pages and public news feeds. The optional API sends only short **public clinic** excerpts, never personal health information. Clinic website links open external pages only when actively clicked. A public repository and public GitHub Issues must contain **no private client data or workplace records**.

This design avoids the earlier geocoding disclosure, but it is **not a PHIPA certification**. Any organization should apply its own policies before recommending the public resource in clinical practice. Public clinic contact data and intake information can become stale; the site indicates review dates and downgrades old claims to "Needs reconfirmation". **Last webpage fetch does not mean intake re-verification.**

## Known limitations and next QA priorities

- The website has successfully deployed using GitHub Actions, but each scheduled research source still needs live reliability monitoring.
- RSS news monitoring is a discovery supplement, **not** a systematic CPSO/CNO provider census or a guarantee of finding every intake opening.
- The 96 records have not all been independently reverified. Street-level clinic pin locations and any boundary-edge practices need an exact-address audit before the map can be treated as spatially complete.
- Patient acceptance can close between checks. Never promise that registration or attachment is guaranteed; clinic contact is the final confirmation.
- No unrestricted AI auto-publishing: intake changes require **explicit evidence and review**, to avoid accidental inaccurate referrals.

## Automated publication (November 11, 2026 update)

**The scheduled workflow now supports automatic, source-constrained publication.** New capabilities:

1. **Clinic-specific intake opening or closure:** `check_sources.py` and `auto_evidence.py` recognize only explicit first-person claims on a clinic's own HTTPS site, when that official evidence URL is assigned to one clinic and the page does not redirect to a different host. Vague registration links, regional lists, health team-wide statements, limited-eligibility language, contradictory lines, stale cached pages, news articles, and AI assessments do not qualify. A claim must be unchanged across **two different daily scans** before `auto_publish.py` changes its intake category. Successful scans establish a candidate first; a failed scan breaks the streak. Each change is recorded in `data/review_history.json` with source, excerpt, and both confirmation days.
2. **Permanent closure:** A clinic's official page must explicitly state that the clinic/location is **permanently closed**, with the same two-day confirmation. The record is **archived**, not deleted; archived offices disappear from the active map and downloadable directories, while their change history remains. A missing webpage or closed *intake* never archives the office. Temporary, generic or conflicting notices remain for human review.
3. **New government-listed primary-care sites:** `official_registry.py` reads Ontario Ministry of Health's official [MOHSERLO layer](https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open09/MapServer/26) (Open Government Licence – Ontario) for FHT, CHC and NP-led program locations, checking civic address and exact public site coordinates against the 75 km circle. Two different-day observations are required and existing sites are deduplicated. An additional site is shown as **government registry listed, intake unknown and operating status unconfirmed**—a government listing is *not* proof of an active clinic, a family doctor's roster or an accepting application. Other independent practices still depend on RSS discovery and manual verification.
4. **Safe publication:** The workflow commits automatic changes to `clinics.json` and the audit log, validates data, and builds/deploys the static map plus Word/PDF from the same records. Failures to reach sources do not automatically alter published statuses. Old positive intake claims still age into **Needs reconfirmation** unless a strong first-party confirmation is recorded.

The current 96-entry dataset is still a research baseline, not a completed CPSO/CNO census. This system cannot guarantee that every new clinic or intake change is detected. A practice may stop accepting patients between daily checks; always verify directly with the clinic before referring someone. No patient address or identifiable health information is processed or transmitted.

To suspend automation for an individual clinic, set `auto_updates_enabled: false` on that clinic's record; manual approved changes remain available. GitHub Pages and the original daily scanning workflow must be operational for this to run. No OpenAI API key is required for deterministic auto-publication.

## Distinguish ongoing primary care from walk-in services

Each record has a `care_model` independent of `status` and `clinic_type`:
`ongoing` (ongoing family physician or NP care), `both` (ongoing + walk-in), `walk_in_only` (episodic walk-in, NOT patient attachment) or `unverified`.

The site defaults to ongoing care and includes mixed practices with a conspicuous combined-service label; a walk-in-only practice is visible only when a walk-in or all-services filter is selected.
All green accepting status indicators mean applications for *ongoing care*, not ability to walk into a clinic. Records without verified ongoing care must keep `status=unknown`.

For combined practices, automatic publication of opening/closure of patient attachment requires an explicit family-practice/primary-care statement in the specific clinic's first-party evidence quotation. A generic “we accept new patients” phrase on a combined walk-in website is too ambiguous to auto-publish.

The 96-record dataset has six mixed-service sites classified using available public clinic information and **no identified walk-in-only sites**; this is an audit of existing listings, not a full census of independent walk-in-only clinics. Any newly discovered service must receive a care-model classification before publication; do not infer ongoing care from walk-in hours or appointment availability.


## Strict public-intake evidence policy (November 11, 2026)

**An advertised application form is not a confirmed available roster space.** The green "Applications advertised" label now requires:

1. An independently reviewed **clinic-owned** notice (not an external physician directory, news item, or generic team-wide announcement).
2. An explicit location-specific or named clinician/NP ongoing-care registration pathway. Walk-in registration never qualifies.
3. Evidence URL and clinic URL with matching hosts, a recorded evidence finding, review method, and date.
4. The clinic-specific public evidence must be **21 days old or newer**; otherwise the public site downgrades its *display* to **Needs reconfirmation**, without implying intake closed.
5. New automatic green changes require an unambiguous explicit ongoing family/NP care statement on the original clinic page on **two different days**. Conflicting statements, unresponsive pages, and regional-only claims are sent for review.

The `data/clinics.json` records now include `intake_verification` with `tier`, `scope`, `reviewed_on`, `method`, `source_url`, `finding`, `telephone_confirmed`, and `enrolment_guaranteed`. The policy lives in `scripts/evidence_policy.py`, is validated in `scripts/validate.py`, and used by the website, Word, and PDF generator. GitHub Actions runs `tests/evidence_policy_test.py` on each deployment.

The historical public-source audit (November 11, 2026) was used to classify 47 intake/waitlist leads. **No clinic was telephoned.** In a conservative cleanup, 3 general-program/municipal announcements are now leads rather than green; 2 Health Care Connect matching pathways were moved to limited intake. The current green count is **14 clinic-specific advertised application pathways**, not 14 verified new patient spots; other first-party notices conflict or identify only program-wide registration. Nine previously listed third-party leads remain amber; more current external announcements can affect these counts. The evidence audit will not be silently re-stamped when the website is rebuilt.

Manual intake approvals now require an exact clinic-published statement for ongoing care, an explicit location or named-clinician scope, and a clinic-owned HTTPS source. The approval form rejects a bare 'accepting' label when those controls aren't met. Staff/client addresses must never be entered. Provider capacity must still be confirmed directly before a referral is made.

### Versioned review-only source monitoring

The automatic intake writer remains paused. `review-context-v2` observations hash
complete meaningful raw HTML/PDF text before shortening review previews, together
with relevant link targets, HTML base resolution, media targets and visibility
attributes. This catches text beyond the old excerpt limits and changes to which
message may be shown. It does **not** render JavaScript, read text inside images,
fetch external assets, establish computed visibility, or verify actual capacity.
Raw-response hashes, byte counts and extraction versions support diagnosis;
public-form values and script contents are excluded from review text. Review
labels are tentative and cannot change clinic facts or intake-review dates.

The first successful scan after an extraction-version upgrade creates a new
baseline without inventing a content-change alert. The previous source hash and
version are retained. Later recurring content transitions can create new review
items even when an earlier item for the same text was resolved. Unchanged scans
do not generate repeat items. A source failure preserves its last good review
snapshot but breaks the independent automatic-publication observation chain.

Directory observations use `directory-v3` full-content fingerprints rather than
440-character previews. A readable news index with zero relevant articles is a
successful zero-result check, and rolling news expiry is not a clinic removal.
Challenges, login pages, empty/JavaScript shells, unsupported layouts and partial
extractions preserve prior entries and report a typed failure. Parser or source
configuration changes establish a new baseline rather than false removals.
Directory entries and content changes remain research leads, never confirmation
that a practice exists within the boundary or accepts ongoing patients.

These safeguards do not solve blocked sources or guarantee complete monitoring.
JavaScript-only clinic pages still need a separately reviewed rendered adapter;
TLS and access failures are not bypassed. A successful build or HTTP 200 response
alone is not evidence of a successful intake check.

### Stage-complete health and no-publication recovery

`monitor_health.current()` reports clinic evidence, configured discovery pages,
the latest rotating RSS query batch, all configured directories, Ontario registry
health, and separate human-only professional-register audit metadata. Optional AI
triage is not a required health stage. Counts may overlap across evidence and
discovery URLs; do not sum them as unique sources or clinics. Latest-batch RSS
success does not prove every configured query was recently checked.

Missing, malformed, future-dated, inconsistent or source-configuration-mismatched
observations cannot earn a blanket healthy result. Date-only clocks expose an age
interval; an interval crossing the 36-hour threshold is uncertain, not green.
The legacy `assess()` evidence-only interface remains available, but whole-system
health uses `assess_all()`. Detailed attention lists are bounded for GitHub issue
size, with explicit omission counts; aggregate counts and problems are retained.

Directory fetches permit one bounded normal retry for transient network/server
failure. Access denials and TLS failures are not retried or bypassed. Long or
invalid Retry-After instructions defer the check instead of overriding the server.
A known empty verification shell is recorded as an access challenge, not evidence.

The source-recovery workflow checks both sources and directories and persists only
source/directory observations and their review queues. It explicitly keeps the
status writer off, never invokes a clinic/profile publisher or external outreach,
and asserts clinic facts/history/registry approvals remain unchanged. It saves
state and diagnostic artifacts before failing visibly when coverage is incomplete.
A red recovery result can therefore mean remaining website failures, not a lost
scan. This recovery workflow does not deploy the site; the next site build exposes
its saved observations. A green deployment alone does not prove healthy monitoring.

### Read-only review inbox

The directory links to `review.html`, a build-time view of all four pending review
queues, unmatched government profile observations and current source/directory
failures. It shows source links, observed excerpts, repair/review steps and stage
health. It is not an approval interface and never writes queues or clinic facts.
Existing authenticated publication and repository review procedures still apply.
Registry observation counts are not counts of missing clinics; same-address
matches are comparison leads, not identity proof. Failed-check counts are not
unique-office counts. Source content is escaped, projected through an allowlist,
and linked only via validated public HTTPS URLs. No script, form, analytics or
remote assets are used by the review page. New observations appear after a site
build, not instantly. A failed input is shown as incomplete, never silently green.
