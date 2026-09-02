# Visit Finland DataHub preparation review

RUN e993e80c8f68 — Visit Finland Shops preparation report

PRODUCT & SCOPE
Selected DataHub product type: Shops. Scope resolved (not ambiguous) to a single product: "K-Supermarket" grocery store at Rewellinkatu 2, 10900 Hanko. This is one identifiable retail business at one location, matching the Shops granularity rule. Both the requested English page (visithanko.fi/en/tuotesivu/k-supermarket-3, source p001) and its Finnish counterpart (visithanko.fi/tuotesivu/k-supermarket, source p002) describe the same store consistently (same address, same phone number in different formatting, same category tags "Grocery store"/"Ruokakauppa" and "Open 365"/"Auki 365"). No competing K-Supermarket location or second product was found on these pages, so no scope ambiguity was recorded.

SOURCES ANALYSED
- p001: English product page (seed page supplied by the request).
- p002: Finnish product page for the same product, fetched to populate the required localized "fi" name/description fields (one fetch_selected_pages call, link l002).
No PDF/DOCX documents were supplied. No retrieval failures or truncation occurred; both pages were static HTML and rendered fully.

EXCLUDED / NOT RETRIEVED
- The Swedish-language variant (l003) was not fetched; the extraction schema only requires fi/en, and this candidate was left as an unretrieved alternative.
- Dozens of unrelated visithanko.fi navigation links to other shops, restaurants, accommodation, and activity products were listed as candidates but correctly excluded — they are separate DataHub products outside this run's scope, not part of the K-Supermarket page.
- The external k-ruoka.fi chain listing and the Google Maps link were never fetched (out-of-domain); only their literal URL text as it appeared on the approved visithanko.fi pages was used as citable evidence, per policy.

FIELD VALUES AND STATUSES
- name (fi/en): found — "K-Supermarket" on both language pages.
- description (fi/en): missing — neither page contains descriptive prose about the shop.
- address: found — street "Rewellinkatu 2", postal code "10900", city "Hanko", cited identically on both pages. Country was not explicitly stated in the source text, so it was omitted rather than inferred.
- coordinates: review — no coordinates are explicitly labeled on the page; a Google Maps link embedded in the page text contains two different numeric pairs (a "@lat,lon" map-center convention and a "!3d..!4d.." place-pin convention). Both are preserved as alternatives with reasoning; curator should confirm the correct pair before use.
- contact: found — phone "+358 (0)20 787 1680" (English page), with the same number in national format "020 787 1680" from the Finnish page kept as an alternative (formatting difference only, not a factual conflict). Website value is the external k-ruoka.fi store listing, included because its URL appears as literal text on the approved page; no shop-specific email was found (only the tourist office's general email appears in the footer, correctly excluded as not belonging to this shop).
- categories: review (as required — categories are never "found") — mapped to "supermarket" from the site's own "Grocery store"/"Ruokakauppa" tag, the closest match in the supplied Shops taxonomy.
- accessibility: missing — no accessibility statement tied to this specific shop was found (site-wide accessibility page exists but is not shop-specific, so it was not used).
- sustainability_label: missing — no named label found.
- stf_status: missing — no Sustainable Travel Finland certification statement tied to this shop; only a generic footer link to the STF program exists site-wide.
- opening_hours: missing — only a category tag ("Open 365"/"Auki 365") and an external link labeled "Opening hours"/"Aukioloajat" are present; no structured schedule or specific times appear in the stored text, so no structured value could be built. Preserved in notes for curator follow-up.
- languages_spoken: missing — not stated.
- images: not_in_scope, per schema policy for this release.

CURATOR ACTIONS NEEDED
1. Verify the correct coordinate pair for the store location (two candidates provided).
2. Confirm whether the k-ruoka.fi link should be treated as the shop's "website" contact field or dropped.
3. If precise opening hours are needed, consult the external k-ruoka.fi store page (outside this run's approved domain) or another authoritative source.
4. Confirm the "supermarket" category mapping is acceptable versus "other_shop".

No unresolved scope ambiguity remains for this run.

<!-- deterministic-appendix: do not edit -->
## Deterministic retrieval and validation summary

- Stored website pages: 2
- Page retrieval failures: 0
- Documents declared: 0
- Document/OCR limitations: 0
- Candidate links indexed: 154
- Candidate links omitted from the agent inventory: 0
- Evidence-bundle truncation/omission events: 0
- Context pages delivered: 2 of 2
- Complete context delivered before extraction: True
- Validation errors: 0
- Validation warnings: 0

### Field status table

| Field | Locale | Status | Value |
| --- | --- | --- | --- |
| name | fi | found | K-Supermarket |
| name | en | found | K-Supermarket |
| description | fi | missing |  |
| description | en | missing |  |
| address |  | found | {"city": "Hanko", "postal_code": "10900", "street": "Rewellinkatu 2"} |
| coordinates |  | review |  |
| contact |  | found | {"phone": "+358 (0)20 787 1680", "website": "https://www.k-ruoka.fi/kauppa/k-supermarket-hanko-hango"} |
| categories |  | review | ["supermarket"] |
| accessibility |  | missing |  |
| sustainability_label |  | missing |  |
| stf_status |  | missing |  |
| opening_hours |  | missing |  |
| languages_spoken |  | missing |  |
| images |  | not_in_scope |  |

### Evidence table

| Field | Locale | Source | Locator | Excerpt |
| --- | --- | --- | --- | --- |
| name | fi | p002 | line 164 | K-Supermarket |
| name | en | p001 | line 164 | K-Supermarket |
| address |  | p001 | line 167 | Rewellinkatu 2, 10900 Hanko |
| address |  | p002 | line 167 | Rewellinkatu 2, 10900 Hanko |
| contact |  | p001 | line 166 | +358 (0)20 787 1680 |
| contact |  | p001 | line 279 | Opening hours -> https://www.k-ruoka.fi/kauppa/k-supermarket-hanko-hango |
| categories |  | p001 | line 169 | Grocery store |
| categories |  | p002 | line 169 | Ruokakauppa |

### Conflict table

| Field | Locale | Alternative | Reason |
| --- | --- | --- | --- |
| coordinates |  | {"lat": 59.8286075, "lon": 22.9640597} | The '!3d..!4d..' segment of the Google Maps link is the place-pin coordinate convention used by Google Maps URLs for the mapped location. |
| coordinates |  | {"lat": 59.824871, "lon": 22.9701567} | The '@lat,lon,zoom' segment of the same URL is the map-view-center convention, which can differ from the exact place pin. |
| contact |  | {"phone": "020 787 1680"} | Same phone number shown in national-format digits on the Finnish-language page, versus international format on the English page. |

### Validation table

| Severity | Rule | Field | Message |
| --- | --- | --- | --- |
| None |  |  |  |
