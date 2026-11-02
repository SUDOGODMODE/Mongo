from loaders import load_json, load_xml
import llm as llm
import config as config
import manual as rater
import compare as compare
from pymongo.collection import Collection
from pymongo import MongoClient
from pathlib import Path
from requests.exceptions import RequestException
from pymongo.errors import PyMongoError



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
    rate_manual(incident_col)
    compare.export_comparison(incident_col)
