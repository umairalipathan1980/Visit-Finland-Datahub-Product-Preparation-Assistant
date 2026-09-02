# Field semantics and enumerated value spaces

Pinned here rather than left to judgment, per `schemas/accommodation-extraction.schema.json`.

| Field | Shape | Closed vocabulary |
| --- | --- | --- |
| `name`, `description` | localized (`fi`/`en`), each independently found/review/missing | -- |
| `address` | object: `street`, `postal_code`, `city`, `region`, `country` | -- |
| `coordinates` | object: `latitude`, `longitude` (decimal degrees) | -- |
| `contact` | object: `email`, `phone`, `website` | -- |
| `categories` | array of category id strings, **status always `review` or `missing`, never `found`** | `schemas/datahub-categories.json` (fixed ~20-entry PoC subset, `complete: false`) |
| `accessibility` | single value | `accessible` \| `non_accessible` \| `not_specified` |
| `sustainability_label` | single value | `true` \| `false` \| `not_specified` |
| `stf_status` | single value | `certified` \| `not_certified` \| `not_specified` |
| `capacity` | object: `rooms`, `beds` (integers) | -- |
| `pricing` | object: `unit`, `type`, `amount` | `unit`: `Person`\|`Hour`\|`Day`\|`Week`; `type`: `Chargeable`\|`Free`\|`Not Known` |
| `booking_url` | string (uri) | must resolve to a booking/reservation destination |
| `availability` | object: `open_year_round` (bool), `minimum_stay_nights` (integer), `notes` (string) | -- |
| `opening_hours` | structured object | use the exact shared format in `references/opening-hours.md` |
| `amenities` | array of strings | free text, prefer terms from `datahub-categories.json`'s `amenity.*` entries where they match |
| `languages_spoken` | array of ISO-639-1-ish strings (`fi`, `en`, `sv`, ...) | -- |
| `images` | always `not_in_scope` | -- |

`not_specified` (accessibility, STF) and `Not Known` (pricing type) are the
correct output whenever no source addresses the field -- never omit the
field or guess a different value to avoid an empty-looking answer.

**`stf_status` and `sustainability_label` are not the same claim.**
`stf_status` is specifically the named **Sustainable Travel Finland**
certification program -- `found`/`certified` requires the source to name
that certification or link to its official listing, not general
"eco-friendly", "green", or "sustainable practices" marketing language.
`sustainability_label` is the broader, unbranded claim and accepts that
looser marketing language. A page saying "we care about the environment"
supports `sustainability_label: true` but never `stf_status: certified` --
downgrade `stf_status` to `not_specified` rather than treating a general
sustainability claim as evidence of the specific certification.

Categories are the one field where `found` is never correct, at any
confidence level: mapping evidence to a category id is classification, not
extraction, so the ceiling is `review`. `scripts/validate_extraction.py`
enforces this and downgrades a `found` category unconditionally.
