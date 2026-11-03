import csv
from pymongo import MongoClient
import config

def export_comparison(col, path="comparison.csv"):
    incidents = col.find({
        "rated_ai": True,
        "rated_manual": True,
    })

    fields = [
        "incident_id", "manual", "ai", "difference",
        "manual_reason", "ai_reason",
    ]

    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for incident in incidents:
            manual = incident["rating_manual"]
            ai = incident["impact_rating_ai"]

            writer.writerow({
                "incident_id": incident["incident_id"],
                "manual": manual["impact_rating"],
                "ai": ai["impact_rating"],
                "difference": abs(manual["impact_rating"] - ai["impact_rating"]),
                "manual_reason": manual["impact_reason"],
                "ai_reason": ai["impact_reason"],
            })

if __name__ == "__main__":
    client = MongoClient(config.MONGO_URL)
    db = client["incident_db"]
    incident_col = db["incidents"]

    export_comparison(incident_col)
