# Regional-lead duplication audit, 18 November 2026

Scope: all 11 `reported` regional-lead records compared with all 223 published records. Dataset checked again at separation commit `e2f371f12eab6ef863a7bc27031b1ea660d80b7b`: 223 unique IDs; all 11 regional-lead identity/address/provider/phone fields unchanged. Read-only; no deletion or repository edit.

## Findings

| Record | Result |
|---|---|
| c017 Bonavista Medical Centre | No second record matching this practice, named providers, address or phone. |
| c018 Dr. Clara Obanor | No second record matching physician, address or phone. Other King/George names are unrelated. |
| c022 Dr. Sherif Mikhail | Shares 350 Conestoga Boulevard with c100/c101, but B7A is distinct from Two Rivers' B12/B10 offices; separate phones. Retain. |
| c025 Dr. Hisham Ghali / Shepherd | Shares clinic name and 512 Coronation Boulevard with c217 Dr. Ezzat Beshay. Distinct physicians, phones and intake routes. Do not delete either opportunity. Could group visually under Shepherd with separate physician rows. |
| c030 Dr. Festus Anochie | No second record matching physician, address or phone. |
| c031 Dundas Medical Clinic | No second record matching address or phone. LIHC Dundas is a different address and organization. |
| c035 Serenity Medical Centre | No second record matching practice, address or phone. |
| c092 Waterford Family Health Center | No second record matching practice, named providers, address or phone. |
| c098 Dr. Martin Schuster | No second record matching physician, address or phone. |
| c113 Dr. Ogbunando / Argyle | Shares street address with c206 Haldimand Medical Clinic Unit 2, but sources describe different physician teams, phones and intake routes. Retain. |
| c123 Dr. Gerald Okafor / Baseline | No second record matching physician, address or registration phone. |

No genuine duplicate provider record was established. This is a bounded identity audit of the regional-lead set, not a claim that the entire directory has no possible duplicates or that intake is freshly confirmed.

## Current external evidence for the plausible overlaps

- Doctors4Cambridge: https://www.doctors4cambridge.com/contact.htm names Ghali at 512 Coronation Boulevard, 519-623-7878, and Mikhail at 350 Conestoga B7A, 519-740-1700. It separately names Hespeler/Two Rivers Unit 12, 519-629-4615. Regional source, not clinic capacity confirmation.
- Dr. Beshay's own page: https://www.drbeshay.ca/newpatients names Beshay at Shepherd, 512 Coronation Boulevard, 519-622-0028, and an office-submitted waitlist form. Distinct from Ghali's regional report.
- Two Rivers indexed official contact page https://tworiversfht.ca/contact/contact-us/ identifies B10/B12/B15; direct retrieval returned 403 in this check. Supporting existing structured records and Healthline describe HealthLink B10 and Hespeler B12. No claim of newly rendered direct-page verification.
- Haldimand FHT https://haldimandfht.ca/affiliated-physicians/ names Ogbunando with Gunning, Olaluwoye, Oyerinde and Xu at Argyle Medical Clinic; Ogbunando phone 905-765-5886.
- Haldimand Medical Clinic https://healthycaledonia.ca/about lists Stephen Tytus, Richard Tytus, Laura Rusu and other team members. https://healthycaledonia.ca/contact identifies Unit 2, 250 Argyle St N and 289-210-7090. Not the same provider/intake entry as c113.

## Recommendation

Use one listing per verified provider/practice intake pathway and retain its evidence links. Do not delete a record merely because its evidence came from a regional directory. If reducing repeated visual locations, group Shepherd's two physicians under one location while preserving both status labels, contacts and routes. Keep separate suites/organizations separate. Rename confusing public labels independently from deduplication. No changes made while service separation is publishing.
