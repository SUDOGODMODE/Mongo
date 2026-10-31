import json
from unittest.mock import Mock

import pytest

from rules import assess_rule
from llm import assess_ai, build_payload


@pytest.mark.parametrize(("service", "message", "expected"), [
    ("Veeam Backup", "Backup job failed: Repository out of space.", "kritisch"),
    ("PostgreSQL", "FATAL: remaining connection slots are reserved", "hoch"),
    ("Exchange Online", "550 5.1.1 Recipient address rejected: User unknown.", "mittel"),
    ("Microsoft Entra ID", "AADSTS50020: Benutzerkonto im falschen Tenant", "niedrig"),
    ("Unknown", "Unbekannter Fehler ohne Auswirkung", "unbestimmt"),
])
def test_rules_use_incident_evidence(service, message, expected):
    result = assess_rule({"system_service": service, "fehlermeldung": message})
    assert result["schweregrad"] == expected
    assert result["regel"] and result["begruendung"]


def test_ai_payload_excludes_reference_label_and_solution():
    incident = {"system_service": "PostgreSQL", "fehlermeldung": "connection slots exhausted",
                "schweregrad": "kritisch", "bekannte_loesung": "restart", "incident_id": "INC-1"}
    payload = build_payload(incident, "gemma3:4b")
    serialized = payload["messages"][1]["content"]
    assert "connection slots exhausted" in serialized
    assert "kritisch" not in serialized
    assert "restart" not in serialized
    assert "INC-1" not in serialized
    assert payload["options"]["temperature"] == 0


def test_ai_rejects_unexpected_grade():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"message": {"content": '{"schweregrad":"dringend","begruendung":"x"}'}}
    session = Mock()
    session.post.return_value = response
    with pytest.raises(ValueError, match="schweregrad"):
        assess_ai({"system_service": "A", "fehlermeldung": "B"}, session=session)
