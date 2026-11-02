"""Rule-based incident severity scoring. Edit the mappings and weights below."""

WEIGHTS = {"impact": 0.50, "keywords": 0.35, "category": 0.15}
IMPACT_SCORES = {
    "very low": 2, "sehr niedrig": 2,
    "low": 3, "niedrig": 3,
    "medium": 5, "moderate": 5, "mittel": 5,
    "high": 8, "hoch": 8,
    "critical": 10, "kritisch": 10,
}
CATEGORY_SCORES = {
    "security": 8, "sicherheit": 8,
    "database": 7, "datenbank": 7,
    "network": 7, "netzwerk": 7,
    "authentication": 6, "authentifizierung": 6,
    "application": 5, "applikation": 5, "software": 5,
    "hardware": 4, "email": 4, "e-mail": 4,
    "backup": 7, "storage": 7, "zertifikat": 6, "certificate": 6,
    "endpoint": 4, "performance": 5,
    "printer": 2, "drucker": 2,
}
# The strongest keyword match determines
# the keyword score, so repeated words or long descriptions cannot inflate it.
KEYWORD_SCORES = {
    "ransomware": 10, "data loss": 10, "datenverlust": 10,
    "data breach": 10, "datenabfluss": 10,
    "production stopped": 10, "produktionsstillstand": 10,
    "outage": 9, "totalausfall": 9, "ausfall": 8,
    "unavailable": 8, "nicht erreichbar": 8,
    "no space left on device": 8, "fatal": 8,
    "packet loss": 7, "deadlock": 7,
    "mehrere personen": 6, "multiple users": 6,
    "produktivbetrieb zeitweise beeinträchtigt": 6,
    "timeout": 6, "slow": 4, "langsam": 4,
    "single user": 2, "einzelner benutzer": 2,
    "cosmetic": 1, "kosmetisch": 1,
}


def rate_incident(incident, impact="impact", category="category"):
    """Return a 1-10 rating and explanation without changing the incident.

    Pass the exact field names, e.g. impact="Schweregrad", category="Kategorie".
    Numeric impact uses 1-10 (higher is worse). Keywords are case-insensitive
    substrings searched in every value, including nested data and solutions.
    Missing/unknown components are omitted; no evidence returns a neutral 5.
    """
    scores = {}
    impact_value = str(incident.get(impact, "")).strip().casefold()
    if impact_value in IMPACT_SCORES:
        scores["impact"] = IMPACT_SCORES[impact_value]
    else:
        try:
            number = float(impact_value)
            if 1 <= number <= 10:
                scores["impact"] = number
        except ValueError:
            pass

    category_value = str(incident.get(category, "")).strip().casefold()
    if category_value in CATEGORY_SCORES:
        scores["category"] = CATEGORY_SCORES[category_value]

    matches = {
        keyword: score
        for keyword, score in KEYWORD_SCORES.items()
        if any(keyword in str(value).casefold() for value in incident.values())
    }
    if matches:
        scores["keywords"] = max(matches.values())

    total_weight = sum(WEIGHTS[key] for key in scores)
    score = (sum(value * WEIGHTS[key] for key, value in scores.items())
             / total_weight) if total_weight else 5
    reason = "; ".join(f"{key}={value:g}" for key, value in scores.items())
    if matches:
        reason += "; matched: " + ", ".join(matches)

    return {
        "impact_rating": int(score + 0.5),
        "impact_reason": reason or "No usable evidence; neutral score 5",
    }
