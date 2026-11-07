from loaders import load_json, load_xml
import llm as llm
from loaders import move_to_done, move_to_failed
from jsonschema.exceptions import ValidationError
from lxml.etree import LxmlError
import config as config
import manual as rater
import compare as compare
from pymongo.collection import Collection
from pymongo import MongoClient
from pathlib import Path
from requests.exceptions import RequestException
from pymongo.errors import PyMongoError
import time


def db_write_incidents(col: Collection, data: list[dict]) -> bool:
    inserted = 0
    updated = 0

    for incident in data:
        if not incident.get("incident_id"):
            print("Database write failed: incident without ID.")
            return False

        try:
            result = col.update_one(
                {"incident_id": incident["incident_id"]},
                {
                    "$set": incident,
                    "$setOnInsert": {
                        "rated_ai": False,
                        "rated_manual": False,
                    },
                },
                upsert=True
            )
        except PyMongoError as error:
            print(f"Database write failed: {error}")
            return False

        if not result.acknowledged:
            print("Database write was not acknowledged.")
            return False

        if result.upserted_id is not None:
            inserted += 1
        else:
            updated += result.modified_count

    print(f"Inserted: {inserted}, Updated: {updated}")
    return True

def rate_ai(col: Collection) -> None:
    unrated_ai = col.find({"rated_ai": False})

    for incident in unrated_ai:
        try:
            llm_incident = {
                key: value
                for key, value in incident.items()
                if key not in {
                    "_id",
                    "rating_manual",
                    "impact_rating_ai",
                    "metrics_ai",
                    "rated_manual",
                    "rated_ai",
                }
            }

            request, schema = llm.build_request(llm_incident, "impact")

            impact_rating_ai, metrics = llm.send_request(
                config.LLM_URL,
                config.LLM_MODEL,
                request,
                schema=schema
            )

            incident["impact_rating_ai"] = impact_rating_ai
            incident["metrics_ai"] = metrics
            incident["rated_ai"] = True

            col.replace_one(
                {"_id": incident["_id"]},
                incident
            )
        except (RequestException, ValueError, KeyError, IndexError, PyMongoError) as error:
            print(f"Rating failed for {incident['incident_id']}: {error}")
            continue

        print(f"Incident: {incident["incident_id"]} / {incident["_id"]} Rated with {config.LLM_MODEL}")

def rate_manual(col: Collection) -> None:
    unrated = col.find({"rated_manual": False})

    for incident in unrated:
        try:
            man_incident = {
                key: value
                for key, value in incident.items()
                if key not in {
                    "_id",
                    "rating_manual",
                    "impact_rating_ai",
                    "metrics_ai",
                    "rated_manual",
                    "rated_ai",
                }
            }

            impact_rating = rater.rate_incident(man_incident, "schweregrad", "kategorie")

            incident["rating_manual"] = impact_rating
            incident["rated_manual"] = True

            col.replace_one(
                {"_id": incident["_id"]},
                incident
            )
        except (RequestException, ValueError, KeyError, IndexError, PyMongoError) as error:
            print(f"Rating failed for {incident['incident_id']}: {error}")
            continue

        print(f"Incident: {incident["incident_id"]} / {incident["_id"]} Rated manually")


if __name__ == "__main__":

    client = MongoClient(config.MONGO_URL)
    db = client["incident_db"]
    incident_col = db["incidents"]
    logs = db["logs"]
    errors = db["errors"]
    import_path = Path(config.PATH_IMPORT)

    # Check if collection already exists
    if not "incidents" in db.list_collection_names():
        db.create_collection("incidents")
    incident_col.create_index("incident_id", unique=True)
    import_path.mkdir(parents=True, exist_ok=True)

    # Start process loop
    print("Begin process-loop, wait for incoming files.")
    while True:

        time.sleep(2)

        for file in import_path.iterdir():
            if not file.is_file():
                continue
            try:
                match file.suffix.lower():
                    case ".json":
                        print(f"{file.name} found, load")
                        incidents = load_json(file.parent, file.stem)
                    case ".xml":
                        print(f"{file.name} found, load")
                        incidents = load_xml(file.parent, file.stem)
                    case _:
                        continue
                if incidents and db_write_incidents(incident_col, incidents):
                    print(f"{file.name} done, move do done")
                    move_to_done(file)
            except (ValueError, ValidationError, LxmlError) as error:
                try:
                    destination = move_to_failed(file)
                    print(f"Invalid import {file.name} moved to {destination}: {error}")
                except OSError as move_error:
                    print(f"Could not quarantine {file.name}; file retained: {move_error}")
            except OSError as error:
                print(f"Import failed for {file.name}; file retained for retry: {error}")

        rate_ai(incident_col)
        rate_manual(incident_col)
