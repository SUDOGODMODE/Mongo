# NoSQL-Datenmodell

Datenbank: `incident_db`. MongoDB speichert Dokumente mit dem normalen technischen Feld `_id`. Fachlich eindeutige ID ist `incident_id`.

| Collection | Inhalt | Eindeutiger Schlüssel |
| --- | --- | --- |
| `incidents_raw` | 30 validierte und normalisierte Incidents | `incident_id` |
| `incidents_rated` | Einzelergebnisse der klassischen Regeln | `incident_id`, `lauf` |
| `incidents_rated_ai` | Einzelergebnisse des lokalen Ollama-Modells | `incident_id`, `lauf` |

Ein Rohdokument enthält `incident_id` (Text), `zeitpunkt` (MongoDB-Datum in UTC), `system_service`, `fehlermeldung`, `schweregrad` (Referenzlabel), `status`, `kategorie`, `bekannte_loesung` (Text oder `null`), `source_format` (`json`/`xml`) und `source_file`. Die Normalisierung entfernt umgebende Leerzeichen. Ungültige Incidents werden mit Quelldatei, Position, Rohwert und Gründen separat in `failed/import_errors.jsonl` protokolliert.

Ergebnisdokumente enthalten `incident_id`, `quelle`, `erwartet`, `methode`, `lauf`, `vorhersage`, `korrekt`, `begruendung`, `regel_oder_modell`, `dauer_s` und `fehler`. Upserts und eindeutige Indizes verhindern Duplikate bei einem erneuten Lauf.

Beispielabfragen auf Fedora:

```bash
podman-compose -f compose.yaml exec mongodb mongosh incident_db --eval 'db.incidents_raw.countDocuments({})'
podman-compose -f compose.yaml exec mongodb mongosh incident_db --eval 'db.incidents_raw.find({schweregrad:"kritisch"},{_id:0,incident_id:1,system_service:1}).toArray()'
podman-compose -f compose.yaml exec mongodb mongosh incident_db --eval 'db.incidents_rated_ai.find({incident_id:"INC-2026-00010"},{_id:0}).toArray()'
```

Die Rohdaten und die Bewertungsergebnisse sind getrennt: Ein Import überschreibt keine Analyse und die Referenzbewertung kann ohne Modellantwort abgefragt werden. `dataset_ids.json` und die CSV/JSON-Exporte liegen zusätzlich als prüfbare Dateien im Repository.
