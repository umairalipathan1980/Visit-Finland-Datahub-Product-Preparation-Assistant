# Structured opening hours

Both Accommodation and Shops use the same structured `opening_hours.value`
object. Do not return a string and do not invent keys based on source wording.

Use this shape:

```json
{
  "regular": [
    {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "opens": "10:00",
      "closes": "18:00"
    },
    {
      "days": ["saturday", "sunday"],
      "closed": true
    }
  ],
  "exceptions": [
    {
      "date": "2026-12-24",
      "opens": "10:00",
      "closes": "14:00",
      "notes": "Christmas Eve"
    }
  ],
  "notes": "Seasonal hours may vary."
}
```

Rules:

- Day names are lowercase English values from Monday through Sunday.
- Times use 24-hour `HH:MM` format.
- Every regular entry has one or more days and either an opening/closing pair,
  `closed: true`, or a source-faithful note.
- Exceptions identify a date or a source label such as "Public holidays".
- Omit `regular`, `exceptions`, or `notes` when the source does not
  support them.
- Use field status `missing` when no hours are available. Use `review` with
  alternatives when sources conflict.
- Keep hours for other facilities, tenants, or branches out of the scoped
  product's value.
