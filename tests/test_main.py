import json
from pathlib import Path
from uuid import uuid4

from pymongo import MongoClient

from main import load_json, load_xml, process_once, read_mongo, write_mongo

ROOT = Path(__file__).resolve().parents[1]


def test_original_json_and_xml_are_loaded_as_incident_lists():
    json_rows = load_json(ROOT / "import", "incidents_sample_50")
    xml_rows = load_xml(ROOT / "import", "incidents_sample_50")
    assert len(json_rows) == len(xml_rows) == 50
    assert json_rows[0]["incident_id"] == "INC-2026-00002"
    assert xml_rows[0]["incident_id"] == "INC-2026-00001"


def test_mongo_upsert_replaces_same_incident_without_duplicate():
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client[f"test_original_service_{uuid4().hex}"]
    try:
        write_mongo(db, "incidents_raw", {"incident_id": "INC-1", "fehlermeldung": "alt", "bekannte_loesung": "alt"})
        write_mongo(db, "incidents_raw", {"incident_id": "INC-1", "fehlermeldung": "neu"})
        assert db.incidents_raw.count_documents({}) == 1
        assert read_mongo(db, "incidents_raw", {"incident_id": "INC-1"})["fehlermeldung"] == "neu"
        assert "bekannte_loesung" not in read_mongo(db, "incidents_raw", {"incident_id": "INC-1"})
    finally:
        client.drop_database(db.name)
        client.close()


def test_worker_processes_new_files_once_and_retries_changes(tmp_path):
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client[f"test_original_service_{uuid4().hex}"]
    inbox = tmp_path / "import"
    failed = tmp_path / "failed"
    inbox.mkdir()
    calls = []

    def fake_analyze(ticket):
        calls.append(ticket)
        return {"impact_rating": 6, "impact_reason": "Test"}, {"duration_seconds": 0.01}

    json_path = inbox / "new.json"
    json_path.write_text(json.dumps({"incidents": [{
        "incident_id": "INC-1", "system_service": "A",
        "fehlermeldung": "erste Meldung", "schweregrad": "kritisch"
    }]}))
    xml_path = inbox / "new.xml"
    xml_path.write_text("<incidents><incident><incident_id>INC-2</incident_id>"
                        "<system_service>B</system_service><fehlermeldung>Fehler</fehlermeldung>"
                        "</incident></incidents>")
    try:
        first = process_once(db, inbox, failed, analyze=fake_analyze)
        assert first["incidents"] == 2
        assert db.incidents_raw.count_documents({}) == 2
        assert db.incidents_rated_ai.count_documents({}) == 2
        assert all("schweregrad" not in ticket for ticket in calls)
        process_once(db, inbox, failed, analyze=fake_analyze)
        assert len(calls) == 2

        json_path.write_text(json_path.read_text().replace("erste Meldung", "neue Meldung"))
        process_once(db, inbox, failed, analyze=fake_analyze)
        assert len(calls) == 3
        assert db.incidents_raw.count_documents({}) == 2
        assert read_mongo(db, "incidents_raw", {"incident_id": "INC-1"})["fehlermeldung"] == "neue Meldung"
    finally:
        client.drop_database(db.name)
        client.close()


def test_bad_file_is_logged_and_next_file_still_processed(tmp_path):
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client[f"test_original_service_{uuid4().hex}"]
    inbox = tmp_path / "import"
    failed = tmp_path / "failed"
    inbox.mkdir()
    (inbox / "bad.json").write_text("{broken")
    (inbox / "good.json").write_text(json.dumps({"incidents": [{
        "incident_id": "INC-3", "system_service": "C", "fehlermeldung": "Problem"
    }]}))
    try:
        result = process_once(
            db, inbox, failed,
            analyze=lambda ticket: (
                {"impact_rating": 4, "impact_reason": "Test"}, {"duration_seconds": 0.01}
            ),
        )
        assert result["incidents"] == 1
        assert (failed / "bad.json.errors.jsonl").exists()
        assert db.incidents_rated_ai.count_documents({}) == 1
    finally:
        client.drop_database(db.name)
        client.close()


def test_wrong_xml_root_is_reported_instead_of_silently_ignored(tmp_path):
    inbox = tmp_path / "import"
    inbox.mkdir()
    (inbox / "wrong.xml").write_text("<other><incident><incident_id>INC-X</incident_id></incident></other>")
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client[f"test_original_service_{uuid4().hex}"]
    try:
        result = process_once(db, inbox, tmp_path / "failed",
                              analyze=lambda ticket: ({"impact_rating": 5, "impact_reason": "Test"}, {}))
        assert result["errors"] == 1
        assert db.incidents_raw.count_documents({}) == 0
        assert "wrong.xml.errors.jsonl" in {p.name for p in (tmp_path / "failed").iterdir()}
    finally:
        client.drop_database(db.name)
        client.close()


def test_failed_model_call_is_retried_and_error_cleared(tmp_path):
    inbox = tmp_path / "import"
    inbox.mkdir()
    (inbox / "one.json").write_text(json.dumps({"incidents": [{
        "incident_id": "INC-R", "system_service": "A", "fehlermeldung": "Problem"
    }]}))
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client[f"test_original_service_{uuid4().hex}"]
    calls = []

    def flaky(ticket):
        calls.append(ticket)
        if len(calls) == 1:
            raise TimeoutError("Ollama schläft")
        return {"impact_rating": 5, "impact_reason": "Test"}, {"duration_seconds": 0.1}

    try:
        first = process_once(db, inbox, tmp_path / "failed", analyze=flaky)
        assert first["errors"] == 1
        assert db.processed_files.count_documents({}) == 0
        second = process_once(db, inbox, tmp_path / "failed", analyze=flaky)
        assert second["errors"] == 0
        assert db.processed_files.count_documents({}) == 1
        assert db.incidents_rated_ai.count_documents({"origin": "worker"}) == 1
        assert len(calls) == 2
        assert not (tmp_path / "failed" / "one.json.errors.jsonl").exists()
    finally:
        client.drop_database(db.name)
        client.close()


def test_missing_id_is_reported_and_following_incident_runs(tmp_path):
    inbox = tmp_path / "import"
    inbox.mkdir()
    (inbox / "mixed.json").write_text(json.dumps({"incidents": [
        {"system_service": "A", "fehlermeldung": "ohne ID"},
        {"incident_id": "INC-G", "system_service": "A", "fehlermeldung": "mit ID"},
    ]}))
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client[f"test_original_service_{uuid4().hex}"]
    try:
        result = process_once(
            db, inbox, tmp_path / "failed",
            analyze=lambda ticket: (
                {"impact_rating": 4, "impact_reason": "Test"}, {"duration_seconds": 0.01}
            ),
        )
        assert result["incidents"] == 1
        assert result["errors"] == 1
        assert db.incidents_rated_ai.count_documents({"incident_id": "INC-G"}) == 1
        report = (tmp_path / "failed" / "mixed.json.errors.jsonl").read_text()
        assert "incident_id fehlt" in report
    finally:
        client.drop_database(db.name)
        client.close()
