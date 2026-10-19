# Agent notes

Read `TEMPLATE_NOTES.md` before deriving another mission template.

- Preserve both `mngl_######` and `emi_######` sample IDs and
  `DCIM/mongolia/` attachment paths across the QGIS project, database
  constraints, scripts, and tests.
- This repository starts with an empty observation store; once fieldwork
  begins, preserve all subsequent observations and attachments.
- Do not add field imagery, QFieldSync state, backups, or generated TIFF/MBTiles.
- The country outline is coarse and country-wide imagery is zoom 8; never
  treat either as a surveyed field-site boundary.
- Update `TEMPLATE_NOTES.md` for reusable changes and migration caveats.
- Run Python checks and scan for stale mission names before handoff.
