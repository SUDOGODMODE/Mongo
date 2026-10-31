"""Read, validate, and choose a reproducible incident dataset."""
from __future__ import annotations

import json
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SEVERITIES = {"niedrig", "mittel", "hoch", "kritisch"}
STATUSES = {"neu", "in_bearbeitung", "wartend", "geloest", "geschlossen"}
REQUIRED = (
    "incident_id", "zeitpunkt", "system_service", "fehlermeldung",
    "schweregrad", "status", "kategorie",
)
EVAL_IDS = tuple(f"INC-2026-{number:05d}" for number in
                 (10, 16, 21, 31, 50, 51, 62, 76, 81, 91))


def load_json(path: Path) -> list:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload.get("incidents") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"{path}: expected an object with an incidents list")
    return rows


def load_xml(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    if root.tag != "incidents":
        raise ValueError(f"{path}: expected <incidents> root")
    return [
        {child.tag: child.text.strip() if child.text else None for child in node}
        for node in root.findall("incident")
    ]


def normalize_incident(raw: dict, source: str) -> tuple[dict | None, list[str]]:
    if not isinstance(raw, dict):
        return None, ["incident: expected an object"]
    document = {"source_format": source}
    errors = []
    for field in REQUIRED:
        value = raw.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field}: missing or empty")
        else:
            document[field] = value.strip()

    solution = raw.get("bekannte_loesung")
    if solution is None or solution == "":
        document["bekannte_loesung"] = None
    elif isinstance(solution, str):
        document["bekannte_loesung"] = solution.strip() or None
    else:
        errors.append("bekannte_loesung: expected text or null")

    incident_id = document.get("incident_id")
    if incident_id and not re.fullmatch(r"INC-\d{4}-\d{5}", incident_id):
        errors.append("incident_id: invalid format")
    if document.get("schweregrad") and document["schweregrad"] not in SEVERITIES:
        errors.append("schweregrad: unknown value")
    if document.get("status") and document["status"] not in STATUSES:
        errors.append("status: unknown value")
    if document.get("zeitpunkt"):
        try:
            moment = datetime.fromisoformat(document["zeitpunkt"])
            if moment.utcoffset() is None:
                raise ValueError("timezone missing")
            document["zeitpunkt"] = moment.astimezone(timezone.utc)
        except ValueError:
            errors.append("zeitpunkt: invalid ISO timestamp with timezone")
    return (None, errors) if errors else (document, [])


def choose_incidents(valid: list[dict], size: int = 30) -> list[dict]:
    by_id = {row["incident_id"]: row for row in valid}
    if len(by_id) != len(valid):
        raise ValueError("duplicate incident IDs in validated input")
    missing = set(EVAL_IDS) - by_id.keys()
    if missing:
        raise ValueError(f"evaluation IDs missing from valid input: {sorted(missing)}")
    if size < len(EVAL_IDS) or size > len(valid):
        raise ValueError("invalid dataset size")
    remaining = [by_id[key] for key in sorted(by_id) if key not in EVAL_IDS]
    random.Random(42).shuffle(remaining)
    return [by_id[key] for key in EVAL_IDS] + remaining[:size - len(EVAL_IDS)]
