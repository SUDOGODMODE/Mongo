import json
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4

from pymongo import MongoClient

from ingest import EVAL_IDS
from pipeline import import_dataset

ROOT = Path(__file__).resolve().parents[1]


def test_import_creates_reproducible_corpus_and_error_report(tmp_path):
    client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    db = client[f"incident_pipeline_test_{uuid4().hex}"]
    try:
        args = (
            ROOT / "import" / "incidents_sample_50.json",
            ROOT / "import" / "incidents_sample_50.xml",
            db,
            tmp_path,
        )
        summary = import_dataset(*args)
        assert summary["read"] == 100
        assert summary["selected"] == 30
        assert summary["invalid"] >= 3
        assert db.incidents_raw.count_documents({}) == 30

        ids = json.loads((tmp_path / "dataset_ids.json").read_text())
        assert len(ids["dataset_ids"]) == 30
        assert set(EVAL_IDS) == set(ids["evaluation_ids"])
        errors = (tmp_path / "failed" / "import_errors.jsonl").read_text()
        for incident_id in ("INC-2026-00004", "INC-2026-00013", "INC-2026-00025"):
            assert incident_id in errors

        json_sample = json.loads((tmp_path / "samples" / "incidents_selected.json").read_text())
        xml_sample = ET.parse(tmp_path / "samples" / "incidents_selected.xml")
        assert len(json_sample["incidents"]) + len(xml_sample.getroot().findall("incident")) == 30

        import_dataset(*args)
        assert db.incidents_raw.count_documents({}) == 30
        assert json.loads((tmp_path / "dataset_ids.json").read_text()) == ids
    finally:
        client.drop_database(db.name)
        client.close()
