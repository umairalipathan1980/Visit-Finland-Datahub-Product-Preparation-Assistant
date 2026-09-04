# Visit Finland DataHub preparation review

RUN b3a0ad4ea61f — Visit Finland Accommodation preparation

SELECTED PRODUCT TYPE & SCOPE (unresolved — curator action required)
The requested source, https://www.helsinkioutlet.fi/en_GB/, is "Helsinki Outlet," a retail shopping outlet village located at Tatti 17, 00760 Helsinki (on Ring Road III, opposite IKEA Vantaa). It hosts roughly 40 clothing/home/beauty/sports brand stores, an online shop, on-site restaurants, and a children's play area. No page retrieved in this run describes any room, bed, overnight stay, check-in/out process, or other lodging offering.

Because this run's product_type is fixed to "accommodation" and no accommodation/lodging product exists anywhere on the site, scope was recorded as scope_ambiguous with error_code "product_boundary_unclear" (the closest available code — this is technically a zero-candidate situation rather than a multi-candidate one, but the tool only supports resolved/scope_ambiguous statuses). No `product` was recorded because there is no accommodation candidate to select. This site's actual business profile matches the Shops DataHub product type (closest PoC categories: "shopping_center", "outlet"), not Accommodation.

SOURCES ANALYSED
- p001 homepage (https://www.helsinkioutlet.fi/en_GB/) — navigation, flash-sale merchandising, Shopping Village hours/address, LEED Gold mention.
- p002 About Us (page/about-us) — company history ("Our Story"), sustainability strategy, team/contact list.
- p003 The Village (page/the-village) — location description, opening hours, "Village Finds" merchandising.
- p004 Floorplan and stores (page/floorplan_and_stores) — largely navigation/footer; no store-by-store floorplan content was rendered in the static fetch.
- p005 Restaurants (page/restaurants) — lists Espresso House, Pizza Hut, Villa Severino, Pingviini Ice Cream Kiosk as on-site restaurants.

All five pages are static HTML (no JavaScript-rendering limitation noted by the tool) and were fully retrieved without failures. 235 initial candidate links plus 27 additional candidates were reviewed; only same-domain "About/Village/Floorplan/Restaurants" pages were fetched, consistent with checking for any hidden accommodation offering (e.g., Arrival, Parking, News, Inspiration, and all product/taxon pages were excluded as clearly retail-catalogue or logistics content, not accommodation-relevant). No external domains (Facebook, Instagram, TikTok, LinkedIn, the WordPress intranet) were fetched, per policy.

OUT-OF-TYPE FACILITIES NOTED (not extracted as Accommodation, do not block this run)
- Espresso House, Pizza Hut, Villa Severino, Pingviini Ice Cream Kiosk — restaurants/cafés (a different DataHub product type).
- Leo's (Leo's Leikkimaa) — children's play facility.
- ~40 retail brand stores (Gant, Marimekko, Tommy Hilfiger, Kari Traa, Levi's, etc.) — the core Shops-type business of this site.

FIELD VALUES AND STATUSES
Every field in the poc-accommodation-schema-v1 schema was returned with status "missing" (images is "not_in_scope" as required), because no Accommodation product could be identified to which any fact could be safely attributed. Facts that are stated on the site in general (village address "Tatti 17, 00760 Helsinki"; contact info@helsinkioutlet.fi; opening hours Mon–Sat 10:00–20:00, Sun 10:00–18:00; general sustainability/LEED Gold claims) were deliberately NOT marked "found" against the Accommodation schema, because they describe the shopping-village business, not a lodging product — attaching them here would misrepresent an Accommodation record for a non-lodging business. This conservative handling follows the invariant to never invent or misattribute product facts and to keep scope-dependent fields out of "found" status when scope is unresolved.

MISSING INFORMATION, CONFLICTS, AND CURATOR ACTIONS
- No conflicts were found (no accommodation facts existed to conflict).
- Curator action needed: confirm whether this URL was intended for a Shops-type DataHub submission instead (Helsinki Outlet fits "shopping_center"/"outlet" categories well), or whether a different, accommodation-specific URL should be supplied for a future Accommodation run. As currently submitted, this record contains no usable Accommodation content and should not be treated as a real Accommodation candidate — only as a documented "no product found" outcome for this run.
- This package (poc-accommodation-schema-v1 / poc-subset-0.3 categories) is a PoC transcription, not an official DataHub export or validation; nothing here should be described as "DataHub-valid."

<!-- deterministic-appendix: do not edit -->
## Deterministic retrieval and validation summary

- Stored website pages: 5
- Page retrieval failures: 0
- Documents declared: 0
- Document/OCR limitations: 0
- Candidate links indexed: 262
- Candidate links omitted from the agent inventory: 0
- Evidence-bundle truncation/omission events: 0
- Context pages delivered: 6 of 6
- Complete context delivered before extraction: True
- Validation errors: 0
- Validation warnings: 0

### Scope review required

- Status: `scope_ambiguous`
- Error code: `product_boundary_unclear`
- Reason: All available evidence (homepage, About Us, The Village, Floorplan & Stores, and Restaurants pages of www.helsinkioutlet.fi) describes 'Helsinki Outlet', a retail shopping outlet ...
- Provisional product: 
- Additional candidates: []
- Extraction continued conservatively; scope-dependent fields must be reviewed.

### Field status table

| Field | Locale | Status | Value |
| --- | --- | --- | --- |
| name | fi | missing |  |
| name | en | missing |  |
| description | fi | missing |  |
| description | en | missing |  |
| address |  | missing |  |
| coordinates |  | missing |  |
| contact |  | missing |  |
| categories |  | missing |  |
| accessibility |  | missing |  |
| sustainability_label |  | missing |  |
| stf_status |  | missing |  |
| capacity |  | missing |  |
| pricing |  | missing |  |
| booking_url |  | missing |  |
| availability |  | missing |  |
| opening_hours |  | missing |  |
| amenities |  | missing |  |
| languages_spoken |  | missing |  |
| images |  | not_in_scope |  |

### Evidence table

| Field | Locale | Source | Locator | Excerpt |
| --- | --- | --- | --- | --- |
| None |  |  |  |  |

### Conflict table

| Field | Locale | Alternative | Reason |
| --- | --- | --- | --- |
| None |  |  |  |

### Validation table

| Severity | Rule | Field | Message |
| --- | --- | --- | --- |
| None |  |  |  |
