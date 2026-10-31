from uuid import uuid4

from pymongo import MongoClient

from ingest import normalize_incident
from storage import save_incidents


def test_repeated_import_updates_instead_of_duplicating():
    client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    db = client[f"incident_pipeline_test_{uuid4().hex}"]
    raw = {
        "incident_id": "INC-2026-99999",
        "zeitpunkt": "2026-09-01T12:00:00+02:00",
        "system_service": "Test",
        "fehlermeldung": "Einzelner Testbenutzer betroffen",
        "schweregrad": "niedrig",
        "status": "neu",
        "kategorie": "Test",
        "bekannte_loesung": None,
    }
    document, errors = normalize_incident(raw, "json")
    assert errors == []
    try:
        save_incidents(db, [document])
        document["status"] = "geloest"
        save_incidents(db, [document])
        assert db.incidents_raw.count_documents({}) == 1
        assert db.incidents_raw.find_one({"incident_id": raw["incident_id"]})["status"] == "geloest"
    finally:
        client.drop_database(db.name)
        client.close()
