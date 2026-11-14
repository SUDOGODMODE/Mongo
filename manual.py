"""Rule-based incident severity scoring. Edit the mappings and weights in config.py."""

import config



def rate_incident(incident, impact="impact", category="category"):
    """Return a 1-10 rating and explanation without changing the incident.

    Pass the exact field names, e.g. impact="Schweregrad", category="Kategorie".
    Numeric impact uses 1-10 (higher is worse). Keywords are case-insensitive
    substrings searched in values except the supplied impact field, including
    nested data and solutions. This avoids counting the supplied impact twice.
    Missing/unknown components are omitted; no evidence returns a neutral 5.
    """
    scores = {}
    impact_value = str(incident.get(impact, "")).strip().casefold()
    if impact_value in config.IMPACT_SCORES:
        scores["impact"] = config.IMPACT_SCORES[impact_value]
    else:
        try:
            number = float(impact_value)
            if 1 <= number <= 10:
                scores["impact"] = number
        except ValueError:
            pass

    category_value = str(incident.get(category, "")).strip().casefold()
    if category_value in config.CATEGORY_SCORES:
        scores["category"] = config.CATEGORY_SCORES[category_value]

    matches = {
        keyword: score
        for keyword, score in config.KEYWORD_SCORES.items()
        if any(keyword in str(value).casefold()
               for key, value in incident.items() if key != impact)
    }
    if matches:
        scores["keywords"] = max(matches.values())

    total_weight = sum(config.WEIGHTS[key] for key in scores)
    score = (sum(value * config.WEIGHTS[key] for key, value in scores.items())
             / total_weight) if total_weight else 5
    reason = "; ".join(f"{key}={value:g}" for key, value in scores.items())
    if matches:
        reason += "; matched: " + ", ".join(matches)

    return {
        "impact_rating": int(score + 0.5),
        "impact_reason": reason or "No usable evidence; neutral score 5",
    }
