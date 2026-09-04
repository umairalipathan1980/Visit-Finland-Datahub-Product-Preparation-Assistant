# Visit Finland DataHub preparation review

Run d58f7c555c3c — Visit Finland Shops preparation

Selected product & scope (resolved):
"Sisustuskauppa Kotilaituri", a home-decor/interior retail shop at Vuorikatu 13, 10900 Hanko, operated by the business "Sisustussuunnittelu Kotilaituri" (Y-tunnus 1315969-4). This is the single identifiable Shops product on kotilaituri.fi. The same business also runs an interior-design consulting service at a separate address (Pahkalaukkaantie 1, 21350 Ilmarinen); that service was excluded from scope as a different offering (design consultancy, not a retail shop location), not treated as a competing shop candidate.

Sources analysed:
- p001 https://www.kotilaituri.fi/ (homepage — general company description, shop teaser, brand list, seasonal hours summary)
- p002 https://www.kotilaituri.fi/yhteydenotto/ (contact page — both addresses, detailed opening hours, phone, email, business ID)
- p003 https://www.kotilaituri.fi/palvelut/ (services page — confirms the Ilmarinen address is a design-consulting service, used only to support the exclusion, no shop fields taken from it)
Two further candidate pages (SUUNNITTELIJA/menu, KOHTEET/kohde — designer bio and past design projects) were left unretrieved as they concern the design-service side of the business and the design portfolio, not the Hanko shop; they were judged non-essential to the Shops record and are noted here rather than fetched, keeping within the single-fetch-call budget. No PDFs/DOCX were supplied. No retrieval failures or JavaScript-rendering limitations were encountered. The entire site is Finnish-only; no English content exists anywhere on the domain.

Field outcomes:
- name (fi): found — "Sisustuskauppa Kotilaituri" (p002). name (en): missing — no English content exists on the site.
- description (fi): found — product/brand description from the homepage (p001). description (en): missing.
- address: found — Vuorikatu 13, 10900 Hanko (p002). Region and country were not explicitly stated and were omitted rather than inferred.
- coordinates: missing — not present in any source.
- contact: review — phone (040 7221 471) and email (kotilaituri@gmail.com) are listed once on the contact page under the registered business name, positioned beneath both the shop and the design-service addresses, so it is unclear whether this line is shop-specific or a shared company contact. Curator should confirm before publishing against the shop record.
- categories: review (required by policy) — "other_shop" selected as the best fit since no taxonomy entry precisely covers an interior/home-decor shop; "boutique" recorded as an alternative given the curated Nordic-vintage/design product mix. Curator judgement requested.
- accessibility, sustainability_label, stf_status, languages_spoken: missing — no statements found on any analysed page; none inferred, per policy.
- opening_hours: review — source gives two distinct seasonal schedules (autumn-winter: TO-PE 11-17, LA 11-15; summer "Juhannuksesta koulujen alkuun asti": MA-PE 11-17, LA 11-15, plus SU 12-15 in July only) without exact calendar boundary dates. The autumn-winter schedule was recorded as the primary structured value (consistent with the current early-September date), and the summer schedule was preserved as a full alternative with its own evidence. "Muina aikoina sopimuksesta" (other times by appointment) preserved in notes.
- images: not_in_scope, per policy — no evidence attached.

Curator actions needed:
1. Confirm whether the listed phone/email serve the Hanko shop specifically or are a shared company line also used for the design-consulting business.
2. Choose the final category between "other_shop" and "boutique" (or another taxonomy entry) for this interior/home-decor shop.
3. Confirm which seasonal opening-hours schedule (autumn-winter vs. summer) should be published as of the record's effective date, since the source does not give exact season-boundary dates.
4. No English-language content exists for this business; if an English record is required, it will need to be sourced elsewhere or left blank.

Extraction validated on first submission (no repair needed).

<!-- deterministic-appendix: do not edit -->
## Deterministic retrieval and validation summary

- Stored website pages: 3
- Page retrieval failures: 0
- Documents declared: 0
- Document/OCR limitations: 0
- Candidate links indexed: 5
- Candidate links omitted from the agent inventory: 0
- Evidence-bundle truncation/omission events: 0
- Context pages delivered: 2 of 2
- Complete context delivered before extraction: True
- Validation errors: 0
- Validation warnings: 0

### Field status table

| Field | Locale | Status | Value |
| --- | --- | --- | --- |
| name | fi | found | Sisustuskauppa Kotilaituri |
| name | en | missing |  |
| description | fi | found | Kotilaiturin sisustuskaupassa on myynnissä kattava valikoima sisustustuotteita, kuten DBKD, Ernst, Eva Solo, Gift Label, Lauritzon, Madam Stoltz, VM Carpet, Helatukku sekä kuratoi... |
| description | en | missing |  |
| address |  | found | {"city": "Hanko", "postal_code": "10900", "street": "Vuorikatu 13"} |
| coordinates |  | missing |  |
| contact |  | review | {"email": "kotilaituri@gmail.com", "phone": "040 7221 471", "website": "https://www.kotilaituri.fi/"} |
| categories |  | review | ["other_shop"] |
| accessibility |  | missing |  |
| sustainability_label |  | missing |  |
| stf_status |  | missing |  |
| opening_hours |  | review | {"notes": "Muina aikoina sopimuksesta (other times by appointment). Source also states a summer-season schedule (Juhannuksesta koulujen alkuun asti: MA-PE 11-17, LA 11-15, SU 12-1... |
| languages_spoken |  | missing |  |
| images |  | not_in_scope |  |

### Evidence table

| Field | Locale | Source | Locator | Excerpt |
| --- | --- | --- | --- | --- |
| name | fi | p002 | line 23 | Sisustuskauppa Kotilaituri |
| description | fi | p001 | line 16 | Kotilaiturin sisustuskaupassa on myynnissä kattava valikoima sisustustuotteita, kuten DBKD, Ernst, Eva Solo, Gift Label, Lauritzon, Madam Stoltz, VM Carpet, Helatukku sekä kuratoi... |
| address |  | p002 | line 24 | Vuorikatu 13, 10900 HANKO |
| contact |  | p002 | line 35 | p. 040 7221 471 |
| contact |  | p002 | line 36 | kotilaituri@gmail.com |
| contact |  | p002 | line 43 | Kotilaituri -> https://www.kotilaituri.fi/ |
| categories |  | p001 | line 16 | Kotilaiturin sisustuskaupassa on myynnissä kattava valikoima sisustustuotteita, kuten DBKD, Ernst, Eva Solo, Gift Label, Lauritzon, Madam Stoltz, VM Carpet, Helatukku sekä kuratoi... |
| opening_hours |  | p002 | line 31 | TO-PE 11-17 \| LA 11-15 |
| opening_hours |  | p001 | line 20 | syys-talvikautena TO-PE 11-17 \| LA 11-15, kesällä MA-PE 11-17 \| LA 11-15. |
| opening_hours |  | p002 | line 32 | Muina aikoina sopimuksesta. |

### Conflict table

| Field | Locale | Alternative | Reason |
| --- | --- | --- | --- |
| categories |  | ["boutique"] | The shop curates branded home-decor products alongside a selection of Nordic vintage/design items, which could also fit a small curated 'Boutique' classification instead of the ge... |
| opening_hours |  | {"notes": "Summer season: Juhannuksesta koulujen alkuun asti (from Midsummer to start of school).", "regular": [{"closes": "17:00", "days": ["monday", "tuesday", "wednesday", "thu... | Summer-season hours differ from the autumn-winter schedule chosen as the primary value; both are stated by the source but apply to different, not-precisely-dated parts of the year. |

### Validation table

| Severity | Rule | Field | Message |
| --- | --- | --- | --- |
| None |  |  |  |
