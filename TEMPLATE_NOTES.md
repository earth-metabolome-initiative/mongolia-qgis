# Template handoff notes

This repository is a clean Mongolia derivation of the
[Macedonia QGIS project](https://github.com/earth-metabolome-initiative/macedonia-qgis).
Macedonia's observation store contains active mission data and was **not**
copied as data: the Mongolia GeoPackage has the same schema, constraints and
form contract but starts with zero observations. The Macedonia collector
roster, duplicate-label investigation, photos, backup exports, field-site
coordinates and regional species lookup are not Mongolia data and were not
transferred.

## Reusable collection behavior

- Sample IDs match `mngl_######`; GeoPackage uniqueness/validation triggers
  enforce this and UUID uniqueness alongside QGIS form constraints. Reapply
  `scripts/harden_observations.sql` if the database is rebuilt. Old QField
  offline schemas/deltas must not be merged blindly after a schema change.
- The ID tab stays visible; duplication resets sample ID, UUID, attachment
  paths, coordinates and date to defaults. QGIS assigns
  `uuid('WithoutBraces')` when collecting.
- Six semantic picture fields name `DCIM/mongolia/<sample>_01.jpg` through
  `_06.jpg`; the first five are required. ORCID and iNaturalist username are
  optional. Changing picture columns requires redeploying/re-downloading the
  project before collecting or syncing offline changes.
- Collector CSV/GeoPackage stays empty until a genuine mission roster is
  provided. The Mongolia taxon source was fetched using the country place
  and its CoL-resolved lookup was built; the QGIS relation fetch limit is off
  so all 7,431 choices remain available, not just the first 1,000.
- The taxon fetcher defaults to the Mongolia country place (`MN`), not the
  country's enclosing rectangle. CoL resolution stays pinned to the published
  2026-07-17 XR dataset (`315834`, DOI `10.48580/dgykv`), with unmatched
  iNaturalist source names explicitly retained. Changing the release requires
  updating provenance and coverage expectations together.
- The satellite mosaic builder and URL attribution remain available, but the
  country-wide default uses z8 and a 1:50m Natural Earth country outline.
  The GeoTIFF uses DEFLATE rather than JPEG compression: one bundled macOS
  QGIS/GDAL build could not decode JPEG tiles due to a libjpeg ABI mismatch.
  Zoom 8 is too coarse for specimen-scale orientation; do not promise fine
  imagery without narrowing to actual field sites. The generated raster and
  MBTiles stay out of Git, require network/working GDAL to rebuild, and
  require provider-terms review before redistribution.
- QFieldCloud direct online basemap access (`no_action`), 15-minute automatic
  pushing, attachment audit, polygon-aware MBTiles pruning and dry-run-first
  append-only phone export rescue are retained. On-demand photo downloads are
  a **server** capability, not guaranteed by project configuration. Phone
  rescue must start from the last synchronized Cloud base and upload the
  consolidated **Local file**, or Cloud can overwrite rescued rows.

## Next mission substitution checklist

Change repository/project slug and QGIS title/layer IDs; identity regex;
`DCIM/<slug>/` paths; country polygon/layer and extent; offline imagery zoom,
bounds, filename and metadata; iNaturalist place; collector and species
lookups; sample IDs; and all user-facing documentation. Create an **empty**
observation store with the schema and triggers, never copy another mission's
records. Verify all layer references and relation forms in QGIS/QField and
scan for old slug, prefix, country bounds, or absolute file paths. Store
actual field-site metadata only when supplied, with its provenance.
