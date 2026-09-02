# Visit Finland Shops Preparation — Review Report (run d528c890e381)

## Product scope
Selected DataHub product type: **Shops**. Scope resolved to a single product: **Hanko marketplace / Hangon Kauppatori**, a public open-air marketplace by the railway bridge on Nycanderinkatu, Hanko. Evidence came from two same-site bilingual product pages: the English page "Hanko marketplace" (p001) and the Finnish page "Hangon Kauppatori" (p002). Both pages describe the same single physical location (same phone number, same opening days/hours, same Google Maps link), so no product-merging occurred — they were treated as localized variants of one product.

No competing Shops candidates were found among the ~80 discovered links; nearly all other links are unrelated theme pages (Accommodation, Wellness, Boating, etc.) or unrelated named businesses (Omena hotels, M. Broman, Vuorikatu, Friman Travel, Pärlan dentist, Hanko museum, Hangolf) at different locations — these were excluded, not treated as scope ambiguity.

One out-of-type facility was identified: **Angkhanan torikahvila**, a café operating seasonally at the marketplace (per the Finnish page text). This is a different DataHub product type (food & beverage) and was recorded under `out_of_type_facilities` rather than merged into the Shops fields.

## Sources analysed
- p001 — english page `https://visithanko.fi/en/tuotesivu/hanko-marketplace/` (seed page)
- p002 — finnish page `https://visithanko.fi/tuotesivu/hangon-kauppatori/` (fetched for localized name/description)
- p003 — english "Accessibility" page (fetched to check for marketplace-specific accessibility evidence; found only general/other-location content, no tie to this product)

No retrieval failures, no JavaScript-only limitations, no documents (PDF/DOCX) were supplied or found relevant, and no OCR requirements arose. The Swedish-language variant and the external map/service-locator subdomain were seen as candidates but were not fetched (out of the two-call budget and not needed for the fi/en schema).

## Field values and statuses
- **name**: found for both fi ("Hangon Kauppatori") and en ("Hanko marketplace").
- **description**: found for fi (full descriptive paragraph about produce sold and location); **missing** for en — the English page only contains a location/hours sentence, no product description; that sentence was instead used for opening_hours.
- **address**: `review` — street name "Nycanderinkatu" and a "by the railway bridge" location note are explicit; postal code, house number, and an explicit in-context city/country statement are not present on the product pages themselves (city inferred only from site-wide context). Curator should confirm the full postal address.
- **coordinates**: `review` — derived from the Google Maps hyperlink URL (not from body prose). The URL encodes two coordinate pairs (map-viewport-center vs. place-marker); the marker pair was used as primary value, the center pair kept as an alternative. Curator should verify against an authoritative source.
- **contact**: found — phone `+358 (0)40 533 4040` (en) with a formatting-variant alternative `040 533 4040` (fi, same number). No email or website specific to the marketplace was found (the tourist office's own contact details were correctly excluded as belonging to a different entity).
- **categories**: `review` (as required by policy) — suggested `market`, supported by the Finnish description of goods sold (local food, fish, vegetables, seasonal plants/berries) and the English name "Hanko marketplace".
- **accessibility**: `missing` — no marketplace-specific accessibility statement found; the site's general Accessibility page discusses other locations (a beach, sights, cafés/restaurants, accommodation) but never this marketplace, so nothing was inferred.
- **sustainability_label**: `review` — a "Green choise"/"Vihreä valinta" related-link appears specifically in the sidebar of this product's own pages (not on the unrelated Accessibility page), suggesting a possible tag, but no explicit sentence states the marketplace holds this label. Flagged for curator confirmation rather than marked found.
- **stf_status**: `missing` — no Sustainable Travel Finland mention found for this product.
- **opening_hours**: submitted as found (Tue/Thu/Sat 06:00–13:00, open year-round, from matching en/fi statements) but the deterministic validator could not verify one excerpt's exact literal match and **downgraded it to `review`** on final validation — curator should re-check this field's excerpt against source formatting.
- **languages_spoken**: `missing` — no explicit statement of staff/vendor languages; the site's own fi/sv/en navigation was correctly not used as a proxy for this field.
- **images**: `not_in_scope` per policy, no evidence attached.

## Missing information, conflicts, curator actions
1. Confirm full postal address (house number, postal code) for the marketplace — only street and a descriptive locator were found.
2. Verify which Google Maps coordinate pair is authoritative; two candidate pairs were preserved as value/alternative.
3. Confirm whether the "Green Choice"/"Vihreä valinta" tag applies to this specific listing (currently inferred only from a related-link placement, not explicit text).
4. Re-verify the `opening_hours` excerpt wording against the live source; the validator flagged a quote-match issue and downgraded the field to review even though the underlying day/time facts (Tue, Thu, Sat, 06:00–13:00, year-round) are corroborated by both language versions.
5. Confirm English-language description is genuinely absent on the live site (only a location/hours sentence exists) versus the fuller Finnish description, and consider whether a curator should port/translate content — no translation was performed here per policy.
6. Angkhanan torikahvila (seasonal café at the marketplace) should be considered for a separate food & beverage product record; it was intentionally not extracted here.

This package prepares reviewable artifacts only; it does not submit to DataHub.

<!-- deterministic-appendix: do not edit -->
## Deterministic retrieval and validation summary

- Stored website pages: 3
- Page retrieval failures: 0
- Documents declared: 0
- Document/OCR limitations: 0
- Candidate links indexed: 160
- Candidate links omitted from the agent inventory: 0
- Evidence-bundle truncation/omission events: 0
- Context pages delivered: 3 of 3
- Complete context delivered before extraction: True
- Validation errors: 0
- Validation warnings: 1

### Field status table

| Field | Locale | Status | Value |
| --- | --- | --- | --- |
| name | fi | found | Hangon Kauppatori |
| name | en | found | Hanko marketplace |
| description | fi | found | Kauppatori sijaitsee sillan kupeessa Nycanderinkadulla. Tori on auki ympäri vuoden. Torilla myynnissä lähiruokaa, kalaa ja vihanneksia sekä kesällä taimia, marjoja ym. Torilla toi... |
| description | en | missing |  |
| address |  | review | {"city": "Hanko", "country": "Finland", "location_note": "by the railway bridge / sillan kupeessa", "postal_code": null, "street": "Nycanderinkatu"} |
| coordinates |  | review | {"latitude": 59.8246165, "longitude": 22.9639141} |
| contact |  | found | {"email": null, "phone": "+358 (0)40 533 4040", "website": null} |
| categories |  | review | ["market"] |
| accessibility |  | missing |  |
| sustainability_label |  | review | Green Choice / Vihreä valinta (tentative) |
| stf_status |  | missing |  |
| opening_hours |  | review | {"notes": "Open all year around (source: 'Open all year around by the railway bridge' / 'Tori on auki ympäri vuoden.')", "regular": [{"closes": "13:00", "days": ["tuesday", "thurs... |
| languages_spoken |  | missing |  |
| images |  | not_in_scope |  |

### Evidence table

| Field | Locale | Source | Locator | Excerpt |
| --- | --- | --- | --- | --- |
| name | fi | p002 | line 164 | Hangon Kauppatori |
| name | en | p001 | line 164 | Hanko marketplace |
| description | fi | p002 | lines 165-166 | Kauppatori sijaitsee sillan kupeessa Nycanderinkadulla. Tori on auki ympäri vuoden. Torilla myynnissä lähiruokaa, kalaa ja vihanneksia sekä kesällä taimia, marjoja ym. Torilla toi... |
| address |  | p002 | line 165 | Kauppatori sijaitsee sillan kupeessa Nycanderinkadulla. |
| address |  | p001 | line 165 | Open all year around by the railway bridge: |
| coordinates |  | p001 | Google Maps link URL | https://www.google.com/maps/place/Hanko+Kauppatori,+10900+Hanko/@59.8246265,22.9551379,15z/data=!3m1!4b1!4m5!3m4!1s0x468ce25e38482ba3:0xfec9c9935eee7261!8m2!3d59.8246165!4d22.9639... |
| contact |  | p001 | line 167 | +358 (0)40 533 4040 |
| categories |  | p002 | line 165 | Torilla myynnissä lähiruokaa, kalaa ja vihanneksia sekä kesällä taimia, marjoja ym. |
| categories |  | p001 | line 164 | Hanko marketplace |
| sustainability_label |  | p001 | line 170 | Green choise |
| sustainability_label |  | p002 | line 171 | Vihreä valinta |
| opening_hours |  | p001 | lines 165-166 | Open all year around by the railway bridge: Tuesday, Thursday and Saturday at 6.00 am to 1 pm |
| opening_hours |  | p002 | lines 166-167 | Ti, to, la klo 6-13. |

### Conflict table

| Field | Locale | Alternative | Reason |
| --- | --- | --- | --- |
| coordinates |  | {"latitude": 59.8246265, "longitude": 22.9551379} | The same Google Maps URL encodes two coordinate pairs: a map-viewport-center pair (@lat,lng) and a place-marker pair (3d/4d). The marker pair was used as the primary value; the vi... |
| contact |  | {"phone": "040 533 4040"} | Finnish-language page lists the same phone number in local format without the +358 country code; treated as a formatting variant of the same number, not a conflicting fact. |

### Validation table

| Severity | Rule | Field | Message |
| --- | --- | --- | --- |
| warning | quote_not_verified | opening_hours | one or more evidence excerpts could not be verified against stored source text; downgraded to review |
