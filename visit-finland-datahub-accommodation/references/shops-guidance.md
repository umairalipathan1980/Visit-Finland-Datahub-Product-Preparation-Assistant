# Shops guidance

## Granularity

One identifiable retail business at one location is one Shops product. A clearly
named shopping center may itself be a Shops product when the source describes
the center as the target. Individual tenants, branches at different addresses,
and separately branded shops are separate products. Product ranges, brands,
departments, campaigns, and seasonal offers are not separate products.

Restaurants, accommodation properties, attractions, and activities operated by
the same business are different DataHub product types. Record them under
`out_of_type_facilities`; do not extract Shops fields for them and do not let
their presence block a run.

## Shared fields

The Shops schema intentionally contains only fields shared with the current
Accommodation workflow: name, description, address, coordinates, contact,
categories, accessibility, sustainability label, Sustainable Travel Finland
status, opening hours, languages spoken, and images. Do not add accommodation
capacity, pricing, booking, availability, or amenity fields to a Shops result.

## Categories

Choose only from the `shops.*` entries in
`schemas/datahub-categories.json`: Artisan, Boutique, Local Products, Market,
Outlet, Shopping Center, Souvenirs, Supermarket, and Other Shop.

Category assignment is classification. Always use status `review` or
`missing`, never `found`, and attach evidence supporting every suggestion.
Do not substitute an Accommodation or amenity category. Use
`shops.other_shop` only when the evidence clearly describes a shop but does
not support one of the more specific Shops categories.

## Evidence cautions

Do not treat a product brand, shopping-center tenant, or store locator result as
the selected shop unless the source ties it to the scoped business and location.
Opening hours and contact details must belong to the selected location. Never
merge details from different branches.
