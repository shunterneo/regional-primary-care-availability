# Expanded practice-discovery audit — November 12, 2026

## Result

Added 36 previously unrepresented practice/service records, bringing the public inventory from 167 to 203 across 41 communities. These are records, not 36 newly opened clinics or 36 confirmed openings. Expanded the existing Victoria Soo location into the WELL London/HealthPark clinic record rather than duplicating it. Clarified Forest City allied-health versus physician contact routes.

New classifications: 29 intake unknown; 1 reported online lead; 2 clinic-published closures; 4 services with restricted eligibility/referral access. Existing 26 accepting-application records were not increased by guesses from registers or appointment buttons.

## Discovery and reconciliation

Read individual undergraduate and postgraduate Western practice profiles for selected communities within a 90 km community-centre screen, then combined 342 unique profile identifiers. The 90 km buffer was used to avoid silently dropping boundary candidates. Ilderton’s source coordinates incorrectly pointed to Vancouver, so its profiles were fetched separately using the known Ontario community. University profiles are discovery evidence, not a current-practice or intake authority.

`detailed-profile-reconciliation.json` records each screened profile, disposition and source. One profile may name several people; profile counts are not physician or clinic counts. Current office information was corroborated using clinic-owned sources, regional directories and individual CPSO entries. Published findings distinguish confirmed offices from existing-office candidates whose individual affiliation remains unconfirmed. Hospital-only, specialist, locum, historical and non-medical profiles were not indiscriminately added.

## Corrections and useful additions

- London Lambeth and Old South Maternity explicitly close new family-practice intake. Maternity referrals at Old South remain a separate service.
- Western employee/family primary care has employment, family-member and local-doctor eligibility rules. Western and Fanshawe student services are student-restricted.
- St. Joseph’s trauma and violence primary care currently takes only specified internal referrals; no unrestricted self-referral claim.
- Polari’s search-indexed clinic pages advertise new patients, but direct retrieval produced only a JavaScript shell. Published as a reported lead requiring confirmation, not verified acceptance.
- Wharnox invites inquiries about availability; Wharncliffe publishes a registration form. Neither alone establishes current roster capacity.
- Lambeth Station is on Bradley Avenue; old Main Street listings remain online. Nzeadi is now register-listed at Wharnox rather than Carling Heights. Colborne/London Family First is at Oxford Street Suite 203; older Colborne Street corporate listings remain online. Natalie Lovesey is register-listed at Core, not the university’s old Nixon location.
- Correct register-listed phones used for Despard, Collins Egbujuo and Ian Hons where university details differ.
- Sunderji’s current primary location is North York; Anna Johnson’s is West Lorne. Old London profiles were not added as current London practices.

## Remaining gaps — not claimed complete

A full, paginated CPSO/CNO census of every MD/NP across the 75 km circle is **not completed**. Search-indexed individual register checks are not a substitute. The CPSO advanced search page was accessible through web retrieval but direct retrieval returned HTTP 403; no bulk census was obtained. The earlier CNO access barrier remains. No access-control bypass was attempted.

The 342-profile file retains unresolved identity/scope cases, practitioner affiliations and 12 boundary candidates. It is not an exhaustive list of all regional practitioners. Family Plus/Ibeme has conflicting Edward Street university and Elgin Street register addresses, so no definitive patient-facing location was invented. Crystal Marko, Coralee De, Leslie Damude, South London Urgent Care and Ivana Burcul still require current office/scope resolution. Focused elder/obstetric profiles also need general-attachment scope confirmation.

Five existing records still lack a clinic-specific confirmed telephone route: Elmdale building registration (online-only), Queens Health & Homelessness, Qamar (email/waitlist), WCHC New Hamburg, and Ozog-Bartlett Burford. Co-located organization numbers were not substituted. The Burford commercial-directory number is documented as a lead but not relabelled clinic-confirmed.

Schuster’s suite (clinic Unit 1/register Unit 2), Akter’s suite (FHT 203B/register 206A), Beaverbrook’s application reception floor and Cambridge Gateway’s mismatched form identity remain explicit conflicts. Fresh research does not erase those conflicts or refresh old acceptance evidence.

No calls, emails, patient-form submissions or guaranteed enrolment claims were made. This is a completed expansion and screening pass, **not a claim that all missing information or all possible practices have been confirmed**.

## Validation

Passed: database validation (203 records, zero errors), generated-site/PDF/Word build, eight offline functional/evidence tests and JavaScript smoke test. Deployment and live record count are checked separately after publication.
