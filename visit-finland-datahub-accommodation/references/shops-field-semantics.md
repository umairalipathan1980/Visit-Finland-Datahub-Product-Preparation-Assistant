# Shops shared-field semantics

This is a local PoC Shops contract, not an authoritative transcription of the
Visit Finland DataHub import schema. Every field uses the status/evidence
envelope in `schemas/shops-extraction.schema.json`.

- `name`: official shop or shopping-center name, localized independently for
  Finnish and English. Do not translate.
- `description`: product description stated by the source, localized
  independently. Do not assemble marketing claims from unrelated branches.
- `address`: structured street, postal code, city, region, and country when
  explicitly available for the selected location.
- `coordinates`: latitude and longitude only when explicitly present in a
  citable source.
- `contact`: email, phone, and website belonging to the selected shop and
  location.
- `categories`: a list of `shops.*` identifiers from the supplied local
  taxonomy. Category status is always `review` or `missing`.
- `accessibility`: `accessible`, `non_accessible`, or `not_specified`.
  Never infer accessibility from photos or absence of a warning.
- `sustainability_label`: only an explicitly named sustainability label or
  certification.
- `stf_status`: `certified`, `not_certified`, or `not_specified`, and
  only for the named Sustainable Travel Finland program.
- `opening_hours`: use the structured schedule defined in
  `references/opening-hours.md`. Hours must belong to the selected location;
  preserve seasonal or exceptional wording in notes.
- `languages_spoken`: languages explicitly offered by the selected business.
- `images`: always `not_in_scope` in this release and carries no evidence.
