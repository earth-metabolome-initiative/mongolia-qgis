# Contributing to the Mongolia QField project

## Boundary and project extent

`qgis/mongolia/optimized_maps/Mongolia-EMI.kml` and `Mongolia-EMI.gpkg`
represent Mongolia's actual national polygon, not its rectangular bounding
box. Source: [Natural Earth 1:50m Admin-0 Countries](https://naturalearth.s3.amazonaws.com/50m_cultural/ne_50m_admin_0_countries.zip),
feature `ADMIN=Mongolia`, `ISO_A2=MN` (public domain). Its EPSG:4326 bounding
box is `87.7431640625,41.5955078125,119.8978515625,52.11728515625`.
A 1:50m outline is suitable for country-scale orientation, not cadastral work
or resolving contested borders. When updating either geometry, keep the
GeoPackage layer name `Mongolia_EMI`, QGIS data source and country bounds in
sync. If `ogr2ogr` is available, rebuild from the KML with:

```bash
ogr2ogr -f GPKG qgis/mongolia/optimized_maps/Mongolia-EMI.gpkg \
  qgis/mongolia/optimized_maps/Mongolia-EMI.kml \
  -nln Mongolia_EMI -overwrite
```

No field coordinates or tracks were supplied; do not invent field locations.

## Building the species lookup

The default fetch uses iNaturalist's Mongolia place. Filtering by its country
place excludes observations from neighboring countries that lie inside the
country bounding rectangle. It is unfiltered by iconic taxon:

```bash
uv run python scripts/fetch_inaturalist_species.py
uv run python scripts/build_col_taxon_lookup.py
ogr2ogr -f GPKG qgis/mongolia/species_list.gpkg \
  qgis/mongolia/species_list.csv -nln species_list -nlt NONE \
  -overwrite -oo EMPTY_STRING_AS_NULL=YES
```

The published Catalogue of Life 2026-07-17 XR release is pinned as
ChecklistBank dataset `315834` (DOI `10.48580/dgykv`); inspect
`col_match_type=unresolved` rows before deployment. Do not accept a genus-level
match as a species resolution. Regenerating the list requires internet access;
Mongolia's complete country-scale list may be substantially larger than a
single field site. The collector CSV and GeoPackage contain Emmanuel Defossez
and Pierre-Marie Allard (details from the
[Macedonia collector CSV](https://github.com/earth-metabolome-initiative/macedonia-qgis/blob/main/qgis/macedonia/collector_list.csv)),
plus Neil Villard (name supplied for this project; other fields unknown).
Keep both lookup files in sync when adding or correcting observers.

## Offline background

The buffered imagery bounds cover the country at zoom 8, rather than attempting
a huge zoom-18 country mosaic. Nominal ground resolution at ~47°N is roughly
417 m/pixel; the raster is for orientation, not specimen-scale wayfinding.
The online satellite layer remains underneath as a connected fallback.

```bash
python3 scripts/build_google_offline_basemap.py \
  --output qgis/mongolia/optimized_maps/mongolia_google_satellite_z8.tif \
  --force
```

The builder writes a tiled **DEFLATE-compressed** GeoTIFF with overviews and
source metadata. DEFLATE is lossless and avoids dependence on QGIS's JPEG
decoder, which is incompatible with libjpeg in some packaged macOS builds.
Run it from the repository root with working GDAL `gdal_translate` and
`gdaladdo` binaries on `PATH`; rebuilding requires network access. The output
is ignored by Git and must be transferred via the QField packaging/deployment
workflow. Review
[Google Maps terms](https://www.google.com/help/terms_maps/) before storing or
redistributing imagery; neither availability nor redistribution rights follow
from the builder. If a smaller field area is established, prefer a separate
local high-resolution offline map over increasing the country mosaic's zoom.
Generated MBTiles stay out of Git; `scripts/prune_mbtiles_to_polygon.py` can
trim a separately generated MBTiles map for deployment.

## Attachment protection

QField automatically pushes changes every 15 minutes while open and online.
If the QFieldCloud deployment supports on-demand attachment downloads, enable
that server-side option only after checking the active Cloud file inventory
and an independent downloaded photo archive. It is not itself a backup. Before
any local photo is removed, sync each collecting device, keep its originals,
and audit the live database against both inventories:

```bash
python3 scripts/audit_observation_attachments.py \
  --database qgis/mongolia/observations.gpkg \
  --cloud-files-json /path/to/qfieldcloud-files.json
python3 scripts/audit_observation_attachments.py \
  --database qgis/mongolia/observations.gpkg \
  --attachments-root /path/to/archive-root \
  --manifest-out /path/to/archive-manifest.json
```

The archive root contains `DCIM/mongolia/`. The audit rejects missing/empty
required references, unexpected attachment names, duplicates, missing inventory
files, and zero-byte files. On-demand support depends on the deployed server;
confirm it there instead of assuming the project XML enables it.

## Rescuing a QField device export

Keep each phone export separate **outside Git**, including its `data.gpkg`,
`deltafile.json` and `DCIM/mongolia/` photos. Freeze normal synchronization,
let healthy devices push, synchronize the latest Cloud file locally once, then
close QGIS. Do not pull from Cloud while recovering phones. Inspect the default
read-only dry run before applying:

```bash
python3 scripts/merge_qfield_device_export.py /path/to/phone-export
python3 scripts/merge_qfield_device_export.py /path/to/phone-export \
  --apply --report-out /path/to/external-recovery-log/phone-export.json
```

The merge is append-only: identity/schema/attachment conflicts stop it, a
validated candidate is swapped atomically, and attachments are collision
checked. `--keep-target-existing` is only for reviewed same-ID/same-UUID
attribute differences with a newer base; it never permits reused identities.
Process one phone at a time, retain each original export/report, and check the
observation and attachment counts. After all merges, choose **Local file** in
QFieldSync for `observations.gpkg` to upload the consolidated store; choosing
**Cloud file** discards the rescued rows. Verify on a pilot device before other
devices sync. A different attachment source may be passed with
`--source-attachments-root`.

## Release checks

1. Open `qgis/mongolia/mongolia.qgs`; confirm no broken vector layers and that
   the country outline and extent cover Mongolia.
2. Review the three collector lookup entries, complete any missing details
   when supplied, and verify the Mongolia species relation before fieldwork.
3. Create test observations with both `mngl_######` and `emi_######`,
   distinct UUIDs, and all six `DCIM/mongolia/<sample_id>_NN.jpg` attachment
   paths for each; check relation forms and optional ORCID.
4. Run `uv run ruff check .` and `uv run pytest`.
5. Repackage from the updated GeoPackage, not earlier `.qfieldsync/` snapshots;
   download afresh to a QField test device. In airplane mode verify the
   offline z8 layer is visible; inspect zoomed-out and field-scale limits.
6. Audit attachment inventory and independent archive before retiring media.
7. Check repository size: no field photos, device exports, generated TIFFs,
   backups, or MBTiles should enter Git.
