"""Command line entry point for importing and comparing incident severity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pymongo import MongoClient

import config
from compare import compare_incidents
from pipeline import import_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Incident-Import und Schweregradvergleich")
    parser.add_argument("command", choices=("import", "compare", "all"))
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    with MongoClient(config.MONGO_URL, serverSelectionTimeoutMS=5000) as client:
        client.admin.command("ping")
        db = client["incident_db"]
        if args.command in ("import", "all"):
            result = import_dataset(
                base / "import" / "incidents_sample_50.json",
                base / "import" / "incidents_sample_50.xml",
                db, args.output,
            )
            print(json.dumps({"import": result}, ensure_ascii=False))
        if args.command in ("compare", "all"):
            selection_path = args.output / "dataset_ids.json"
            if not selection_path.exists():
                raise SystemExit("dataset_ids.json fehlt; zuerst 'import' ausführen")
            selection = json.loads(selection_path.read_text(encoding="utf-8"))
            result = compare_incidents(db, selection["evaluation_ids"], args.output)
            print(json.dumps({"vergleich": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
