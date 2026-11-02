from os import write

import llm as llm
import config as config
import json
import xml.etree.ElementTree as ET
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo import MongoClient
from pathlib import Path


def load_json(folder, name):
    with open(f"{folder}/{name}.json", "r", encoding="utf-8") as datei:
        data = json.load(datei)

    return data["incidents"]


def load_xml(folder, name):
    tree = ET.parse(f"{folder}/{name}.xml")
    root = tree.getroot()

    incidents = []
    for incident in root.findall("incident"):
        incident_dict = {
            child.tag: child.text.strip() if child.text else None
            for child in incident
        }
        incidents.append(incident_dict)

    return incidents


def db_write_incidents(col: Collection, data: list[dict]) -> None:
    inserted = 0
    updated = 0

    for incident in data:
        if not incident.get("incident_id"):
            print("Skipping incident without ID.")
            continue

        result = col.update_one(
            {"incident_id": incident["incident_id"]},
            {
                "$set": incident,
                "$setOnInsert": {
                    "rated_ai": False,
                    "rated_manual": False 
                }
            },
            upsert=True
        )

        if result.upserted_id is not None:
            inserted += 1
        else:
            updated += result.modified_count

    print(f"Inserted: {inserted}, Updated: {updated}")

    return 


def rate_ai(col: Collection) -> None:
    unrated_ai = col.find({"rated_ai": False})

    for incident in unrated_ai:

        llm_incident = incident.copy()
        llm_incident.pop("_id", None)

        request, schema = llm.build_request(llm_incident, "impact")

        impact_rating_ai = llm.send_request(
            config.LLM_URL,
            config.LLM_MODEL,
            request,
            schema=schema
        )

        incident["impact_rating_ai"] = impact_rating_ai
        incident["rated_ai"] = True

        col.replace_one(
            {"_id": incident["_id"]},
            incident
        )

        print(f"Incident: {incident["incident_id"]} / {incident["_id"]} Rated with {config.LLM_MODEL}")




client = MongoClient(config.MONGO_URL)
db = client["incident_db"]
incident_col = db["incidents"]
logs = db["logs"]
errors = db["errors"]


incidents = []
import_path = Path(config.PATH_IMPORT)

for file in import_path.iterdir():
    if file.is_file():
        match file.suffix.lower():
            case ".xml":
                incidents.extend(load_xml(file.parent, file.stem))
            case ".json":
                incidents.extend(load_json(file.parent, file.stem))

if not "incidents" in db.list_collection_names():
    db.create_collection("incidents")
    incident_col.create_index("incident_id", unique=True)


db_write_incidents(incident_col, incidents)
rate_ai(incident_col)
