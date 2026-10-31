"""Deterministic severity rules using only service and error message."""
from __future__ import annotations


def assess_rule(incident: dict) -> dict:
    text = f'{incident.get("system_service", "")} {incident.get("fehlermeldung", "")}'.casefold()
    rules = (
        ("backup_speicher", "kritisch", "Backup-Repository ohne freien Speicher", ("backup", "repository", "out of space")),
        ("standortnetz_ausfall", "kritisch", "Standortnetz ausgefallen und Produktivbetrieb beeinträchtigt", ("switchport", "down", "produktivbetrieb")),
        ("datenbank_verbindungen", "hoch", "Datenbank-Verbindungslimit erreicht", ("connection slots",)),
        ("zertifikat_abgelaufen", "hoch", "TLS-Zertifikat abgelaufen", ("certificate has expired",)),
        ("dateizugriff", "hoch", "Zugriff auf Teamfreigabe verweigert", ("smb", "access_denied")),
        ("workflow", "mittel", "Genehmigungsworkflow blockiert", ("workflow", "pending")),
        ("antwortzeit", "mittel", "Erhöhte Antwortzeit", ("response time",)),
        ("empfaenger", "mittel", "Empfängeradresse unbekannt", ("recipient address rejected",)),
        ("tenant", "niedrig", "Einzelnes Benutzerkonto im falschen Tenant", ("aadsts50020",)),
        ("wlan_standby", "niedrig", "WLAN-Verlust nach Standby", ("standby", "wlan")),
    )
    for rule_id, grade, reason, terms in rules:
        if all(term in text for term in terms):
            return {"schweregrad": grade, "regel": rule_id, "begruendung": reason}
    return {"schweregrad": "unbestimmt", "regel": "keine_regel",
            "begruendung": "Keine passende Regel; manuelle Prüfung erforderlich"}
