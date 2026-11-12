# Live-source follow-up — 12 November 2026

## Published corrections

The directory now contains 204 records across 41 communities: 26 advertise applications, 19 have waitlists, 15 have limited intake, 14 are regional intake reports, 17 carry a clinic closure-to-intake notice, and 113 remain unconfirmed. These are practice/service records, not a count of independent physicians.

- **Dr. Jonathon Griffin:** the live clinic homepage explicitly invites waitlist requests at 519-681-8860. Updated from unknown to waitlist. The live page supersedes older indexed closure wording. No guaranteed enrolment date.
- **Family Plus / Dr. Ikechukwu Walter Ibeme:** live CPSO now lists 107 Edward Street, Unit 103, St. Thomas, 226-289-1430. This resolves the conflict with an older indexed Elgin Street address. Added as c204; intake remains unknown.
- **St. Thomas Family Care Centre:** live CPSO places Dr. Derek Vaughan at PeopleCare Tillsonburg. Dr. Rick Goodhew’s current record separately confirms the Talbot Street office and 519-631-8460. Corrected c187 to Goodhew; no inference that the clinic closed or that Vaughan stopped all community work.
- **Tillsonburg Medical Centre:** clinic-owned website is accessible and confirms its address and phone. It is under development and does not state intake. Removed the earlier website-access limitation from the research finding.
- **Historical exclusions:** Crystal Ann Marko (CPSO 98329) resigned in 2018; Leslie Ruth Damude (33503) resigned in 2020. Both were found in the university inventory and are excluded from active additions. Western identifies Ivana Burcul’s addiction-medicine role; no separate general attachment office was established.

See `live-register-corrections.json` and the updated profile reconciliation for record-specific evidence URLs. Live CPSO and indexed search extracts differed materially: an indexed extract is not proof of today's practice address.

## Remaining public-source conflicts

| Record | What remains unresolved | Published handling |
|---|---|---|
| Beaverbrook c004 | FAQ directs Hassani applications to the second floor; the previously reviewed form uses Unit 1 | Named-provider application status retained; confirm reception before travel |
| Stoney Creek c005 | Broad August announcement conflicts with more specific FAQ/location wording | Unknown; not shown as an opening |
| Cambridge Gateway c055 | Cambridge intake form still carries Burlington GC Medical contact details | Cambridge phone route only; no direct application link published |
| Schuster c098 | Own contact page says Unit 1; live CPSO says Unit 2 | Street/building retained; suite flagged |
| Akter c154 | FHT says 203B; live CPSO says 206A | Suite flagged |

Re-reading both conflicting sources does not resolve which instruction the clinic intends. No phone calls, emails, or patient applications were made.

## Unconfirmed intake is now explained

Each unknown record has a visible explanation, preserved in selected CSV/PDF/Word downloads and full PDF/Word directories. The overview shows counts:

- 104: no current office-specific intake established;
- 6: application/program scope unclear;
- 2: relevant intake source could not be inspected;
- 1: conflicting intake statements.

Address disputes are recorded separately: they do not imply conflicting intake claims. A source-access failure is not evidence of closure. A clinic website with no capacity statement remains unknown, not closed.

## Register coverage: incomplete

The interactive register works. Exploratory searches returned result counts for 32 city labels, including separate St Thomas/St. Thomas spellings. Counts and search settings are saved in `interactive-register-search-log.json`.

**This is not a completed census.** Not all individual rows were retained before the browser runtime reset, and those searches have not all been reconciled to offices. Brantford exceeded the 100-result limit. Surname searches are substring searches, so a surname-B subset is not a disjoint alphabetical partition. The Family Doctor filter also omits some historical physicians without a listed family-medicine specialty. Municipality aliases, additional practice locations, boundary practices and a comprehensive CNO nurse-practitioner reconciliation remain incomplete.

The university inventory's 342 profile identifiers remain an audit input, not a completeness denominator. Coralee De remains an unresolved identity; an all-status/all-doctor-type CPSO search for Coralee returned no match. Ziradkar is named on Masonville's current walk-in clinic website, but the relationship to older South London Urgent Care addresses and ongoing attachment scope remains unresolved.

## Validation

Data validation: 204 records, 41 communities, zero errors. Eight offline Python test scripts and the JavaScript smoke checks passed. Filtering, guarded editing, selected/all exports, CSV formula protection, and research provenance were exercised. Full site/PDF/Word generation succeeded.
