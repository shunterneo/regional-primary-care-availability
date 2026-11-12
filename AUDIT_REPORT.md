# Regional Primary Care Availability Hub — targeted integrity audit

**Assessment date:** November 11, 2026 · **Centre:** 96 Tillson Avenue, Tillsonburg · **Area:** 75 km straight-line radius.

## Scope and conclusions

This audit checked the structure, source links, evidence classification, and publicly listed addresses of the current **96 clinic / service locations**. It did **not** conduct phone calls with practices, exhaustively compare every Ontario physician and nurse practitioner registration, or confirm that advertised application forms translate into current roster spaces. The public map still uses town-centre pins and cannot be used as a precise clinic-location or driving-distance map.

| Published intake classification | Office / service records |
|---|---:|
| Clinic-published application pathway (not guaranteed attachment) | 14 |
| Regional / third-party intake report, contact clinic to confirm | 14 |
| Restricted / limited intake | 5 |
| Waitlist | 6 |
| Explicitly not accepting per cited public evidence | 4 |
| Unknown, conflicting, or unsupported current intake | 53 |
| **Total** | **96** |

**Quality follow-up:** 70/96 records have at least one follow-up flag (overlap permitted); 67/96 have a recorded independently checked public office address source; **29 still require more source-level address reconfirmation**. **Three** records have no usable office phone. The fact that a record has an address source is **not** a guarantee that its street-level geocoding or provider roster is independently verified.

## Corrections and new discovery in this pass

1. **Langs North Dumfries CHC, Ayr:** Corrected former 2938 Greenfield Road to official **2958 Greenfield Road** and updated phone to **519-632-1229**. Source: https://www.langs.org/locations-hours.
2. **London Family Health Team — Beaverbrook and Stoney Creek:** Official 2026-08-26 intake announcement conflicts with the organization's general locations page indicating no new patients. Both records set to **unknown/conflicting**, and automatic promotion disabled until verified directly. Sources: https://londonfht.ca/looking-for-a-primary-care-provider-apply-here-now/ and https://londonfht.ca/our-locations/.
3. **London InterCommunity Health Centre — Argyle:** Added a missing third primary-care site at **1700 Dundas Street Unit 1, London; 519-660-5853**. Intake unknown until site-specific confirmation. Source: https://lihc.on.ca/locations-and-hours-of-services/.
4. **London InterCommunity Health Centre — Huron:** Corrected site phone to **519-659-6399**, separate from the Dundas site contact. Source: https://lihc.on.ca/locations-and-hours-of-services/.
5. **Saginaw Medical Centre, Cambridge:** Corrected listing to **525 Saginaw Parkway, Unit A2, 226-666-0345**. This is office verification, **not** proof that Dr. Bhatia currently accepts new patients. Source: https://www.saginawmedicalcentre.com/about.
6. **Dr. Clara Obanor, Brantford:** Corrected practice unit to **250 King George Road, Unit 2** and contact from public CPSO record; this does not confirm intake. Source: https://register.cpso.on.ca/physician-info/?cpsonum=155642.
7. **Dr. Sherif Mikhail, Cambridge:** Corrected suite format to **350 Conestoga Boulevard, Unit B7-A**, with clinic-owned contact link. Source: https://www.sherifmikhail.ca/.
8. **Dr. Festus Anochie, London:** Corrected suite detail to **440 Boler Road, Suite 200** from public CPSO registration. Source: https://register.cpso.on.ca/physician-info/?cpsonum=145987.
9. **Thames Valley FHT sites:** Independently cross-checked numerous public office addresses against https://thamesvalleyfht.ca/locations/ and corrected several FHT *program* contact numbers; those numbers do not automatically reach a family's doctor or indicate an open roster.
10. **Elmdale building-wide registration:** Reclassified the entry as an **unverified care model** and intake **unknown** because a multi-tenant building registration notice cannot identify a confirmed ongoing family-medicine practice.

11. **Talbot Family Health, St. Thomas:** Original clinic website explicitly says **not accepting new patients**. Added clinic phone 226-210-3773 and confirmed Suite 1, 294 Talbot Street. This is an intake status, **not a permanent closure**. Source: https://talbothealth.ca/.
12. **Coronation Family Physicians, Cambridge; TMC+ St. Thomas; London FHT Medway:** Added public office/team contact numbers and Coronation Suite 201. Source numbers are not proof of available doctor roster spaces. Sources: https://www.coronationfamilyphysicians.ca/, https://thompsonmedical.ca/contact/, https://londonfht.ca/our-locations/.

## QA safeguards added

- `scripts/validate.py` now blocks green accepting statuses that carry unresolved first-party conflicts or that claim an independently verified street address without a supporting source URL.
- `scripts/evidence_policy.py` no longer qualifies accepting status while an unresolved conflict flag exists.
- `scripts/auto_publish.py` skips conflicting cases and respects a manual override preventing automatic status promotion.
- `scripts/audit_inventory.py` emits distinct address source/checked-date/phone-note columns and flags unresolved first-party contradictions.
- Regression tests check the Langs address, Saginaw and LIHC phone numbers, both London FHT conflicts, and the missing Argyle site; previously fixed cross-organization evidence links remain covered by tests.
- The data and generated Word/PDF/map outputs contain **public clinic information only**, never client addresses.

## Important unfinished work — do not describe as fully verified

- **29 clinic addresses** lack sufficient recorded independent public-source verification. Even the other 65 do not yet have individually verified building coordinates or routing information.
- **Three office contact numbers** remain absent. Other published phone numbers may connect to a regional FHT coordinator rather than the patient's specific physician.
- **14 regional intake reports** still lack unambiguous clinic-specific current enrolment confirmation; 53 records have unknown/conflicting intake.
- **Physician-by-physician and nurse-practitioner-by-nurse-practitioner census** against CPSO/CNO is not complete, so additional practices may exist.
- **Automated scheduled research quality** needs real-run evidence, separate from successful page deployments or simulated tests. A successful build does not prove external sites were searched successfully.
- Site-level acceptance and patient attachment are **not** established by online registration forms. Call a clinic directly before giving a definitive referral.
