import csv
import json
from pathlib import Path
from uuid import uuid4

from pymongo import MongoClient

from compare import compare_incidents


def test_comparison_uses_ten_same_incidents_and_persists_runs(tmp_path):
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client[f"test_compare_{uuid4().hex}"]
    ids = [f"INC-2026-{i:05d}" for i in range(10)]
    db.incidents_raw.insert_many({
        "incident_id": iid, "system_service": "Testservice",
        "fehlermeldung": "Unbekannte Meldung", "schweregrad": "mittel"
    } for iid in ids)

    def fake_ai(_incident):
        return {"schweregrad": "mittel", "begruendung": "Testbewertung",
                "modell": "fake", "dauer_s": 0.01}

    try:
        summary = compare_incidents(db, ids, tmp_path, ai_assessor=fake_ai, repeats=3)
        assert summary["incidents"] == 10
        assert summary["runs_per_method"] == 30
        assert summary["classical"]["correct"] == 0
        assert summary["ai"]["correct"] == 30
        assert db.incidents_rated.count_documents({}) == 30
        assert db.incidents_rated_ai.count_documents({}) == 30
        rows = list(csv.DictReader((tmp_path / "exports" / "comparison.csv").open()))
        assert len(rows) == 10
        assert {row["incident_id"] for row in rows} == set(ids)
        assert all(row["klassisch"] == "unbestimmt" and row["ki"] == "mittel" for row in rows)
        assert json.loads((tmp_path / "exports" / "summary.json").read_text())["ai"]["correct"] == 30
        compare_incidents(db, ids, tmp_path, ai_assessor=fake_ai, repeats=3)
        assert db.incidents_rated_ai.count_documents({}) == 30
    finally:
        client.drop_database(db.name)
        client.close()


def test_ai_failure_is_recorded_without_losing_comparison(tmp_path):
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client[f"test_compare_{uuid4().hex}"]
    ids = [f"INC-2026-{i:05d}" for i in range(20, 30)]
    db.incidents_raw.insert_many({
        "incident_id": iid, "system_service": "Test",
        "fehlermeldung": "Unknown", "schweregrad": "mittel"
    } for iid in ids)

    def failing_ai(_incident):
        raise TimeoutError("Ollama nicht erreichbar")

    try:
        result = compare_incidents(db, ids, tmp_path, ai_assessor=failing_ai, repeats=1)
        assert result["ai"]["errors"] == 10
        assert result["ai"]["valid_predictions"] == 0
        assert db.incidents_rated_ai.count_documents({"vorhersage": "fehler"}) == 10
        rows = list(csv.DictReader((tmp_path / "exports" / "comparison.csv").open()))
        assert all(row["ki"] == "fehler" and "TimeoutError" in row["ki_fehler"] for row in rows)
    finally:
        client.drop_database(db.name)
        client.close()
