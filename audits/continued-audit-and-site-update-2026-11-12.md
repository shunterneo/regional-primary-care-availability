# Continued audit and site update — 12 November 2026 UTC

## Delivered changes

- **Tillsonburg Oxford County NPLC:** corrected from a regional lead to applications advertised. The live Ocean form linked by the clinic explicitly identifies **Tillsonburg site only**. This decisive location evidence was missed in the earlier review. Application eligibility and non-guaranteed enrolment remain explicit. The clinic's future permanent Unit 14 opening is not a reason to hide current applications at temporary Unit 12.
- **Ingersoll OCNPLC:** limited capacity remains the clinic's wording, but its linked form is Tillsonburg-only. The listing now directs Ingersoll applicants to call for the correct route.
- **11 missing records:** c123–c133, including Baseline/Dr Gerald Okafor, Courtland Medical Clinic in Kitchener, two Port Dover practices, two separately contacted Port Stanley physicians, two Dorchester offices, Thorndale, Synergy family medicine, and the independent Burford physician. 133 total records across 38 communities.
- **Baseline lead resolved:** live CPSO search confirms Gerald Obiora Okafor, 278541, at 25 Base Line Road West. LDAM independently provides the registration number. Published as regional reported intake, not first-party verified capacity.
- **Mapping:** 100 records now have sourced planning or address points. 33 retain visibly approximate community locations. Added a clinic-location view, community zoom and source links. Rejected street-only matches, unrelated retail POIs and materially separated address candidates. The centre at 96 Tillson Avenue is now sourced to its building point.
- **Safe editing:** site editor with before/after review, evidence fields, acknowledgement and typed clinic ID. No live write occurs in the public page. A repository writer completes the existing GitHub workflow with the edit code and `PUBLISH cNNN`. Server-side validation rejects stale drafts, unsupported fields, invalid evidence and unsubstantiated advertised intake. Address changes discard old coordinates. History retains field-level changes. No credentials are stored in the site.
- **Download chooser:** PDF, genuine DOCX and CSV, for all records, current filters or manually selected clinics. Includes intake notes, review dates and source links. PDF embeds a licensed font; Word is OOXML. CSV guards spreadsheet formula interpretation. Existing full audit remains available separately.

## Evidence

- [OCNPLC registration](https://www.ocnplc.ca/patient-information/new-patients/)
- [Clinic-linked live Tillsonburg application](https://ocean.cognisantmd.com/eRequest/d5e47774-8987-4e5a-b069-f8bbf23fd9d9) — opening instructions reviewed without entering or submitting patient data.
- [LDAM](https://www.ldam.ca/find-a-doctor) and [CPSO 278541](https://register.cpso.on.ca/physician-info/?cpsonum=278541)
- [Courtland Medical Clinic](https://courtlandclinic.com/)
- Other sources are attached to each new clinic record.
- [Geocoding response cache](geocoding/nominatim-2026-11-12.json) and [review decisions](geocoding/decisions-2026-11-12.json). One-time public-office lookup; no patient addresses. OpenStreetMap data is ODbL, with visible attribution. Government planning points retain their original provenance.

## Validation

Database validation: 133 records, zero errors. Offline monitor, discovery, directory, auto-publication, evidence, inventory, approval and site-edit tests cover failure handling and publishing safeguards. JavaScript checks exercise filters, both map views, selection/export scope, editor review and confirmation. Generated subset PDF and DOCX were parsed successfully; subset PDF visually inspected after embedding the font. The full custom PDF contains 29 pages. Deployment and browser outcomes are recorded below.

## What remains externally unconfirmed

59 records have no current supported intake outcome. Three addresses remain disputed. 64 records have concrete follow-up questions, including missing contact numbers and Ingersoll's form route. See [confirmation follow-up](../data/confirmation_followup.json).

This pass does **not** establish an exhaustive CPSO/CNO census. Live register searches resolved the named Baseline lead and reviewed Tillsonburg/Dorchester results; they also demonstrate why a family-medicine qualification or hospital business address alone does not prove a community roster. The Tillsonburg search returned 25 records over three pages (default English filter); most additional entries were hospital, emergency or long-term-care locations. Dorchester results included an out-of-country same-name locality, which was excluded. Hamza Aman was found as CPSO 277205, but his listed Brampton address does not resolve the Oxfordia Woodstock suite claim.

Additional Thames River FHO pages contain inconsistent addresses for Niesner/Hommel; these were not promoted without reconciliation. Published clinic capacity cannot be inferred from an absent notice. No clinic was telephoned or emailed. A public-source audit may finish with explicit unknown outcomes; this must not be represented as confirmed live availability at every regional practice.

## Published verification

Commit `2e89e7ce7aafe460071a90b3162bc06c0e7e2795` deployed successfully in [run 43155740494](https://github.com/shunterneo/regional-primary-care-availability/actions/runs/43155740494). All eight Python suites and JavaScript smoke checks passed. The live monitoring pass fetched 77 of 98 source URLs; 21 failed to fetch and therefore were not freshly verified by that run. It queued no source changes. Discovery completed 16 queries with no new leads. These automated results do not replace manual verification or resolve unknown capacity.

Published browser checks confirmed 133 listings, 17 advertised ongoing-care application opportunities, and 20 regional leads. The Tillsonburg NPLC card shows the corrected application status and direct form link. All-record PDF and single-selected-clinic Word and CSV downloads completed. The edit review correctly displayed old/new phone values, kept approval disabled until acknowledgement and the exact clinic ID, and discarded the test draft without changing the real telephone number. No test edit was published. Tillsonburg clinic-map filtering displayed two sourced and three approximate locations, matching its five filtered listings. Desktop layout was visually inspected; no separate mobile-browser test was performed.
