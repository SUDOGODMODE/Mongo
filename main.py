"""Einfacher Incident-Worker auf Basis des ursprünglichen Projektcodes."""
import argparse
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from pymongo import MongoClient

import config
import llm


def load_json(folder, name):
    with open(Path(folder) / f"{name}.json", encoding="utf-8") as datei:
        data = json.load(datei)
    incidents = data.get("incidents") if isinstance(data, dict) else data
    if not isinstance(incidents, list):
        raise ValueError("JSON muss eine Liste unter 'incidents' enthalten")
    return incidents


def load_xml(folder, name):
    tree = ET.parse(Path(folder) / f"{name}.xml")
    root = tree.getroot()
    if root.tag != "incidents":
        raise ValueError("XML muss ein <incidents>-Wurzelelement haben")
    incidents = []
    for incident in root.findall("incident"):
        incidents.append({
            child.tag: child.text.strip() if child.text else None
            for child in incident
        })
    return incidents


def write_mongo(db, collection, data):
    incident_id = data.get("incident_id")
    if not isinstance(incident_id, str) or not incident_id.strip():
        raise ValueError("incident_id fehlt")
    db[collection].replace_one(
        {"incident_id": incident_id},
        data,
        upsert=True,
    )


def read_mongo(db, collection, data):
    return db[collection].find_one({"incident_id": data["incident_id"]})


def update_mongo(db, collection, data):
    query = {"incident_id": data["incident_id"]}
    if "origin" in data:
        query["origin"] = data["origin"]
    db[collection].update_one(query, {"$set": data}, upsert=True)


def analyze_ticket(ticket):
    # Das ursprüngliche flexible 1-bis-10-Schema aus llm.py bleibt erhalten.
    messages, schema = llm.build_request(ticket, ["impact"])
    return llm.send_request(config.LLM_URL, config.LLM_MODEL, messages, schema=schema)


def _hash_record(record):
    data = json.dumps(record, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _write_errors(path, error_folder, errors):
    error_folder.mkdir(parents=True, exist_ok=True)
    report = error_folder / f"{path.name}.errors.jsonl"
    if errors:
        report.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in errors),
            encoding="utf-8",
        )
    elif report.exists():
        report.unlink()


def process_once(db, import_folder, error_folder, analyze=analyze_ticket):
    import_folder = Path(import_folder)
    error_folder = Path(error_folder)
    import_folder.mkdir(parents=True, exist_ok=True)
    db["incidents_raw"].create_index("incident_id", unique=True)
    summary = {"files": 0, "incidents": 0, "errors": 0}

    for path in sorted(import_folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in (".json", ".xml"):
            continue
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        state = db["processed_files"].find_one({"file_name": path.name})
        if state and state.get("file_hash") == file_hash:
            continue

        summary["files"] += 1
        errors = []
        retry_needed = False
        try:
            rows = (load_json(path.parent, path.stem) if path.suffix.lower() == ".json"
                    else load_xml(path.parent, path.stem))
        except (ValueError, OSError, ET.ParseError) as exc:
            rows = []
            errors.append({"file": path.name, "position": None,
                           "error": f"{type(exc).__name__}: {exc}"})

        for position, incident in enumerate(rows, start=1):
            if not isinstance(incident, dict):
                errors.append({"file": path.name, "position": position,
                               "error": "Incident ist kein Objekt"})
                continue
            incident_id = incident.get("incident_id")
            if not isinstance(incident_id, str) or not incident_id.strip():
                errors.append({"file": path.name, "position": position,
                               "error": "incident_id fehlt"})
                continue

            record_hash = _hash_record(incident)
            raw = {**incident, "source_file": path.name, "source_hash": record_hash}
            try:
                write_mongo(db, "incidents_raw", raw)
                summary["incidents"] += 1
                old = db["incidents_rated_ai"].find_one({
                    "incident_id": incident_id, "origin": "worker",
                    "source_hash": record_hash,
                })
                if old:
                    continue
                service = incident.get("system_service")
                message = incident.get("fehlermeldung")
                if not service or not message:
                    errors.append({"file": path.name, "position": position,
                                   "incident_id": incident_id,
                                   "error": "system_service oder fehlermeldung fehlt"})
                    continue

                # Referenz-Schweregrad wird nicht an Ollama gesendet.
                answer, metrics = analyze({
                    "system_service": service,
                    "fehlermeldung": message,
                })
                update_mongo(db, "incidents_rated_ai", {
                    "incident_id": incident_id,
                    "origin": "worker",
                    "source_file": path.name,
                    "source_hash": record_hash,
                    **answer,
                    "metrics": metrics,
                })
                print(f"{incident_id}: KI-Bewertung {answer.get('impact_rating')}/10", flush=True)
            except Exception as exc:
                retry_needed = True
                errors.append({"file": path.name, "position": position,
                               "incident_id": incident_id,
                               "error": f"{type(exc).__name__}: {exc}"})

        _write_errors(path, error_folder, errors)
        summary["errors"] += len(errors)
        if not retry_needed and hashlib.sha256(path.read_bytes()).hexdigest() == file_hash:
            db["processed_files"].update_one(
                {"file_name": path.name},
                {"$set": {"file_hash": file_hash}},
                upsert=True,
            )
    return summary


def watch(db, import_folder, error_folder, interval=5):
    while True:
        try:
            result = process_once(db, import_folder, error_folder)
            if result["files"]:
                print(f"Verarbeitet: {result}", flush=True)
        except Exception as exc:
            print(f"Worker wartet nach Fehler: {type(exc).__name__}: {exc}", flush=True)
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Incidents importieren und bewerten")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Einmal verarbeiten")
    mode.add_argument("--watch", action="store_true", help="Importordner dauerhaft überwachen")
    args = parser.parse_args()
    client = MongoClient(config.MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client["incident_db"]
    try:
        if args.watch:
            watch(db, config.PATH_IMPORT, config.PATH_ERROR)
        else:
            print(process_once(db, config.PATH_IMPORT, config.PATH_ERROR))
    finally:
        client.close()


if __name__ == "__main__":
    main()
