## Visit Finland Accommodation Preparation — Run da395b4aaf01

**Product & scope:** Accommodation record for **Villa Maija**, Hangö Farm, Appelgrenintie 7, 10900 Hanko. Scope was resolved (not ambiguous): Villa Maija is one historic (1888) villa fully renovated 2022–2023 and subdivided into 4 furnished apartments (Eastside, Southside, Westside, Upperside) sharing one address, one operator (C&E Rosenberg Oy / Hangö Farm), one contact channel, and one Guesty booking system — per guidance this counts as one Accommodation product, not four.

**Sources analysed (5 same-domain pages, all static HTML, no JS/documents involved):**
- p001 https://hangofarm.fi/loma-asunto-hanko/hotelli-villa-maija-hanko/ (seed page, primary product page)
- p002 https://hangofarm.fi/yhteystiedot/ (contact — distinguishes the accommodation business's own contact block from the Deli's)
- p003 https://hangofarm.fi/yritys/ (company/about background)
- p004 https://hangofarm.fi/loma-asunto-hanko/ (accommodation overview, shows the site's own split between Villa Maija and a separate rentals portfolio)
- p005 https://hangofarm.fi/loma-asunto-hanko/vuokra-asunto-hanko/ (read only to confirm the scope boundary, not used for Villa Maija fields)

A recovery fetch of an additional "/kohteet/villamaija" candidate returned no new content (0 bytes fetched), so no further pages were added.

**Excluded / deferred, not merged:**
- **"Muut kohteet" / private rental apartments portfolio** (~15 separately addressed units: Villa Rosa, Serenity Suite, Villa Granit View, Hangon Herttua, Kuningatarranta/Solara Suite, Regatta Suite, Surf & Turf, Gunnarstrand Surf House, Villa Lotta, Villa Amanda, Hanko Holiday, Hanko Harbor Studio, etc., p004/p005) — a distinct accommodation product/portfolio from Villa Maija. Not extracted or merged; recorded as excluded because the run's seed page specifically identified Villa Maija.
- **Hangö Farm Deli** (restaurant, Satamakatu 3, own hours) — different DataHub product type (food service), recorded as `out_of_type_facilities`.
- **Co-working space** (mentioned in "Meistä" as part of the "Hangö Farm Lifestyle" concept) — different facility type, recorded as `out_of_type_facilities`.

**Field outcomes (see submitted JSON for full evidence):**
- `name.fi` **found** ("Villa Maija"); `name.en` **missing** — no English-language content was found on the fetched pages.
- `description.fi` **found**; `description.en` **missing**.
- `address` **found** (Appelgrenintie 7, 10900 Hanko; region/country not stated, left out rather than guessed).
- `coordinates` **found** — read literally from the Google Maps URL embedded in the page's link list (59.8236528, 22.9718909); the external maps page itself was never fetched.
- `contact` **found** (email, phone, and the Villa Maija page URL as website), sourced from the accommodation-specific contact block (p002), separate from the Deli's contact block on the same page.
- `categories` **review** (mandatory ceiling) — value `["apartment"]`, with `["guest_house"]` recorded as an alternative; the PoC taxonomy has no dedicated "villa" category, so a curator should confirm the closest fit.
- `accessibility`, `sustainability_label`, `stf_status` — all **missing**, value `not_specified`: none of the fetched pages address any of these for Villa Maija (accessibility statements found on the site apply only to the separate, excluded rental-portfolio units, e.g. Regatta Suite/Hanko Harbor Studio, and were not carried over).
- `capacity` **found** — 4 apartments; overall guest capacity of 12–19 people is noted, but per-apartment bed counts are not stated, so `beds` was left out rather than estimated.
- `pricing` **missing** — no room rate is published on the fetched pages (handled inside the external Guesty engine, not fetched); a breakfast add-on price (18.50 €/person) exists but is a separate optional service, not the room rate, so it was not used to fill this field, only noted.
- `booking_url` **found** (villamaija.guestybookings.com), cited as the link line on p001 per policy.
- `availability` **found** — open year-round, minimum stay 1 night generally, 3 nights in June–August (seasonal detail kept in `notes`).
- `opening_hours` **missing** — no reception/check-in hours schedule was stated (the only opening-hours text on the site belongs to the excluded Deli restaurant).
- `amenities` **found** — private bathroom, air conditioning, washing machine, fully equipped kitchen, shared terrace, sauna (one apartment only), optional breakfast delivery.
- `languages_spoken` **missing** — not stated on any fetched page.
- `images` **not_in_scope** per policy.

**Validation:** `submit_extraction` returned `valid: true` on the first submission; no repair was needed.

**Curator actions suggested:** confirm/replace the `categories` classification (apartment vs. guest_house, or request a "villa" category be added to the taxonomy); consider a follow-up run against `villamaija.guestybookings.com` (external booking domain, not fetched in this run) if pricing/beds detail is needed; confirm whether the separate rental-apartment portfolio should become its own Accommodation record in a future run.

<!-- deterministic-appendix: do not edit -->
## Deterministic retrieval and validation summary

- Stored website pages: 5
- Page retrieval failures: 0
- Documents declared: 0
- Document/OCR limitations: 0
- Candidate links indexed: 13
- Candidate links omitted from the agent inventory: 0
- Evidence-bundle truncation/omission events: 0
- Context pages delivered: 2 of 2
- Complete context delivered before extraction: True
- Validation errors: 0
- Validation warnings: 0

### Field status table

| Field | Locale | Status | Value |
| --- | --- | --- | --- |
| name | fi | found | Villa Maija |
| name | en | missing |  |
| description | fi | found | Villa Maija on yksi Hangon tunnetuimmista pitsihuviloista ja avoinna vuoden jokaisena päivänä. Villa Maija tarjoaa loistavan mahdollisuuden nopeaan irtiottoon arjesta. Yöpyminen a... |
| description | en | missing |  |
| address |  | found | {"city": "Hanko", "postal_code": "10900", "street": "Appelgrenintie 7"} |
| coordinates |  | found | {"latitude": 59.8236528, "longitude": 22.9718909} |
| contact |  | found | {"email": "hello@hangofarm.fi", "phone": "+358 50 505 2013", "website": "https://hangofarm.fi/loma-asunto-hanko/hotelli-villa-maija-hanko"} |
| categories |  | review | ["apartment"] |
| accessibility |  | missing | not_specified |
| sustainability_label |  | missing | not_specified |
| stf_status |  | missing | not_specified |
| capacity |  | found | {"rooms": 4} |
| pricing |  | missing |  |
| booking_url |  | found | https://villamaija.guestybookings.com/ |
| availability |  | found | {"minimum_stay_nights": 1, "notes": "Kesäkuu-elokuu (June-August) minimum stay rises to 3 nights; shorter stays may be opened in summer if gaps remain between existing bookings.",... |
| opening_hours |  | missing |  |
| amenities |  | found | ["private bathroom (shower & wc) in every apartment", "air conditioning", "washing machine", "fully equipped kitchen", "shared terrace", "sauna (in apartment 2 Southside only)", "... |
| languages_spoken |  | missing |  |
| images |  | not_in_scope |  |

### Evidence table

| Field | Locale | Source | Locator | Excerpt |
| --- | --- | --- | --- | --- |
| name | fi | p001 | characters 1-7119 | Villa Maija |
| description | fi | p001 | characters 1-7119 | Villa Maija on yksi Hangon tunnetuimmista pitsihuviloista ja avoinna vuoden jokaisena päivänä. |
| description | fi | p001 | characters 1-7119 | Tullijohtaja, hovineuvos Frans von Haartman rakennutti Villa Maijan vuonna 1888. |
| address |  | p001 | characters 1-7119 | Appelgrenintie 7, 10900 Hanko |
| coordinates |  | p001 | characters 1-7119 | Appelgrenintie 7, 10900 Hanko -> https://www.google.com/maps/place/Appelgrenintie+7,+10900+Hanko/@59.8236528,22.9718909,1129m |
| contact |  | p002 | characters 1-3352 | hello@hangofarm.fi |
| contact |  | p002 | characters 1-3352 | +358 50 505 2013 |
| contact |  | p001 | characters 1-7119 | Villa Maija -> https://hangofarm.fi/loma-asunto-hanko/hotelli-villa-maija-hanko |
| categories |  | p001 | characters 1-7119 | Villa Maijan vanhat huoneet on saneerattu ylellisiksi puuhuvila-asunnoiksi. |
| capacity |  | p001 | characters 1-7119 | Villa Maija 1 Eastside |
| capacity |  | p001 | characters 1-7119 | Majoitamme hieman seurueesta riippuen 12-19 henkeä. |
| booking_url |  | p001 | characters 1-7119 | Varaa majoitus -> https://villamaija.guestybookings.com/ |
| availability |  | p001 | characters 1-7119 | Villa Maija on auki vuoden jokaisena päivänä. |
| availability |  | p001 | characters 1-7119 | Minimi yöpyminen on yksi yö, ja kesällä kesäkuu-elokuu kolme yötä. |
| amenities |  | p001 | characters 1-7119 | Kaikissa huoneistoissa on omat kylpyhuoneet (suihku ja wc) sekä uudenaikaiset ilmastointilaitteet sekä pyykkikone. |
| amenities |  | p001 | characters 1-7119 | Huoneistossa nro 2 Southside on myös oma sauna. |
| amenities |  | p001 | characters 1-7119 | Uudistuksen yhteydessä jokaiseen huoneistoon rakennettiin myös täysin varusteltu keittiö. |
| amenities |  | p001 | characters 1-7119 | kaikki vieraat saavat käyttää yhteistä terassia |
| amenities |  | p001 | characters 1-7119 | Villa Maijassa voit tilata aamupalan kesällä joka päivä (toukokuu-elokuu). |

### Conflict table

| Field | Locale | Alternative | Reason |
| --- | --- | --- | --- |
| categories |  | ["guest_house"] | Villa Maija could also be classified as a guest house/villa-style lodging rather than self-contained apartments, since the PoC taxonomy has no dedicated 'villa' category; curator ... |

### Validation table

| Severity | Rule | Field | Message |
| --- | --- | --- | --- |
| None |  |  |  |
