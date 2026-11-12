> Superseded in part by [continued audit and site editing/export update](continued-audit-and-site-update-2026-11-12.md). The report below describes the earlier 122-record pass.

# Completion audit — 12 November 2026 UTC

## Result

The public-source and operational pass is complete: 25 missing records added, 122 total records across 33 communities, Joseph Street relocation corrected, Westmount closure statement corrected, regional/clinic conflicts retained, and real monitoring exercised. This is not a completed telephone verification or exhaustive practitioner census.

Current categories: 15 applications advertised, 20 regional reports, 8 limited intake, 15 waitlists, 14 not accepting, 50 unknown. Unknown increased because newly identified offices without intake evidence were added. All 122 have a dated public-review outcome. Three address claims remain unresolved; four records have no direct office number. Structural checks report zero critical failures, with 77 records retaining informational follow-up flags.

## Plan outcomes

| Work | Outcome |
|---|---|
| Existing public-source review | All original 97 have dated outcomes from this and the previous pass; further checks corrected Westmount and Joseph Street. |
| Address conflicts | Rechecked Oxfordia, Colborne/Niaz and future Qamar practice; no reliable evidence resolves all discrepancies. Flags retained. |
| Regional coverage | Compared LDAM, BCHS, Doctors4Cambridge, TVFHT, CFFM, PrimaCare, Haldimand FHT, SOAHAC, Woolwich and 40 government records. Added 25 records. |
| Government record review | All 40 have individual dispositions in the linked JSON. 34 matched, five excluded or withheld as non-attachment program sites, one Caledonia office address unresolved. |
| Discovery leads | Nine directory leads matched; header rejected; two walk-in leads deferred; one new named physician lead uncorroborated. Five irrelevant/out-of-region news leads rejected. |
| Monitoring | Real GitHub run retrieved 55/74 source URLs, 3/6 directories, 40 registry records. Pipeline and deployment succeeded; retrieval failures remain explicit. |
| Safeguards | Registry auto-add now requires independent office approval; table headers excluded; phone caveats and unverified-address notices visible; UTC dates prevent same-day false staleness. |
| Validation | Database validation, seven Python fixture suites and JavaScript filter/map checks passed. 122 records, 33 community markers. |

## Material corrections

- CFFM Joseph Street is closed and moved to **16 Andrew Street**, phone **519-578-2100**. [Relocation](https://family-medicine.ca/joseph-street-relocation/) and [current location](https://family-medicine.ca/andrew-street/).
- Westmount FAQ explicitly says no new patients. [Clinic FAQ](https://www.westmountfamilyphysicians.ca/faq).
- Forbes Park is present in a regional accepting directory but its own page says no physicians accepting. The record uses the clinic statement and retains a conflict flag. [Clinic statement](https://www.forbesparkmedical.com/new-patients).
- Two Rivers offers a team waitlist. Its named Callaghan roster form is for people already contacted, not an unrestricted application. [Waitlist](https://tworiversfht.ca/patient-centre/how-to-become-a-patient/).
- SOAHAC advertises new clients in Cambridge, Owen Sound and Newbury; that banner is not applied to London or Chippewa of the Thames. [Cambridge clinic](https://www.soahac.on.ca/locations/waterloo-wellington).
- TVFHT's government-listed **1385 North Routledge Park** address is an administrative office, explicitly not a medical clinic. It was excluded. [Office statement](https://thamesvalleyfht.ca/locations/central-office/).

- Victoria Family Medical Centre direct number corrected to **519-433-8424** from [LHSC](https://www.lhsc.on.ca/patients-visitors/victoria-family-medical-centre).

## Added records

| ID | Office | Intake category | Source |
|---|---|---|---|
| c098 | Dr. Martin Schuster — Family Practice (Cambridge) | reported | [Evidence](https://www.doctors4cambridge.com/contact.htm) |
| c099 | Forbes Park Medical Centre (Cambridge) | not_accepting | [Evidence](https://www.forbesparkmedical.com/new-patients) |
| c100 | Two Rivers FHT — Hespeler Medical Clinic (Cambridge) | waitlist | [Evidence](https://tworiversfht.ca/patient-centre/how-to-become-a-patient/) |
| c101 | Two Rivers FHT — HealthLink Family Practice (Cambridge) | waitlist | [Evidence](https://tworiversfht.ca/patient-centre/how-to-become-a-patient/) |
| c102 | Centre for Family Medicine FHT — Victoria Street (Kitchener) | not_accepting | [Evidence](https://family-medicine.ca/patient-resources/frequently-asked-questions/) |
| c103 | Centre for Family Medicine FHT — University Gates (Waterloo) | not_accepting | [Evidence](https://family-medicine.ca/patient-resources/frequently-asked-questions/) |
| c104 | Centre for Family Medicine FHT — The Boardwalk (Waterloo) | not_accepting | [Evidence](https://family-medicine.ca/patient-resources/frequently-asked-questions/) |
| c105 | Centre for Family Medicine FHT — Wellesley (Wellesley) | not_accepting | [Evidence](https://family-medicine.ca/patient-resources/frequently-asked-questions/) |
| c106 | PrimaCare Community FHT — Paris (Paris) | unknown | [Evidence](https://www.pccfht.ca/contacts/) |
| c107 | PrimaCare — Dr. Alice Wang (Ayr) | unknown | [Evidence](https://www.pccfht.ca/contacts/) |
| c108 | St. George Medical Centre (St. George) | waitlist | [Evidence](https://stgeorgemedical.ca/) |
| c109 | Central Community Health Centre (St. Thomas) | unknown | [Evidence](https://centralchc.com/) |
| c110 | Happy Valley Family Health Team (St. Marys) | not_accepting | [Evidence](https://happyvalleyfht.ca/about-us/) |
| c111 | Six Nations Primary Care / Family Health Team (Ohsweken) | waitlist | [Evidence](https://www.snhs.ca/family-and-community-care/primary-care-family-health-team/) |
| c112 | Haldimand FHT — Hagersville (Hagersville) | limited | [Evidence](https://haldimandfht.ca/) |
| c113 | Argyle Medical Clinic — Dr. Chukwuemeka Ogbunando (Caledonia) | reported | [Evidence](https://haldimandfht.ca/affiliated-physicians/) |
| c114 | Okechukwu Medicine (Caledonia) | unknown | [Evidence](https://haldimandfht.ca/affiliated-physicians/) |
| c115 | Caledonia Family Clinic — Dr. Nicolaas Cloete (Caledonia) | unknown | [Evidence](https://haldimandfht.ca/affiliated-physicians/) |
| c116 | Takach Medicine — Dr. Sarah Takach (Ohsweken) | unknown | [Evidence](https://haldimandfht.ca/affiliated-physicians/) |
| c117 | SOAHAC — London (London) | unknown | [Evidence](https://www.soahac.on.ca/locations/london) |
| c118 | SOAHAC — Chippewa of the Thames (Muncey) | unknown | [Evidence](https://www.soahac.on.ca/locations/chippewa-of-the-thames) |
| c119 | SOAHAC — Waterloo Wellington (Cambridge) | limited | [Evidence](https://www.soahac.on.ca/locations/waterloo-wellington) |
| c120 | Woolwich Community Health Centre — Wellesley (Wellesley) | waitlist | [Evidence](https://wchc.on.ca/registered-client-services/accepting-new-patients/) |
| c121 | Woolwich Community Health Centre — New Hamburg (New Hamburg) | waitlist | [Evidence](https://wchc.on.ca/registered-client-services/accepting-new-patients/) |
| c122 | Nith Valley Family Practice (New Hamburg) | unknown | [Evidence](https://www.nvfp.ca/) |

## Remaining external dependencies

These are not silently marked complete:

- **Current capacity:** 50 unknown records need a current clinic statement or direct response. No clinic was contacted and no patient form submitted.
- **Three disputed addresses:** Oxfordia Suite 300 remains uncorroborated; Colborne/Niaz differs from CPSO's Southdale address; Qamar's January 2027 practice differs from the current register. Do not travel without confirmation.
- **Two new discovery questions:** the government Caledonia address and the live-run LDAM entry for Dr. Gerald Okafor/Baseline require further corroboration. They are not presented as confirmed openings.
- **Comprehensiveness:** CPSO/CNO enumeration is not completed. The government dataset includes only certain program types and cannot substitute for every individual family practice.
- **Geography:** 22 existing street addresses were manually matched to government planning points. The public map still intentionally shows community markers, not entrance-level clinic pins. The 75 km boundary is approximate for offices without verified coordinates.
- **Blocked sources:** 19/74 automatic requests failed; chiefly 403 responses from TVFHT/STAR, plus a Healthline certificate failure. Manual indexed-source review and automatic live fetch are different evidence channels. Certificate validation was not disabled and access controls were not bypassed.
- **Visual browser check:** offline JavaScript tests passed; no successful interactive browser rendering check is claimed in this environment.

## Monitoring verification after expansion

[Run 43151342754](https://github.com/shunterneo/regional-primary-care-availability/actions/runs/43151342754) completed all checks and deployed the expanded site. It retrieved 66 of 87 source URLs (21 failures). Seven CPSO alerts reflected retrieval-clock text in retained excerpts; no intake changes were inferred. The monitor now normalizes only that clock, with a regression test preserving actual practice-text changes. A table-header removal alert was rejected.

The new TVFHT article was reviewed: [two future clinics in London and Lambeth are planned](https://thamesvalleyfht.ca/2026/11/11/nurse-practitioner-week-2026/), but no opening dates or street addresses are given. This remains a deferred lead, not an operating clinic listing.

## Evidence files

- [40 government dispositions](../data/registry_review_2026-11-12.json)
- [54 records with concrete confirmation questions](../data/confirmation_followup.json)
- [Directory lead dispositions](../data/directory_queue.json)
- [News lead dispositions](../data/discovery_queue.json)
- [Live-run source results](../data/source_state.json)
- [Live monitoring run and deployment](https://github.com/shunterneo/regional-primary-care-availability/actions/runs/43150063574)

The plan's public-review and technical tasks are complete. External confirmations, exhaustive enumeration, and precise geocoding remain open; this report must not be represented as proof that all regional offices or roster spaces have been verified.

## Final live verification

[Run 43151763614](https://github.com/shunterneo/regional-primary-care-availability/actions/runs/43151763614) passed all seven Python suites and JavaScript checks, regenerated the 122-record site and downloads, and deployed successfully. The live scan retrieved 68 of 89 URLs, recorded 21 failures and queued zero new source changes. Source-change and news queues have no unreviewed items; the uncorroborated Baseline physician lead remains pending and deferred future/walk-in leads remain retained. The PDF has 21 pages; PDF/Word text checks confirmed the relocation, Nith Valley addition and corrected Victoria phone. Unknown records now say public clinic source reviewed, current intake not confirmed.
