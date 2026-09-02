# General curation principles

These apply across every field, not just the ones named explicitly elsewhere.

- **Evidence before inference.** A value is `found` only if a stored page or
  document states it. If you would need to infer it from a photo, a room
  name, or general knowledge about Finland, it is not `found` -- it is
  `missing` or `review`.
- **One product per run.** This PoC produces exactly one Accommodation
  record. If the sources describe more than one, that is a scope problem
  (Stage 4), not an extraction problem.
- **Conflicts are data, not noise.** If the Finnish and English pages disagree
  on capacity, or the homepage and a PDF brochure disagree on address, keep
  both as alternatives under `review` with a stated reason. Do not average,
  guess, or silently prefer one source over another.
- **Silence is not "no".** A missing accessibility statement is `missing`,
  never a `false` accessibility value. The same applies to sustainability
  labels and STF status.
- **Provisional schema.** This package's schemas and category list are a PoC
  transcription (see `schemas/schema-version.json`), not an official DataHub
  export. Never describe a result as "DataHub-valid" -- only as valid against
  `poc-accommodation-schema-v1`.
