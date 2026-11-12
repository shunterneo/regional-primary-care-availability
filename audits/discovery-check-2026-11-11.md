# Independent discovery check — 2026-11-11

Scope: public-source spot check against existing 97-record directory; **not** a completed 75-km exhaustive census or telephone verification.

## Findings

- **Dr Hamza Aman, Oxfordia (c012)** — November 10 Heart FM report independently corroborates accepting new patients. Existing City of Woodstock announcement already supports intake pathway. Suite 300 still not independently verified. https://www.heartfm.ca/news/local-news/new-family-doctor-now-accepting-patients/
- **Oxford County NPLC Tillsonburg (c011)** — Clinic's current new-patient page says applications are open, not guaranteed; Ingersoll limited capacity, Woodstock residents not currently prioritized; future Tillsonburg Unit 14 opening early 2027. Existing record correctly distinguishes temporary Unit 12. https://www.ocnplc.ca/patient-information/new-patients/
- **London FHT Beaverbrook and Stoney Creek (c004,c005)** — August 26 clinic notice invites applications at both locations, but does not guarantee attachment. Existing unknown/conflicting status should not be promoted without resolving conflicting locations page. https://londonfht.ca/looking-for-a-primary-care-provider-apply-here-now/
- **Brantford regional intake (c016,c017,c018,c019,c020)** — Brant Community Healthcare System lists Avenue/Desai, Bonavista, Obanor, and both Valleyview sites. This is regional-source evidence only; no telephone-confirmed capacity. https://www.bchsys.org/patients-and-visitors/finding-a-doctor/
- **London regional intake (c029,c030,c031,c032,c033,c034,c035,c036,c037,c047)** — London & District Academy of Medicine lists 12 opportunities, including Dr Qamar's *future* January 2027 waitlist. These appear represented in existing inventory, but direct intake remains unconfirmed. https://www.ldam.ca/find-a-doctor
- **Thames Valley FHT** — Organization says its NP clinics in London, Middlesex, Elgin and Oxford accept new patients. Site-specific capacity requires follow-up. https://thamesvalleyfht.ca/
- **Tillsonburg Family Physicians (c089)** — Southwest Healthline entry updated May 21, 2026 supports address and phone, not accepting-new-patient status. https://www.southwesthealthline.ca/displayService.aspx?id=187735
- **Health Zone NPLC (c064)** — Existing database has 230 Victoria Street Suite 230; a third-party business listing suggests 1057 Southdale Road East. Do not overwrite with a directory claim; verify current clinic-owned contact page and office before changing.

## Quality warnings

- Physician register does **not** report new-patient intake: https://register.cpso.on.ca/
- Generic scraped doctor directories may label specialist/hospital-only physicians as accepting primary-care patients. Exclude such claims unless independently supported.
- This pass did not identify a **confirmed** new eligible primary-care opening absent from the database. That is not proof the inventory is complete.
- No clinic telephone calls, comprehensive CPSO/CNO roster enumeration, precise geocoding, or successful GitHub Actions deployment confirmation occurred in this pass.

## Next verification queue

1. Resolve Health Zone's conflicting street address against its own contact page.
2. Resolve three previously flagged address/provider-location discrepancies: Oxfordia suite, Dr Niaz, Dr Qamar.
3. Check every remaining unknown-intake record against clinic-owned pages and regional notices.
4. Expand discovery to individual physician and NP registries and local recruitment announcements; distinguish provider existence from intake.
5. Verify the latest GitHub Actions run and site deployment separately from source commits.
