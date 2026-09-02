# Visit Finland Accommodation Preparation – Run 12b0276d658a

## Scope decision: AMBIGUOUS (multiple_accommodation_products)
The requested domain (hangofarm.fi, operator "Hangö Farm" / C&E Rosenberg Oy, Hanko) presents **more than one candidate Accommodation product**:

- **Villa Maija** (chosen for extraction) – a single, fully renovated (2022–2023) 1888 historic villa at Appelgrenintie 7, 10900 Hanko, divided into 4 named short-term-rental apartments (Eastside, Southside, Westside, Upperside) that share one address, one operator, and one booking engine (villamaija.guestybookings.com). This is a clean, bounded product under the granularity rule ("one hotel/B&B/apartment building... sharing one management/booking system" = one product).
- **16 additional, individually named apartments/villas** listed on the site's "Muut kohteet" page (Villa Rosa, Serenity Suite, Villa Granit View, Hangon Herttua, Villa Magnus Studio, Villa Aurinko, Solara Suite/Kuningatarranta, Villa Primavera, Villa Granit, Regatta Suite, Surf & Turf, Gunnarstrand Surf House, Villa Lotta, Villa Amanda, Hanko Holiday, Hanko Harbor Studio) — each at a **different street address**, each with its own distinct Guesty booking property ID, its own capacity and amenity list. These are separate physical rental units, not room types/packages within Villa Maija, so they are legitimate additional candidate Accommodation products, not exclusions.

No source resolves which single property should be "the" Accommodation record for this run. Per policy this was recorded as `scope_ambiguous` / `multiple_accommodation_products`. Villa Maija was retained as the extracted candidate (most complete, single-building, dedicated page); the other 16 are preserved as `additional_products` in the scope record with names/URLs, **not merged** into Villa Maija's fields. A curator should confirm whether Villa Maija alone, one of the other 16, or a separate multi-record submission (one per property) is intended.

Also recorded as `out_of_type_facilities`: **Hangö Farm Deli**, a restaurant/café at Satamakatu 3, 10900 Hanko, operated by the same company but a different DataHub product type — not extracted here.

## Sources analysed
- p001 https://hangofarm.fi/ (homepage)
- p002 https://hangofarm.fi/loma-asunto-hanko/hotelli-villa-maija-hanko/ (Villa Maija product page – primary source)
- p003 https://hangofarm.fi/loma-asunto-hanko/vuokra-asunto-hanko/ (the 16 other apartments – used only to establish scope ambiguity, not for Villa Maija fields)
- p004 https://hangofarm.fi/yhteystiedot/ (contact page – confirms address/contact split between Deli and accommodation business)
- p005 https://hangofarm.fi/yritys/ (about/company page)

All sources are static HTML, Finnish-language only; no JavaScript-rendering limitations encountered, no documents (PDF/DOCX) were supplied. No fetch failures.

## Excluded / deferred (not fetched or not in scope)
News/blog articles (Horse and Hound Hanko, Hangö Farm VINTAGE), the Villa Maija yoga retreat announcement (seasonal package, not a separate product), the webshop/gift-card storefront, the breakfast add-on product page, the booking terms-and-conditions page, the newsletter signup, the privacy-policy page, and social media links. External booking-engine pages (villamaija.guestybookings.com) and Google Maps were treated strictly as discovery/link-text candidates, never fetched or cited beyond the literal link line stored on the approved pages.

## Field-by-field summary (Villa Maija)
- **name (fi)**: found – "Villa Maija" (p002 title). **name (en)**: missing – no English-language page was retrieved.
- **description (fi)**: found, quoting the villa's introductory sentence (p002). **description (en)**: missing.
- **address**: found – Appelgrenintie 7, 10900 Hanko (site footer, p002).
- **coordinates**: review – derived only from the numeric parameters of a Google Maps link attached to the address; not an explicit on-page coordinate statement, so downgraded from found.
- **contact**: found – email hello@hangofarm.fi, phone +358 50 505 2013, website https://hangofarm.fi/ (p001, p002).
- **categories**: review (as required by policy, never found) – suggested `apartment` and `guest_house`; the PoC taxonomy has no dedicated "villa" category, noted as a gap.
- **accessibility, sustainability_label, stf_status**: missing – none is addressed anywhere on the Villa Maija-specific pages (silence, not a negative claim).
- **capacity**: review – rooms=4 (four named apartments, found); beds could not be reduced to a single integer because the source only gives guest-capacity ranges (1–6 per apartment; 12–19 for the whole villa).
- **pricing**: missing – no fixed rate or explicit dynamic-pricing statement found for accommodation (a €18.50/person breakfast add-on exists but is out of scope for this field).
- **booking_url**: found – https://villamaija.guestybookings.com/ (third-party Guesty engine, linked from p002).
- **availability**: found – open year-round; minimum stay 1 night generally, 3 nights in June–August (captured in notes).
- **opening_hours**: missing – no daily check-in/reception hours stated (property is described only as open every day of the year, captured under availability).
- **amenities**: found – private bathroom, air conditioning, washing machine, fully equipped kitchen, shared terrace, and a sauna specific to unit 2 Southside (p002).
- **languages_spoken**: missing – not stated.
- **images**: not_in_scope, as required.

## Curator actions needed
1. Confirm which of the 17 total Hangö Farm properties (Villa Maija + 16 others) should be submitted as the Accommodation record for this run, or whether multiple separate records are intended.
2. Confirm/replace the `categories` suggestion (no exact "villa" taxonomy entry exists).
3. Decide whether the map-link-derived `coordinates` are acceptable or should be re-verified against an authoritative source.
4. Consider a follow-up run against the English-language site variant (if one exists) to fill the `en` name/description fields.

<!-- deterministic-appendix: do not edit -->
## Deterministic retrieval and validation summary

- Stored website pages: 5
- Page retrieval failures: 0
- Documents declared: 0
- Document/OCR limitations: 0
- Candidate links indexed: 17
- Candidate links omitted from the agent inventory: 0
- Evidence-bundle truncation/omission events: 0
- Context pages delivered: 2 of 2
- Complete context delivered before extraction: True
- Validation errors: 0
- Validation warnings: 0

### Scope review required

- Status: `scope_ambiguous`
- Error code: `multiple_accommodation_products`
- Reason: Villa Maija (https://hangofarm.fi/loma-asunto-hanko/hotelli-villa-maija-hanko) is a clearly bounded single Accommodation product: one restored 1888 historic villa building contain...
- Provisional product: {"pages": ["p001", "p002", "p004", "p005"], "summary": "Villa Maija: a fully renovated (2022-2023) 1888 historic villa in Hanko (Appelgrenintie 7, 10900 Hanko), operated by Hangö ...
- Additional candidates: [{"name": "Villa Rosa", "note": "2-bedroom apartment, sleeps 3, Appelgrenintie area", "url": "https://villamaija.guestybookings.com/en/properties/688fd07d1c98ac0013433fbc"}, {"nam...
- Extraction continued conservatively; scope-dependent fields must be reviewed.

### Field status table

| Field | Locale | Status | Value |
| --- | --- | --- | --- |
| name | fi | found | Villa Maija |
| name | en | missing |  |
| description | fi | found | Villa Maija on yksi Hangon tunnetuimmista pitsihuviloista ja avoinna vuoden jokaisena päivänä. Villa Maija tarjoaa loistavan mahdollisuuden nopeaan irtiottoon arjesta. Yöpyminen a... |
| description | en | missing |  |
| address |  | found | {"city": "Hanko", "postal_code": "10900", "street": "Appelgrenintie 7"} |
| coordinates |  | review | {"latitude": 59.8236528, "longitude": 22.9718909} |
| contact |  | found | {"email": "hello@hangofarm.fi", "phone": "+358 50 505 2013", "website": "https://hangofarm.fi/"} |
| categories |  | review | ["apartment", "guest_house"] |
| accessibility |  | missing |  |
| sustainability_label |  | missing |  |
| stf_status |  | missing |  |
| capacity |  | review | {"rooms": 4} |
| pricing |  | missing |  |
| booking_url |  | found | https://villamaija.guestybookings.com/ |
| availability |  | found | {"minimum_stay_nights": 1, "notes": "Minimi yöpyminen on yksi yö, ja kesällä kesäkuu-elokuu kolme yötä. Avaamme myös kesällä mahdollisuuden lyhyempiin yöpymisiin, jos majoitusten ... |
| opening_hours |  | missing |  |
| amenities |  | found | ["private bathroom (shower and toilet) in every apartment", "air conditioning", "washing machine", "fully equipped kitchen", "shared terrace for all guests", "sauna (Villa Maija 2... |
| languages_spoken |  | missing |  |
| images |  | not_in_scope |  |

### Evidence table

| Field | Locale | Source | Locator | Excerpt |
| --- | --- | --- | --- | --- |
| name | fi | p002 | line 1 | Huvilamajoitus Villa Maija Hanko |
| description | fi | p002 | line 16-17 | Villa Maija on yksi Hangon tunnetuimmista pitsihuviloista ja avoinna vuoden jokaisena päivänä. |
| address |  | p002 | line 60 | Appelgrenintie 7, 10900 Hanko |
| coordinates |  | p002 | line 97 | Appelgrenintie 7, 10900 Hanko -> https://www.google.com/maps/place/Appelgrenintie+7,+10900+Hanko/@59.8236528,22.9718909,1129m |
| contact |  | p002 | line 61 | hello@hangofarm.fi |
| contact |  | p002 | line 62 | +358 50 505 2013 |
| contact |  | p001 | line 137 | (no link text) -> https://hangofarm.fi/ |
| categories |  | p002 | line 20 | Villa Maijan vanhat huoneet on saneerattu ylellisiksi puuhuvila-asunnoiksi. |
| capacity |  | p002 | line 24-28 | Huoneistot: Villa Maija 1 Eastside Villa Maija 2 Southside Villa Maija 3 Westside Villa Maija 4 Upperside |
| capacity |  | p002 | line 23 | Voit varata majoituksen Villa Maijasta 1-6:lle hengelle per huoneisto. |
| capacity |  | p002 | line 41 | Majoitamme hieman seurueesta riippuen 12-19 henkeä. |
| booking_url |  | p002 | line 91 | Varaa majoitus -> https://villamaija.guestybookings.com/ |
| availability |  | p002 | line 23 | Villa Maija on auki vuoden jokaisena päivänä, viikon jokainen päivä. |
| availability |  | p002 | line 23 | Minimi yöpyminen on yksi yö, ja kesällä kesäkuu-elokuu kolme yötä. |
| amenities |  | p002 | line 20 | Kaikissa huoneistoissa on omat kylpyhuoneet (suihku ja wc) sekä uudenaikaiset ilmastointilaitteet sekä pyykkikone. |
| amenities |  | p002 | line 20 | Huoneistossa nro 2 Southside on myös oma sauna. |
| amenities |  | p002 | line 20 | Uudistuksen yhteydessä jokaiseen huoneistoon rakennettiin myös täysin varusteltu keittiö. |
| amenities |  | p002 | line 20 | Huoneistot ovat tilavia ja kaikki vieraat saavat käyttää yhteistä terassia. |

### Conflict table

| Field | Locale | Alternative | Reason |
| --- | --- | --- | --- |
| None |  |  |  |

### Validation table

| Severity | Rule | Field | Message |
| --- | --- | --- | --- |
| None |  |  |  |
