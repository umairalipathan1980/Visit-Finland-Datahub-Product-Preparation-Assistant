# Visit Finland DataHub preparation review

Visit Finland Accommodation preparation — run 08e97b42290e

SELECTED PRODUCT & SCOPE
- Product type: Accommodation (poc-accommodation-schema-v1).
- Product: "Bed & Breakfast Villa Aurora", Hanko, Finland — a single, unambiguous accommodation product page maintained by the Visit Hanko destination site (visithanko.fi). Scope was resolved (not ambiguous): the requested page clearly identifies one B&B business (7 double rooms, own management/booking, open year-round).
- Global site navigation on the same pages links to many unrelated businesses and to a small number of out-of-type facilities (e.g. Restaurant Segel, Dyyni restaurant/sauna) and other accommodation-themed pages (Omena hotels, Villa Tellina, Stormhälla, Itämerenportti, Isla Nordica, Whynot Finland). These were treated as navigation exclusions, per policy, and were not merged into or extracted as this product; they are recorded under `excluded` / `out_of_type_facilities` in the scope decision, not extracted.

SOURCES ANALYSED
- p001 — English product page: https://visithanko.fi/en/tuotesivu/bed-breakfast-villa-aurora-3/
- p002 — Finnish product page: https://visithanko.fi/tuotesivu/bed-breakfast-villa-aurora/
Both are static HTML captures of the same underlying listing (English and Finnish language variants), fetched successfully with no retrieval failures. The Swedish variant (sv) was discovered as a candidate link but not fetched, since the schema only requires fi/en localization and the two fetched pages were sufficient and consistent with each other. No PDF/DOCX documents were supplied or parsed for this run. No JavaScript-rendering limitations were encountered (site is static HTML).

FIELD VALUES AND STATUSES
- name (fi/en): found — "Bed & Breakfast Villa Aurora" (identical in both languages).
- description (fi/en): found — localized descriptions kept separate and untranslated, covering room count/type, ensuite bathrooms, accessibility, guide/photography services, and year-round operation.
- address: found — street "Vartiovuorentie 4", postal_code "10900", city "Hanko" (identical on both pages). Region and country are not stated anywhere on the source pages and were left out rather than inferred.
- coordinates: review — parsed from an embedded Google Maps link URL on the page rather than an explicit lat/long statement. The URL contains two slightly different coordinate pairs (map-center vs. pin marker); the pin pair (59.8239446, 22.9742483) was used as the primary value with the map-center pair (59.8239472, 22.9720539) recorded as an alternative. Curator should confirm which pair is authoritative.
- contact: found — email villaaurorahanko@gmail.com, phone +358 44 9703750, website http://www.villaaurora.fi/ (the business's own external site, cited as literal text/link on the stored page, not fetched itself since it is an unapproved domain).
- categories: review (per policy, categories are never "found") — suggested "bed_and_breakfast", based on the business name/title and an "Accomodations" tag on the listing. This is a classification judgment for curator confirmation, not a verbatim fact.
- accessibility: found — "accessible", explicitly stated on both language pages ("Villa Aurora is also accessible" / "kiinteistö on esteetön ja varustettu mm. hissillä") and supported by an "Accessible accommodation" tag.
- sustainability_label: missing — no statement on either page addresses environmental/sustainability practices for this specific business.
- stf_status: missing — no mention of the named Sustainable Travel Finland certification for this business (a general sustainability nav link exists site-wide but does not reference this specific product, so it was not used as evidence).
- capacity: found (partial) — rooms: 7 (stated as "seven double rooms" / "seitsemän" double rooms). Beds count is not stated and was left out rather than computed/inferred.
- pricing: missing — no rate, unit, or "varies" language found on either page.
- booking_url: missing — no dedicated booking/reservation destination distinct from the business's general website was found in the stored evidence.
- availability: found — open_year_round: true, stated identically on both pages ("Open all year around." / "Toiminta on ympärivuotista."). No minimum-stay or blackout-date information was present.
- opening_hours: missing — no check-in/check-out or structured hours were stated.
- amenities: found — compiled free-text list (private ensuite shower/WC, air conditioning, dog friendly, kid friendly, accessible facilities including a lift, guide/photography services, garden or park view), each item tied to a specific verbatim excerpt.
- languages_spoken: missing — the page is offered in fi/sv/en, but that is a website-localization fact, not a stated claim about which languages the host/staff speak, so it was deliberately not extracted as evidence for this field (noted in the field's own notes).
- images: not_in_scope, as required by policy.

MISSING INFORMATION / CONFLICTS / CURATOR ACTIONS
- Curator should verify the correct coordinate pair (review status) against an authoritative source.
- Curator should confirm or adjust the suggested "bed_and_breakfast" category (review status, PoC taxonomy is a ~20-entry subset only).
- No conflicting facts were found between the English and Finnish pages; all shared facts (name, address, contact, room count, accessibility, year-round operation) were consistent across both language versions.
- No retrieval failures, truncation, or OCR/document-parsing issues occurred in this run. One additional fetch call (Finnish-language page, l002) was used to obtain localized fi content directly rather than translating from English; the Swedish variant and generic category/navigation pages (e.g. accessible-accommodation directory) were not fetched as they were not essential to completing the required schema fields for this single product.

<!-- deterministic-appendix: do not edit -->
## Deterministic retrieval and validation summary

- Stored website pages: 2
- Page retrieval failures: 0
- Documents declared: 0
- Document/OCR limitations: 0
- Candidate links indexed: 164
- Candidate links omitted from the agent inventory: 0
- Evidence-bundle truncation/omission events: 0
- Context pages delivered: 2 of 2
- Complete context delivered before extraction: True
- Validation errors: 0
- Validation warnings: 0

### Field status table

| Field | Locale | Status | Value |
| --- | --- | --- | --- |
| name | fi | found | Bed & Breakfast Villa Aurora |
| name | en | found | Bed & Breakfast Villa Aurora |
| description | fi | found | Majoitusyritys myy majoituspalvelua sekä tuottaa oheispalveluja kuten esim. opas- ja kuvauspalveluja. Lisäksi erilaiset teematapahtumat ja -illat ovat ohjelmistossa. Huoneet, joit... |
| description | en | found | Bed & Breakfast that also offers guide- and photograph services. There are seven double rooms, from which there are garden or park view. All rooms have their own showers and toile... |
| address |  | found | {"city": "Hanko", "postal_code": "10900", "street": "Vartiovuorentie 4"} |
| coordinates |  | review | {"latitude": 59.8239446, "longitude": 22.9742483} |
| contact |  | found | {"email": "villaaurorahanko@gmail.com", "phone": "+358 44 9703750", "website": "http://www.villaaurora.fi/"} |
| categories |  | review | ["bed_and_breakfast"] |
| accessibility |  | found | accessible |
| sustainability_label |  | missing |  |
| stf_status |  | missing |  |
| capacity |  | found | {"rooms": 7} |
| pricing |  | missing |  |
| booking_url |  | missing |  |
| availability |  | found | {"open_year_round": true} |
| opening_hours |  | missing |  |
| amenities |  | found | ["Private shower/WC in every room", "Air conditioning (AC)", "Dog friendly", "Kid friendly", "Accessible facilities including a lift", "Guide and photography services", "Garden or... |
| languages_spoken |  | missing |  |
| images |  | not_in_scope |  |

### Evidence table

| Field | Locale | Source | Locator | Excerpt |
| --- | --- | --- | --- | --- |
| name | fi | p002 | line 164 | Bed & Breakfast Villa Aurora |
| name | en | p001 | line 164 | Bed & Breakfast Villa Aurora |
| description | fi | p002 | line 165 | Majoitusyritys myy majoituspalvelua sekä tuottaa oheispalveluja kuten esim. opas- ja kuvauspalveluja. Lisäksi erilaiset teematapahtumat ja -illat ovat ohjelmistossa. Huoneet, joit... |
| description | fi | p002 | line 166 | Villa Aurora voi majoittaa myös liikuntaesteisiä, sillä kiinteistö on esteetön ja varustettu mm. hissillä. Rakennuksessa on myös erillinen suihku ja WC liikuntaesteiset huomioon o... |
| description | en | p001 | line 165 | Bed & Breakfast that also offers guide- and photograph services. |
| description | en | p001 | line 166 | There are seven double rooms, from which there are garden or park view. All rooms have their own showers and toilets. Villa Aurora is also accessible. |
| description | en | p001 | line 167 | Open all year around. |
| address |  | p001 | line 171 | Vartiovuorentie 4, 10900 Hanko |
| address |  | p002 | line 170 | Vartiovuorentie 4, 10900 Hanko |
| coordinates |  | p001 | line 293 | Vartiovuorentie 4, 10900 Hanko -> https://www.google.com/maps/place/B%26B+Villa+Aurora/@59.8239472,22.9720539,17z/data=!3m1!4b1!4m8!3m7!1s0x468ce261a1fbb65f:0x3aeb2eef3798df98!5m2... |
| contact |  | p001 | line 169 | villaaurorahanko@gmail.com |
| contact |  | p001 | line 170 | +358 44 9703750 |
| contact |  | p001 | line 292 | villaaurora.fi -> http://www.villaaurora.fi/ |
| categories |  | p001 | line 164 | Bed & Breakfast Villa Aurora |
| categories |  | p001 | line 174 | Accomodations |
| accessibility |  | p001 | line 166 | Villa Aurora is also accessible. |
| accessibility |  | p002 | line 166 | Villa Aurora voi majoittaa myös liikuntaesteisiä, sillä kiinteistö on esteetön ja varustettu mm. hissillä. |
| accessibility |  | p001 | line 173 | Accessible accommodation |
| capacity |  | p001 | line 166 | There are seven double rooms, from which there are garden or park view. |
| capacity |  | p002 | line 165 | Huoneet, joita on seitsemän ovat kahden hengen huoneita, joista on puutarha- tai puistonäkymät. |
| availability |  | p001 | line 167 | Open all year around. |
| availability |  | p002 | line 166 | Toiminta on ympärivuotista. |
| amenities |  | p001 | line 166 | All rooms have their own showers and toilets. |
| amenities |  | p001 | line 172 | AC |
| amenities |  | p001 | line 175 | Dog friendly |
| amenities |  | p001 | line 176 | Kid friendly |
| amenities |  | p002 | line 166 | kiinteistö on esteetön ja varustettu mm. hissillä |
| amenities |  | p001 | line 165 | Bed & Breakfast that also offers guide- and photograph services. |
| amenities |  | p001 | line 166 | There are seven double rooms, from which there are garden or park view. |

### Conflict table

| Field | Locale | Alternative | Reason |
| --- | --- | --- | --- |
| coordinates |  | {"latitude": 59.8239472, "longitude": 22.9720539} | The stored Google Maps link URL embeds two coordinate pairs: the @lat,lng map-center parameter (59.8239472, 22.9720539) and the !3d/!4d pin-marker parameter (59.8239446, 22.974248... |

### Validation table

| Severity | Rule | Field | Message |
| --- | --- | --- | --- |
| None |  |  |  |
