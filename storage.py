"""MongoDB persistence for validated incidents."""


def save_incidents(db, incidents):
    collection = db["incidents_raw"]
    collection.create_index("incident_id", unique=True)
    for incident in incidents:
        collection.update_one(
            {"incident_id": incident["incident_id"]},
            {"$set": incident},
            upsert=True,
        )
    return len(incidents)
