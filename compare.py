import csv
from pymongo import MongoClient
import config

def export_comparison(col, path=None):
    if path is None:
        path = config.PATH_COMPARISON
    incidents = col.find({
        "rated_ai": True,
        "rated_classic_rule": True,
    })

    fields = [
        "incident_id", "classic_rule", "ai", "difference",
        "classic_rule_reason", "ai_reason",
    ]

    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for incident in incidents:
            classic_rule = incident["rating_classic_rule"]
            ai = incident["impact_rating_ai"]

            writer.writerow({
                "incident_id": incident["incident_id"],
                "classic_rule": classic_rule["impact_rating"],
                "ai": ai["impact_rating"],
                "difference": abs(classic_rule["impact_rating"] - ai["impact_rating"]),
                "classic_rule_reason": classic_rule["impact_reason"],
                "ai_reason": ai["impact_reason"],
            })

if __name__ == "__main__":
    client = MongoClient(config.MONGO_URL)
    db = client[config.MONGO_DATABASE]
    incident_col = db[config.MONGO_INCIDENTS_COLLECTION]

    export_comparison(incident_col)
