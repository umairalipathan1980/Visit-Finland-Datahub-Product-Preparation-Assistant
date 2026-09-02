# Accommodation guidance

## Granularity

One hotel, hostel, B&B, apartment building, or cottage village is one
Accommodation product. The following are **not** separate products and must
not be extracted as if they were: individual room types, packages, seasonal
offers, single cottages within a village that share one management/booking
system, and campaigns.

A restaurant, spa, or meeting-facility operated by the same business is a
**different** DataHub product type. Record it under `out_of_type_facilities`
in `work/scope-decision.json`; do not extract Accommodation fields for it and
do not let its presence block the run.

## Field notes

- `categories`: choose from `schemas/datahub-categories.json` only. This file
  is a small, fixed PoC subset (about 20 entries, not DataHub's full
  taxonomy) -- if the business's type is not in the list, choose the closest
  match and note the gap in the review report rather than inventing a new
  category id. **Always write category status as `review`, never `found`,**
  even when the match is obvious (a page that literally says "hotelli" still
  only supports `review` for `accommodation.hotel`) -- assigning a category
  id is a classification judgment, not a quoted fact, and a curator confirms
  it either way. `missing` is correct and unremarkable when nothing on the
  site supports any category; do not force a guess to avoid an empty field.
  Attach evidence to every suggested category regardless of its `review`
  status, the same as any other field.
- `accessibility`: tri-state (`accessible` / `non_accessible` / `not_specified`).
  `not_specified` is the correct, expected output whenever no source
  addresses it -- it is not a lower-quality answer than the other two.
- `stf_status`: tri-state (`certified` / `not_certified` / `not_specified`),
  and specifically about the named Sustainable Travel Finland program --
  see `references/field-semantics.md` for how it differs from
  `sustainability_label`. A general eco-friendly claim is not evidence for
  this field; only a claim naming the certification is.
- `pricing`: `unit` is one of `Person`/`Hour`/`Day`/`Week`; `type` is one of
  `Chargeable`/`Free`/`Not Known`. Extract only values a page or document
  states directly. When a source explicitly describes dynamic/variable
  pricing rather than a fixed rate, use `type: "Not Known"` and put the
  description (e.g. "varies by date, guest count, and length of stay") in
  `notes` rather than leaving the field bare.
- `booking_url`: must point to an actual booking/reservation destination, not
  a general contact form. It is commonly a third-party domain (a booking
  engine, a channel manager) -- that is expected and fine to cite. Look for
  it in the `--- LINKS ---` section `fetch_pages.py` appends to each stored
  page, or in the page's `external_links`/`internal_links` metadata; the
  evidence excerpt is the link line as it appears in stored text, and the
  cited source is the page that links to it, never the destination itself.
- `availability`: `open_year_round` and `minimum_stay_nights` only when a
  source states them; put anything more specific (seasonal minimum-stay
  changes, blackout dates) in `notes` as free text rather than forcing it
  into the two structured sub-fields.
- `capacity`: rooms/beds as stated. If a room-count page and a marketing page
  disagree, that is a `review` conflict.
