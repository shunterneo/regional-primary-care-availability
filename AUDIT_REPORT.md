# Primary Care Availability Hub — quality audit

**Audit dated:** November 11, 2026 (America/Toronto)

## Scope and honesty of findings

All **95 records** in the published database were checked programmatically for schema validity, source/organization attribution, green-status eligibility, care-model versus walk-in distinction, civic address completeness, duplicate record keys and mismatched evidence URLs. Targeted public-web checks independently inspected key intake and practice pages, especially records that were advertised as open or used another organization as evidence. **This is not a 95-clinic telephone audit or a complete CPSO/CNO physician census.**

Baseline display classifications after corrections:

| Category | Records |
|---|---:|
| Clinic-published application pathways (not guaranteed enrolment) | 16 |
| Regional/secondary reported opportunities | 15 |
| Restricted/limited intake | 5 |
| Waitlist | 6 |
| Explicitly not accepting (public reports) | 3 |
| No established intake status | 50 |
| **Total** | **95** |

**79 records contain at least one follow-up flag**, which includes expected categories such as no direct intake evidence, missing telephone number, or office location needing independent reconfirmation. A flag is **not** proof of an incorrect address or closed practice. The underlying file `site/documents/quality-audit.csv` lists every record and the specific flags. The follow-up count can change whenever records or data quality improve.

## Corrections made

- **Woodstock Thames Valley FHT:** Fixed the wrong "Intake evidence" link to Oxford County NPLC. Direct registration now uses Thames Valley FHT's own attachment-team page and intake phone **519-473-0530 ext. 2197**. The source is a **regional NP-attachment pathway**, not verification of an available family physician roster at the Woodstock building.
- **Oxfordia (Woodstock):** The clinic website now points to **oxfordiamedical.com**. The City of Woodstock physician-recruitment announcement remains clearly identified as secondary evidence, not the clinic's own intake verification.
- **Active Care Medical Centre (London):** Replaced the placeholder street location with the clinic-published **1807 Wonderland Road North, Suite 201**; named the specifically accepting physicians.
- **Viva Medical Clinic (London):** Corrected the telephone listing for **Dr. Osita Ohaeto to 226-289-7231**, rather than using another physician's phone number from the same centre.
- **Elmdale Health Centre (St. Thomas):** Downgraded the building-wide registration notice. A multi-tenant building form does not identify a specific physician's available roster space.
- **Oxford County NPLC — Tillsonburg:** Distinguished regional NP applications from immediate, location-specific assignment. The permanent Tillsonburg Unit 14 location is described as opening in early 2027, while existing temporary services continue at Unit 12. This remains a referral/application lead, not a verified new patient space at a specific site.
- **Old South FHO (London):** Downgraded the intake claim because the original clinic registration page could not be independently retrieved. London's medical association provides a directory lead for Drs Spence and Goosheh; clinic confirmation remains outstanding.
- **Valleyview Medical Centre, Brantford:** Replaced generic homepage evidence with the correct **Colborne** and **Lynden** clinic-specific family-practice registration paths, separate from walk-in booking.
- **Greenwich Medical Centre:** Flagged the clinic's inconsistent telephone numbers rather than selecting one as definitively confirmed.

## Permanent safeguards added

1. Every build validates the clinic's **claimed first-party evidence domain against its own website**, including program-wide referrals. The exact error the user found now **fails validation** instead of displaying an apparently valid intake link.
2. Green requires a **recent, clinic-specific published ongoing-care application notice**, a properly recorded source and a checked physical street address. A generic booking button is not enough.
3. Program-level intake, directory-only reports, waitlists, unknown status, walk-in care, and office closures are kept distinct. No error or missing page automatically means "not accepting" or "closed".
4. Public evidence review dates, record-edit dates and source URLs are distinct. All records remain explicitly **not telephone verified** unless an actual documented verification process exists.
5. The user-facing website provides a **downloadable 95-record QA CSV**, not just a green badge, and the Word/PDF directory regenerates from the same data.
6. The daily workflow runs new structural-audit regression tests. A cross-organization evidence link or unsupported green classification blocks deployment.

## Remaining work

The structural QA is complete, but 79 records have follow-up flags. A systematic physician-by-physician CPSO/CNO audit, direct phone confirmation when feasible, and address-level geographic checking remain outstanding. The public map displays approximate *community-centre* markers rather than verified building pins. Ongoing online monitoring is a supplement, not a substitute for contacting clinics before making referrals.
