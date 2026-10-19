from __future__ import annotations

import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
PROJECT = ROOT / "qgis/mongolia/mongolia.qgs"
MAPS = ROOT / "qgis/mongolia/optimized_maps"


def test_country_geometry_is_mongolia_not_a_rectangular_extent() -> None:
    kml = ET.parse(MAPS / "Mongolia-EMI.kml").getroot()
    rings = kml.findall(".//{*}outerBoundaryIs/{*}LinearRing/{*}coordinates")
    assert rings
    points = [
        tuple(map(float, token.split(",")[:2]))
        for ring in rings
        for token in (ring.text or "").split()
    ]
    west = min(point[0] for point in points)
    east = max(point[0] for point in points)
    south = min(point[1] for point in points)
    north = max(point[1] for point in points)
    assert len(points) > 50
    assert 87.7 < west < 87.8
    assert 119.8 < east < 120
    assert 41.5 < south < 41.7
    assert 52 < north < 52.2

    with sqlite3.connect(MAPS / "Mongolia-EMI.gpkg") as connection:
        contents = connection.execute(
            "SELECT table_name, srs_id, min_x, min_y, max_x, max_y "
            "FROM gpkg_contents WHERE table_name='Mongolia_EMI'"
        ).fetchone()
        assert contents is not None
        assert contents[:2] == ("Mongolia_EMI", 4326)
        assert contents[2:] == pytest.approx((west, south, east, north), abs=0.001)
        assert connection.execute("SELECT COUNT(*) FROM Mongolia_EMI").fetchone()[0] == 1


def test_collector_lookup_contains_requested_observers() -> None:
    with sqlite3.connect(ROOT / "qgis/mongolia/collector_list.gpkg") as connection:
        rows = connection.execute(
            "SELECT fullname, email, ORCID FROM collector_list "
            "WHERE fullname IN (?, ?, ?) ORDER BY fullname",
            ("Emmanuel Defossez", "Neil Villard", "Pierre-Marie Allard"),
        ).fetchall()
    assert [row[0] for row in rows] == [
        "Emmanuel Defossez",
        "Neil Villard",
        "Pierre-Marie Allard",
    ]
    assert rows[0][1:] == ("emmanuel.defossez@unine.ch", "0000-0002-3279-9190")
    assert rows[2][1:] == ("pierre-marie.allard@unifr.ch", "0000-0003-3389-2191")


def test_mongolia_species_lookup_is_populated_from_country_observations() -> None:
    with sqlite3.connect(ROOT / "qgis/mongolia/species_list.gpkg") as connection:
        species = connection.execute(
            "SELECT ScientificName, lookup_type FROM species_list "
            "WHERE inat_taxon_id = '46080'"
        ).fetchone()
        assert species is not None
        assert species[1] == "species"
        assert connection.execute(
            "SELECT COUNT(*) FROM species_list WHERE lookup_type = 'higher_taxon'"
        ).fetchone()[0] > 0


@pytest.mark.parametrize("reharden", [False, True])
def test_database_enforces_mongolia_sample_identity(tmp_path: Path, reharden: bool) -> None:
    # Isolation: SQLite's backup API keeps all indexes and constraints intact.
    database = sqlite3.connect(ROOT / "qgis/mongolia/observations.gpkg")
    replica = sqlite3.connect(tmp_path / "observations.gpkg")
    try:
        database.backup(replica)
        if reharden:
            replica.executescript((ROOT / "scripts/harden_observations.sql").read_text())
    finally:
        database.close()
    try:
        # Spatial-index triggers call these GDAL functions even for null geometry.
        for name in ("ST_MinX", "ST_MaxX", "ST_MinY", "ST_MaxY"):
            replica.create_function(name, 1, lambda _geometry: None)
        replica.create_function("ST_IsEmpty", 1, lambda _geometry: 1)
        uuid1 = "00000000-0000-4000-8000-000000000001"
        uuid2 = "00000000-0000-4000-8000-000000000002"
        uuid3 = "00000000-0000-4000-8000-000000000003"
        replica.execute(
            "INSERT INTO observations(sample_id, uuid_qfield) VALUES (?, ?)",
            ("mngl_000001", uuid1),
        )
        replica.execute(
            "INSERT INTO observations(sample_id, uuid_qfield) VALUES (?, ?)",
            ("emi_000001", uuid2),
        )
        for sample_id, uuid in (
            ("mcdn_000001", uuid3),
            ("mngl_1", uuid3),
            ("emi_1", uuid3),
            ("emi_0000000", uuid3),
            ("emi_00000a", uuid3),
            ("emi_000001 ", uuid3),
            ("mngl_000001", uuid3),
            ("emi_000001", uuid3),
            ("mngl_000002", uuid1),
            ("emi_000002", uuid1),
        ):
            with pytest.raises(sqlite3.IntegrityError):
                replica.execute(
                    "INSERT INTO observations(sample_id, uuid_qfield) VALUES (?, ?)",
                    (sample_id, uuid),
                )
        with pytest.raises(sqlite3.IntegrityError):
            replica.execute(
                "UPDATE observations SET sample_id = ? WHERE sample_id = ?",
                ("emi_00000a", "mngl_000001"),
            )
        replica.execute(
            "UPDATE observations SET sample_id = ? WHERE sample_id = ?",
            ("emi_000002", "mngl_000001"),
        )
        replica.execute(
            "UPDATE observations SET sample_id = ? WHERE sample_id = ?",
            ("mngl_000001", "emi_000002"),
        )
    finally:
        replica.close()


def test_project_can_collect_with_country_appropriate_references() -> None:
    root = ET.parse(PROJECT).getroot()
    layers = {layer.findtext("layername"): layer for layer in root.findall(".//maplayer")}
    observations = layers["observations"]
    assert observations.findtext("datasource") == "./observations.gpkg|layername=observations"
    sample_tab = observations.find(".//attributeEditorContainer[@name='sample_id']")
    assert sample_tab is not None and sample_tab.get("visibilityExpressionEnabled") == "0"
    assert root.findtext(".//forceAutoPushIntervalMins") == "15"
    satellite = layers["satellite (offline — Google z8)"]
    assert satellite.findtext("datasource") == (
        "./optimized_maps/mongolia_google_satellite_z8.tif"
    )
    assert satellite.get("hasScaleBasedVisibilityFlag") == "0"
    assert satellite.findtext("provider") == "gdal"
    assert satellite.find(".//Option[@name='QFieldSync/cloud_action']").get("value") == "no_action"
    online = layers["google-earth-connection"]
    assert online.find(".//Option[@name='QFieldSync/cloud_action']").get("value") == "no_action"


def test_species_selector_can_reach_all_country_taxa() -> None:
    root = ET.parse(PROJECT).getroot()
    observations = next(
        layer for layer in root.findall(".//maplayer")
        if layer.findtext("layername") == "observations"
    )
    selector = observations.find(
        "./fieldConfiguration/field[@name='taxon_name']/editWidget/"
        "config/Option/Option[@name='FetchLimitActive']"
    )
    assert selector is not None
    assert selector.get("value") == "false"
