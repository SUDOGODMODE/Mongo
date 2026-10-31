---
marp: true
theme: default
paginate: true
---

# Incident-Schweregrad: Regeln oder lokale KI?

**IN258 – MongoDB-Projekt**
JSON + XML → MongoDB → Regeln / Ollama → Vergleich

**Leitfrage:** Welche Methode liefert auf unserem Datensatz die verlässlichere Einstufung?

<!-- Sprechtext: Ziel, gewählte Analyseaufgabe B und den Vergleich in einem Satz nennen. Dauer 1 Min. -->

---

# Datensatz und Qualitätsprüfung

- 50 JSON- und 50 XML-Incidents
- Gemeinsame Felder: ID, Zeitpunkt, Service, Meldung, Schweregrad, Status, Kategorie, optionale Lösung
- 90 gültig; 10 fehlerhaft und einzeln protokolliert
- 30 gültige Fälle reproduzierbar ausgewählt; 10 davon im Vergleich

**Beispiele für Fehler:** ungültiges Datum, leere ID, fehlender Service, unbekannter Status.

<!-- Sprechtext: Die 100 Eingaben sind Quelle, die Datenbank enthält bewusst 30 ausgewählte gültige Dokumente. Fehlerdatei zeigen. Dauer 1,5 Min. -->

---

# Datenfluss

```text
JSON (50) ─┐
           ├─> Einlesen → Validieren → Normalisieren → MongoDB: incidents_raw
XML (50) ──┘                    │                         │
                               └→ failed/import_errors   ├→ Regeln → incidents_rated
                                                          └→ Ollama → incidents_rated_ai
                                                                    │
                                                 Vergleichstabelle und Kennzahlen
```

**Keine Referenzlabel im Bewertungseingang:** Regeln und KI erhalten nur Service + Fehlermeldung.

<!-- Sprechtext: Zeitstempel werden als UTC-Datum gespeichert. Die KI erzeugt nur eine Empfehlung und führt keine Befehle aus. Dauer 1,5 Min. -->

---

# Live-Demo: Import und MongoDB

```bash
cd ~/Mongo
podman-compose -f compose.yaml ps
.venv/bin/python main.py import
podman-compose -f compose.yaml exec mongodb mongosh incident_db \
  --eval 'db.incidents_raw.countDocuments({})'
podman-compose -f compose.yaml exec mongodb mongosh incident_db \
  --eval 'db.incidents_raw.findOne({incident_id:"INC-2026-00021"},{_id:0})'
```

**Erwartete Ausgabe:** 100 gelesen, 90 gültig, 10 ungültig, 30 ausgewählt; 30 Dokumente.

<!-- Sprechtext: Ein gespeichertes Dokument mit Quelle, UTC-Zeit und optionaler Lösung zeigen. Wiederholter Import erzeugt keine Duplikate. Dauer 2 Min. -->

---

# Klassische Bewertung

**Beispiel INC-2026-00021:** PostgreSQL meldet „remaining connection slots are reserved“.

- Regel `datenbank_verbindungen` trifft auf die Fehlermeldung zu.
- Ausgabe: `hoch`, mit Regelkennung und kurzer Begründung.
- Keine Regel? Ausgabe `unbestimmt` und manuelle Prüfung.

**Eigenschaften:** deterministisch, sehr schnell, klar zu prüfen; Wortlautänderungen können Regeln verfehlen.

<!-- Sprechtext: In exports/comparison.csv die Zeile zeigen. Die Regeln sind am vorhandenen Datensatz entwickelt worden. Dauer 1,5 Min. -->

---

# KI-Bewertung mit Ollama

**Dasselbe Beispiel:** `gemma3:4b` antwortet `hoch` mit einer Begründung.

- Lokaler Aufruf an `/api/chat`, JSON-Schema mit vier erlaubten Stufen
- Temperatur 0, Seed 42, HTTP-Timeout
- Referenzschweregrad und bekannte Lösung werden nicht übergeben
- Nur Empfehlung; kein Systembefehl

**Achtung:** Eine plausible Begründung kann unbelegte Details enthalten.

<!-- Sprechtext: exports/comparison.csv oder incidents_rated_ai für INC-2026-00021 zeigen. Eine KI-Antwort dauert hier mehrere Sekunden. Dauer 1,5 Min. -->

---

# Ergebnis: zehn Incidents, je drei Wiederholungen

| Kriterium | Regeln | Ollama |
| --- | ---: | ---: |
| Korrekt zum Referenzlabel | 30/30 | 6/30 |
| Gültige Einstufung | 30/30 | 30/30 |
| Technische Fehler | 0 | 0 |
| Konsistent über 3 Läufe | 10/10 | 10/10 |
| Median pro Lauf | 0,000012 s | 5,613542 s |

**Auffällig:** Ollama gab 27-mal `hoch`, dreimal `mittel` aus.

<!-- Sprechtext: Qualitätsmaß ist Label-Übereinstimmung, nicht unabhängig bewiesene fachliche Richtigkeit. Dauer 2 Min. -->

---

# Beispiele für Abweichungen

| Incident | Referenz | Regeln | KI |
| --- | --- | --- | --- |
| Falscher Tenant 00010 | niedrig | niedrig | hoch |
| Switchport down 00016 | kritisch | kritisch | hoch |
| Backup-Speicher voll 00076 | kritisch | kritisch | hoch |
| Zertifikat abgelaufen 00091 | hoch | hoch | hoch |

**Beobachtetes Risiko:** KI fügte in Begründungen teils nicht belegte Annahmen hinzu.

<!-- Sprechtext: Warum Über- und Unterbewertung bei Incident-Triage problematisch sind erklären. Die Labels können selbst fragwürdig sein. Dauer 1,5 Min. -->

---

# Antwort auf die Leitfrage und nächster Schritt

- Auf diesen zehn Beispielen passten die Regeln deutlich besser zu den vorhandenen Labels.
- Die KI war in keinem Fall allein besser; sie war deutlich langsamer.
- Die Regeln wurden mit Kenntnis des Datensatzes erstellt: 100 % sind **keine** Prognose für neue Fälle.
- Für einen fairen Produktivvergleich: neue, unabhängige Incidents und fachlich geprüfte Labels.
- KI nur mit menschlicher Freigabe, Protokollierung, Ausgabevalidierung, Datenschutz und Fallback.

**Antwort:** Für diese Daten Regeln als Baseline; KI vorerst nur als überprüfbare Zusatzempfehlung.

<!-- Sprechtext: Schlussfolgerung zusammenfassen und Fragen aufnehmen. Dauer 1,5 Min. Gesamt ca. 12–13 Min. -->
