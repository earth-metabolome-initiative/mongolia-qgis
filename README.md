# Mongolia QField project

Project slug: `mongolia`  
Sample identifier prefix: `mngl_`

This repository derives the EMI QGIS/QField collection workflow from the
[Macedonia project](https://github.com/earth-metabolome-initiative/macedonia-qgis)
without copying its field observations, photographs, participant roster, or
regional species. The project starts with an empty observation store. The
field area is the **country of Mongolia**, not Macedonia's field-area rectangle.
No Mongolia field sites or collector roster have been supplied.

## Main files

- QGIS/QField project: `qgis/mongolia/mongolia.qgs`
- Empty observation layer: `qgis/mongolia/observations.gpkg`
- Mongolia species relation: `qgis/mongolia/species_list.gpkg`
- Collector relation: `qgis/mongolia/collector_list.gpkg` (populate before fieldwork)
- Observation subject relation: `qgis/mongolia/observation_subject.gpkg`
- Mongolia country outline: `qgis/mongolia/optimized_maps/Mongolia-EMI.gpkg`
- Offline satellite builder: `scripts/build_google_offline_basemap.py`
- Deployment and rebuild procedures: `CONTRIB.md`

## Field conventions

Identifiers match `mngl_######`; photographs use
`DCIM/mongolia/mngl_001234_01.jpg` through `_06.jpg`. Taxon names populate
lookup/display fields but never attachment filenames. `uuid_qfield` is generated
by QGIS with `uuid('WithoutBraces')`. ORCID and iNaturalist username are optional.
The collection form and QFieldCloud sync rules are carried over, but observations
start empty; configure actual collectors before deployment.

## Country-wide map strategy

A low-detail country outline replaces the small field-site polygon. A
**zoom-8** Google Satellite offline GeoTIFF replaces the Macedonia zoom-18
setting: covering all of Mongolia at zoom 18 would be impractically large.
The current 288-tile, DEFLATE-compressed z8 mosaic is about 42 MiB and
contains internal overviews. The raster is intentionally **not versioned**;
generate it locally, review the imagery provider's licensing/redistribution
terms, and package it with QField. The live online satellite layer remains a
connected fallback. At this zoom, imagery is for broad orientation, not
locating an individual specimen.
For field-scale navigation, build a separately scoped local map after field sites
are confirmed. See `CONTRIB.md` for build and offline-deployment checks.

## Taxon workflow

The default source query selects iNaturalist's Mongolia country place, rather
than the enclosing bounding box (which would include neighboring countries).
The versioned source contains 4,742 species-level iNaturalist taxa returned
for country place `7347` on 2026-10-19, without restricting iconic taxa.
The lookup contains 4,699 unique species names and 2,732 CoL higher taxa;
78 species remain explicitly unresolved. The QGIS relation selector has no
1,000-item cap, so the entire country lookup can be searched.

```bash
uv sync
uv run python scripts/fetch_inaturalist_species.py
uv run python scripts/build_col_taxon_lookup.py
ogr2ogr -f GPKG qgis/mongolia/species_list.gpkg \
  qgis/mongolia/species_list.csv -nln species_list -nlt NONE \
  -overwrite -oo EMPTY_STRING_AS_NULL=YES
```

The resolver uses the pinned Catalogue of Life 2026-07-17 XR release
(ChecklistBank `315834`, DOI `10.48580/dgykv`); unresolved names remain explicit
fallbacks. Refreshing this country-wide list requires network access; review
unresolved names before deployment.

## Checks

```bash
uv run ruff check .
uv run pytest
```
