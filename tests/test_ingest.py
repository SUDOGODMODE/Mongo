from pathlib import Path

from ingest import EVAL_IDS, choose_incidents, load_json, load_xml, normalize_incident

ROOT = Path(__file__).resolve().parents[1]
JSON = ROOT / "import" / "incidents_sample_50.json"
XML = ROOT / "import" / "incidents_sample_50.xml"


def test_both_formats_produce_incident_dictionaries():
    json_rows = load_json(JSON)
    xml_rows = load_xml(XML)
    assert len(json_rows) == len(xml_rows) == 50
    assert json_rows[0]["incident_id"] == "INC-2026-00002"
    assert xml_rows[0]["incident_id"] == "INC-2026-00001"


def test_invalid_date_is_rejected():
    row = next(x for x in load_json(JSON) if x["incident_id"] == "INC-2026-00004")
    document, errors = normalize_incident(row, "json")
    assert document is None
    assert any("zeitpunkt" in error for error in errors)


def test_missing_service_and_bad_severity_are_rejected():
    rows = {x["incident_id"]: x for x in load_xml(XML)}
    for incident_id, field in (
        ("INC-2026-00013", "system_service"),
        ("INC-2026-00025", "schweregrad"),
    ):
        document, errors = normalize_incident(rows[incident_id], "xml")
        assert document is None
        assert any(field in error for error in errors)


def test_missing_solution_is_allowed():
    document, errors = normalize_incident(load_xml(XML)[0], "xml")
    assert errors == []
    assert document["bekannte_loesung"] is None
    assert document["source_format"] == "xml"


def test_dataset_selection_is_stable_and_contains_ten_evaluation_cases():
    valid = []
    for source, rows in (("json", load_json(JSON)), ("xml", load_xml(XML))):
        for row in rows:
            document, errors = normalize_incident(row, source)
            if not errors:
                valid.append(document)
    first = choose_incidents(valid)
    second = choose_incidents(list(reversed(valid)))
    assert len(first) == 30
    assert [row["incident_id"] for row in first] == [row["incident_id"] for row in second]
    assert set(EVAL_IDS) <= {row["incident_id"] for row in first}


def test_non_object_json_row_is_returned_for_individual_validation(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"incidents":[{"incident_id":"INC-2026-00001"},42]}')
    rows = load_json(path)
    assert len(rows) == 2
    document, errors = normalize_incident(rows[1], "json")
    assert document is None
    assert errors == ["incident: expected an object"]
