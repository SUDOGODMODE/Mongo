"""Reproducible rule/AI comparison over the same selected incidents."""
from __future__ import annotations

import csv
import json
import statistics
import time
from collections import Counter
from pathlib import Path

from ingest import SEVERITIES
from llm import assess_ai
from rules import assess_rule


def _metrics(runs: list[dict], ids: list[str]) -> dict:
    correct = sum(row["vorhersage"] == row["erwartet"] for row in runs)
    valid = sum(row["vorhersage"] in SEVERITIES for row in runs)
    errors = sum(row["fehler"] != "" for row in runs)
    consistent = sum(
        len({row["vorhersage"] for row in runs if row["incident_id"] == iid}) == 1
        for iid in ids
    )
    durations = [row["dauer_s"] for row in runs]
    return {
        "correct": correct,
        "accuracy": round(correct / len(runs), 3),
        "valid_predictions": valid,
        "coverage": round(valid / len(runs), 3),
        "errors": errors,
        "consistent_incidents": consistent,
        "median_duration_s": round(statistics.median(durations), 6),
        "total_duration_s": round(sum(durations), 6),
    }


def compare_incidents(db, ids: list[str], output_dir: Path, *,
                      ai_assessor=assess_ai, repeats: int = 3) -> dict:
    if len(ids) < 10 or len(set(ids)) != len(ids) or repeats < 1:
        raise ValueError("Mindestens zehn eindeutige Incidents und ein Lauf erforderlich")
    output_dir = Path(output_dir)
    incidents = {row["incident_id"]: row for row in
                 db.incidents_raw.find({"incident_id": {"$in": ids}})}
    if set(incidents) != set(ids):
        raise ValueError("Evaluations-IDs fehlen in MongoDB")

    rows = []
    for incident_id in ids:
        incident = incidents[incident_id]
        for run in range(1, repeats + 1):
            for method in ("klassisch", "ki"):
                started = time.perf_counter()
                try:
                    result = assess_rule(incident) if method == "klassisch" else ai_assessor(incident)
                    prediction = result["schweregrad"]
                    reason = result["begruendung"]
                    rule_or_model = result.get("regel") or result.get("modell", "")
                    error = ""
                except Exception as exc:
                    prediction, reason, rule_or_model = "fehler", "", ""
                    error = f"{type(exc).__name__}: {exc}"
                duration = round(time.perf_counter() - started, 6)
                row = {
                    "incident_id": incident_id,
                    "quelle": incident.get("source_format", ""),
                    "erwartet": incident["schweregrad"],
                    "methode": method,
                    "lauf": run,
                    "vorhersage": prediction,
                    "korrekt": prediction == incident["schweregrad"],
                    "begruendung": reason,
                    "regel_oder_modell": rule_or_model,
                    "dauer_s": duration,
                    "fehler": error,
                }
                rows.append(row)
                collection = db.incidents_rated if method == "klassisch" else db.incidents_rated_ai
                collection.create_index([("incident_id", 1), ("lauf", 1)], unique=True)
                collection.replace_one(
                    {"incident_id": incident_id, "lauf": run}, row, upsert=True
                )

    export_dir = output_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    with (export_dir / "runs.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    comparison = []
    for incident_id in ids:
        group = [row for row in rows if row["incident_id"] == incident_id]
        classical = next(row for row in group if row["methode"] == "klassisch")
        ai = next(row for row in group if row["methode"] == "ki")
        comparison.append({
            "incident_id": incident_id, "quelle": classical["quelle"],
            "erwartet": classical["erwartet"],
            "klassisch": classical["vorhersage"], "klassisch_korrekt": classical["korrekt"],
            "klassisch_regel": classical["regel_oder_modell"],
            "klassisch_dauer_s": classical["dauer_s"],
            "klassisch_begruendung": classical["begruendung"],
            "ki": ai["vorhersage"], "ki_korrekt": ai["korrekt"],
            "ki_begruendung": ai["begruendung"],
            "ki_dauer_s": ai["dauer_s"],
            "ki_fehler": ai["fehler"],
        })
    with (export_dir / "comparison.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(comparison[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(comparison)

    summary = {
        "incidents": len(ids), "repeats": repeats, "runs_per_method": len(ids) * repeats,
        "evaluation_ids": ids,
        "classical": _metrics([row for row in rows if row["methode"] == "klassisch"], ids),
        "ai": _metrics([row for row in rows if row["methode"] == "ki"], ids),
        "prediction_counts": {
            method: dict(Counter(row["vorhersage"] for row in rows if row["methode"] == method))
            for method in ("klassisch", "ki")
        },
    }
    (export_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary
