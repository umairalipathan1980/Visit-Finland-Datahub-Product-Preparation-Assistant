// Mirrors the product-specific workflow field semantics.
// Kept in sync by hand; this PoC has no shared generated schema package.

export type FieldKind = "localized-text" | "object" | "array" | "enum" | "text" | "json";

export interface FieldSpec {
  key: string;
  label: string;
  kind: FieldKind;
  subfields?: { key: string; label: string; type: "text" | "number" | "boolean" }[];
  options?: string[];
}

const COMMON_FIELD_SPECS: FieldSpec[] = [
  { key: "name", label: "Name", kind: "localized-text" },
  { key: "description", label: "Description", kind: "localized-text" },
  {
    key: "address", label: "Address", kind: "object",
    subfields: [
      { key: "street", label: "Street", type: "text" },
      { key: "postal_code", label: "Postal code", type: "text" },
      { key: "city", label: "City", type: "text" },
      { key: "region", label: "Region", type: "text" },
      { key: "country", label: "Country", type: "text" },
    ],
  },
  {
    key: "coordinates", label: "Coordinates", kind: "object",
    subfields: [
      { key: "latitude", label: "Latitude", type: "number" },
      { key: "longitude", label: "Longitude", type: "number" },
    ],
  },
  {
    key: "contact", label: "Contact", kind: "object",
    subfields: [
      { key: "email", label: "Email", type: "text" },
      { key: "phone", label: "Phone", type: "text" },
      { key: "website", label: "Website", type: "text" },
    ],
  },
  { key: "categories", label: "Categories", kind: "array" },
  { key: "accessibility", label: "Accessibility", kind: "enum", options: ["accessible", "non_accessible", "not_specified"] },
  { key: "sustainability_label", label: "Sustainability label", kind: "enum", options: ["true", "false", "not_specified"] },
  { key: "stf_status", label: "Sustainable Travel Finland status", kind: "enum", options: ["certified", "not_certified", "not_specified"] },
  { key: "opening_hours", label: "Opening hours", kind: "json" },
  { key: "languages_spoken", label: "Languages spoken", kind: "array" },
];

const ACCOMMODATION_ONLY_FIELD_SPECS: FieldSpec[] = [
  {
    key: "capacity", label: "Capacity", kind: "object",
    subfields: [
      { key: "rooms", label: "Rooms", type: "number" },
      { key: "beds", label: "Beds", type: "number" },
    ],
  },
  {
    key: "pricing", label: "Pricing", kind: "object",
    subfields: [
      { key: "unit", label: "Unit", type: "text" },
      { key: "type", label: "Type", type: "text" },
      { key: "amount", label: "Amount", type: "number" },
    ],
  },
  { key: "booking_url", label: "Booking URL", kind: "text" },
  {
    key: "availability", label: "Availability", kind: "object",
    subfields: [
      { key: "open_year_round", label: "Open year-round", type: "boolean" },
      { key: "minimum_stay_nights", label: "Minimum stay (nights)", type: "number" },
      { key: "notes", label: "Notes", type: "text" },
    ],
  },
  { key: "amenities", label: "Amenities", kind: "array" },
];

const IMAGES_FIELD: FieldSpec = { key: "images", label: "Images", kind: "text" };

export function getFieldSpecs(productType: string): FieldSpec[] {
  if (productType === "shops") return [...COMMON_FIELD_SPECS, IMAGES_FIELD];
  return [...COMMON_FIELD_SPECS, ...ACCOMMODATION_ONLY_FIELD_SPECS, IMAGES_FIELD];
}

export const STATUS_LABELS: Record<string, string> = {
  found: "Found",
  review: "Needs review",
  missing: "Missing",
  not_in_scope: "Not in scope",
};
