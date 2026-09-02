# Visit Finland DataHub preparation review

Run 7cefa6fa19fc — Visit Finland Shops preparation

PRODUCT & SCOPE
Selected product type: Shops. Scope resolved without ambiguity to a single business: "Design PURO Casa & Shop," an interior-design/lifestyle shop at Vuorikatu 15, 10900 Hanko. Two sources describe this same business/location: the English product page (p001, visithanko.fi/en/tuotesivu/design-puro-casa-shop-3) and its Finnish counterpart (p002, visithanko.fi/tuotesivu/design-puro-casa-shop). No competing candidate shop was found; the only alternative "products" visible were the site's global navigation links to entirely different businesses (restaurants, accommodation, other shops such as Anna Berner, M. Broman, Helkama, etc.), which were excluded as unrelated navigation, not competing scope for this shop.

SOURCES ANALYSED
- p001 (English product page, seed page): full page text and link list read.
- p002 (Finnish product page): fetched as the one permitted selection call, to populate the required localized `fi` fields for name and description, since the seed page is English-only.
No second (recovery) fetch was used — the two language variants of the same product page were sufficient for the shared-field schema. The Swedish variant (l003) and generic town-wide theme pages (Accessibility, Shops-and-stores category listings) were identified as candidates but not fetched: the theme pages are not tied specifically to this business and would not have supported `found` values under the evidence-cautions guidance, and the Swedish page was not needed once English and Finnish were both captured.

FIELD RESULTS
- name (fi/en): found — "Design PURO Casa & Shop" on both language pages.
- description (fi/en): found — distinct localized descriptions preserved separately, not translated. The Finnish text is notably more detailed (mentions fitted furniture, kitchenware/spices, women's clothing) than the shorter English summary; both are kept verbatim rather than merged.
- address: found — "Vuorikatu 15, 10900 Hanko" (structured as street/postal_code/city). Note: the description text references "Vuorikatu 15-17" as the shop's frontage, while the discrete address block states "Vuorikatu 15"; both wordings are preserved in notes for curator awareness (not a hard conflict, but worth confirming the correct street-number range).
- coordinates: missing — no coordinates are stated in page prose. A Google Maps link on the page encodes coordinates in its URL, but per policy external link targets are not fetched/interpreted, so this was deliberately not treated as an explicit coordinate statement.
- contact: found — phone "040 715 1107", email "info@purocasa.fi", website "https://www.purocasa.fi/" (website value recorded as literal text from the approved page; the external purocasa.fi site itself was never fetched or cited).
- categories: review (as required — categories are never `found`). Primary suggestion "other_shop", because the business is described as a full-service interior-design/lifestyle store selling furniture, kitchenware, spices, and women's clothing, which doesn't map cleanly onto one specific Shops taxonomy label. Alternative "boutique" is recorded with reasoning (site tags it "fashion"/"Muoti" and mentions individual women's clothing). No taxonomy entry exists for "Interior"/"Sisustus," which is the site's own third tag — curator judgment is needed to finalize the category.
- accessibility, sustainability_label, stf_status, languages_spoken: all missing — no shop-specific evidence found on the fetched pages. Generic town-wide Accessibility and STF-program links exist in site navigation/footer but do not state anything specific to this shop, so per policy silence was recorded as missing rather than inferred.
- opening_hours: missing — both language pages show an "Opening hours:"/"Aukioloajat:" label with no following schedule text in the retrieved static HTML; this looks like a JavaScript-rendered or dynamically-loaded widget not available to this tool's static retrieval capability (javascript_rendering: false was reported by prepare_sources).
- images: not_in_scope, per schema.

LIMITATIONS
- No JavaScript rendering capability — likely cause of the missing opening-hours schedule.
- No documents (PDF/DOCX) were supplied or relevant to this shop.
- External domains (purocasa.fi, Instagram, Google Maps, Facebook) were correctly treated as discovery-only and never fetched or cited beyond their literal link text on the approved visithanko.fi pages.
- The Swedish-language variant of the product page was not fetched; if the run is repeated with an expanded fetch budget, it could be checked for any additional or conflicting details.

VALIDATION
submit_extraction returned valid on the first submission (no repair needed).

CURATOR ACTIONS NEEDED
1. Confirm final Shops category: "other_shop" vs. "boutique" (see categories field alternatives).
2. Verify whether the shop's address street number is "15" or "15-17" (minor wording inconsistency between the description and the address block).
3. Consider contacting the shop directly for opening hours, accessibility, sustainability, STF status, and languages spoken, none of which were available in the retrieved static content.

<!-- deterministic-appendix: do not edit -->
## Deterministic retrieval and validation summary

- Stored website pages: 2
- Page retrieval failures: 0
- Documents declared: 0
- Document/OCR limitations: 0
- Candidate links indexed: 156
- Candidate links omitted from the agent inventory: 0
- Evidence-bundle truncation/omission events: 0
- Context pages delivered: 2 of 2
- Complete context delivered before extraction: True
- Validation errors: 0
- Validation warnings: 0

### Field status table

| Field | Locale | Status | Value |
| --- | --- | --- | --- |
| name | fi | found | Design PURO Casa & Shop |
| name | en | found | Design PURO Casa & Shop |
| description | fi | found | Design PURO Casa & Shop tarjoaa Hangossa, Vuorikatu 15-17:ssa täyden palvelun sisustussuunnittelua. Suunnittelemme myös kiintokalusteet kuten kaapistot ja keittiöt. Valikoimistamm... |
| description | en | found | Design PURO Casa & Shop – interior design shop on Vuorikatu 15-17, Hanko. This lifestyle store is open all year round. |
| address |  | found | {"city": "Hanko", "postal_code": "10900", "street": "Vuorikatu 15"} |
| coordinates |  | missing |  |
| contact |  | found | {"email": "info@purocasa.fi", "phone": "040 715 1107", "website": "https://www.purocasa.fi/"} |
| categories |  | review | ["other_shop"] |
| accessibility |  | missing |  |
| sustainability_label |  | missing |  |
| stf_status |  | missing |  |
| opening_hours |  | missing |  |
| languages_spoken |  | missing |  |
| images |  | not_in_scope |  |

### Evidence table

| Field | Locale | Source | Locator | Excerpt |
| --- | --- | --- | --- | --- |
| name | fi | p002 | line 164 | Design PURO Casa & Shop |
| name | en | p001 | line 164 | Design PURO Casa & Shop |
| description | fi | p002 | line 165 | Design PURO Casa & Shop tarjoaa Hangossa, Vuorikatu 15-17:ssa täyden palvelun sisustussuunnittelua. Suunnittelemme myös kiintokalusteet kuten kaapistot ja keittiöt. Valikoimistamm... |
| description | en | p001 | line 165 | Design PURO Casa & Shop – interior design shop on Vuorikatu 15-17, Hanko. This lifestyle store is open all year round. |
| address |  | p001 | line 172 | Vuorikatu 15, 10900 Hanko |
| contact |  | p001 | line 168 | 040 715 1107 |
| contact |  | p001 | line 169 | info@purocasa.fi |
| contact |  | p001 | line 170 | purocasa.fi |
| categories |  | p001 | line 173-175 | fashion Interior Shops |
| categories |  | p002 | line 173-175 | Muoti Putiikit ja puodit Sisustus |

### Conflict table

| Field | Locale | Alternative | Reason |
| --- | --- | --- | --- |
| categories |  | ["boutique"] | The site tags the shop under 'fashion'/'Muoti' and the description mentions individual women's clothing, which could support a Boutique classification. However, the shop is descri... |

### Validation table

| Severity | Rule | Field | Message |
| --- | --- | --- | --- |
| None |  |  |  |
