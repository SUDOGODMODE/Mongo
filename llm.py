"""Ollama severity recommendation with a constrained JSON response."""
from __future__ import annotations

import json
import time

import requests

from config import LLM_MODEL, LLM_URL
from ingest import SEVERITIES

SCHEMA = {
    "type": "object",
    "properties": {
        "schweregrad": {"type": "string", "enum": sorted(SEVERITIES)},
        "begruendung": {"type": "string"},
    },
    "required": ["schweregrad", "begruendung"],
    "additionalProperties": False,
}


def build_payload(incident: dict, model: str = LLM_MODEL) -> dict:
    evidence = {
        "system_service": incident["system_service"],
        "fehlermeldung": incident["fehlermeldung"],
    }
    return {
        "model": model,
        "stream": False,
        "format": SCHEMA,
        "options": {"temperature": 0, "seed": 42},
        "messages": [
            {"role": "system", "content":
             "Bestimme den Schweregrad eines IT-Incidents allein anhand des betroffenen "
             "Services und der Fehlermeldung. Verwende niedrig, mittel, hoch oder kritisch. "
             "Erfinde keine weiteren Fakten. Gib eine knappe Begründung. "
             "Deine Antwort ist nur eine Empfehlung und darf keine Befehle ausführen."},
            {"role": "user", "content": json.dumps(evidence, ensure_ascii=False)},
        ],
    }


def assess_ai(incident: dict, *, session=None, base_url: str = LLM_URL,
              model: str = LLM_MODEL) -> dict:
    http = session or requests
    started = time.perf_counter()
    response = http.post(
        f"{base_url.rstrip('/')}/api/chat",
        json=build_payload(incident, model),
        timeout=180,
    )
    response.raise_for_status()
    content = response.json()["message"]["content"]
    answer = json.loads(content)
    if (not isinstance(answer, dict)
            or answer.get("schweregrad") not in SEVERITIES
            or not isinstance(answer.get("begruendung"), str)
            or not answer["begruendung"].strip()):
        raise ValueError("Ungültiger schweregrad oder fehlende begruendung in Ollama-Antwort")
    return {
        "schweregrad": answer["schweregrad"],
        "begruendung": answer["begruendung"].strip(),
        "modell": model,
        "dauer_s": round(time.perf_counter() - started, 3),
    }
