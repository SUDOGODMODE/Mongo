# Incident-Analyse mit MongoDB und Ollama

Ein reproduzierbares Studienprojekt zur [IN258-Aufgabenstellung](Aufgabe.md): Incidents aus JSON und XML einlesen, validieren, in MongoDB speichern und ihren Schweregrad mit Regeln und einem lokalen Sprachmodell bewerten. Die KI liefert ausschließlich Empfehlungen; sie führt keine Systembefehle aus.

## Überblick

| Schritt | Umsetzung | Ergebnis |
| --- | --- | --- |
| Einlesen | 50 JSON- und 50 XML-Einträge | 100 geprüfte Eingaben |
| Validieren | Pflichtfelder, ID, Zeitpunkt, Status, Schweregrad | 90 gültig, 10 mit Fehlerprotokoll |
| Auswählen | Fester Seed und gespeicherte ID-Liste | 30 Incidents, davon 10 Vergleichsfälle |
| Speichern | MongoDB mit eindeutigen Indizes und Upserts | Wiederholbarer Import |
| Bewerten | Schlüsselwortregeln und Ollama `gemma3:4b` | Zwei getrennte Ergebnissammlungen |
| Vergleichen | Drei Läufe je Methode und Incident | CSV-Tabelle und JSON-Kennzahlen |

Der Datenfluss ist:

```text
JSON + XML → Validierung → 30 normalisierte Dokumente → MongoDB
                    │                                    ├→ Regeln ─┐
                    └→ Fehlerprotokoll                   └→ Ollama ─┴→ Vergleich
```

## Voraussetzungen

- Fedora mit `podman` und `podman-compose`
- Python 3 mit `venv` und `pip`
- Speicherplatz für MongoDB und das Modell `gemma3:4b` (Modell-Datei ungefähr 3,4 GB)

MongoDB und Ollama laufen als Podman-Container. Python läuft auf dem Fedora-Host. Die Containerports sind in `compose.yaml` an `127.0.0.1` gebunden. Für diese Anwendung ist weder ein MongoDB-RPM noch EPEL erforderlich. Ein externer KI-Dienst oder API-Schlüssel wird nicht verwendet.

## Schnellstart auf Fedora

Nach dem Klonen des Repositories im Projektverzeichnis:

```bash
cd ~/Mongo
podman-compose -f compose.yaml up -d
podman-compose -f compose.yaml exec ollama ollama pull gemma3:4b
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python main.py all
```

Der Modell-Download ist nur beim ersten Start nötig. `all` führt Import und Vergleich nacheinander aus. Der Vergleich macht 30 lokale Modellaufrufe und kann mehrere Minuten dauern. Die Laufzeit hängt von der Hardware ab.

Dienste prüfen oder stoppen:

```bash
podman-compose -f compose.yaml ps
podman-compose -f compose.yaml down
```

`down` entfernt keine Daten aus den benannten MongoDB- und Ollama-Volumes.

## Befehle

| Befehl | Wirkung |
| --- | --- |
| `.venv/bin/python main.py import` | JSON/XML prüfen, 30 Incidents auswählen, nach MongoDB schreiben und Beispieldaten exportieren |
| `.venv/bin/python main.py compare` | Zehn festgelegte Incidents mit Regeln und Ollama je dreimal bewerten |
| `.venv/bin/python main.py all` | Import und Vergleich zusammen ausführen |
| `PYTHONPATH=. .venv/bin/python -m pytest -q` | Tests ausführen; MongoDB muss laufen |

`compare` benötigt einen vorherigen Import und `dataset_ids.json`. Erneute Läufe aktualisieren vorhandene Datensätze über eindeutige Schlüssel. Mit `--output PFAD` können die erzeugten Dateien in ein anderes Verzeichnis geschrieben werden; Import und Vergleich müssen dann denselben Pfad verwenden. Quellpfade und Dienstadressen stehen in `main.py` beziehungsweise `config.py`.

## Daten und Ergebnisse

| Pfad | Inhalt |
| --- | --- |
| `import/incidents_sample_50.json`, `.xml` | Ursprüngliche Beispieldaten |
| `failed/import_errors.jsonl` | Abgewiesene Einträge mit Quelle, Position und Fehlergrund |
| `dataset_ids.json` | Reproduzierbare Auswahl und Vergleichs-IDs |
| `samples/incidents_selected.json`, `.xml` | Die 30 ausgewählten Incidents in beiden Quellformaten |
| `exports/comparison.csv` | Zehn Fälle mit Referenzlabel und beiden Methoden |
| `exports/runs.csv` | Alle 60 Einzelläufe mit Laufzeit, Begründung und Fehlerfeld |
| `exports/summary.json` | Aggregierte Qualität, Abdeckung, Laufzeit und Konsistenz |

Die Datenbank `incident_db` enthält `incidents_raw`, `incidents_rated` und `incidents_rated_ai`. Ein Blick auf die gespeicherten Dokumente:

```bash
podman-compose -f compose.yaml exec mongodb mongosh incident_db --quiet \
  --eval 'db.incidents_raw.countDocuments({})'
podman-compose -f compose.yaml exec mongodb mongosh incident_db --quiet \
  --eval 'db.incidents_raw.findOne({incident_id:"INC-2026-00021"},{_id:0})'
```

Die ausführliche Feldbeschreibung und weitere Abfragen stehen in [docs/datenmodell.md](docs/datenmodell.md).

## Wie die Bewertung funktioniert

Die Regeln und das Modell erhalten ausschließlich `system_service` und `fehlermeldung`. Das vorhandene Schweregradlabel, Kategorie, Status und bekannte Lösungen werden nicht als Hinweis an die Bewertungsverfahren gegeben. Die Regeln liefern bei fehlender Übereinstimmung `unbestimmt`; das Modell muss eine der vier Stufen `niedrig`, `mittel`, `hoch` oder `kritisch` als JSON zurückgeben. Ungültige Antworten und Verbindungsfehler werden als Fehler protokolliert.

Im durchgeführten Vergleich trafen die Regeln 30/30 vorhandene Labels, Ollama 6/30. Beide Methoden waren über drei Läufe je Incident konsistent und hatten keine technischen Fehler. **Diese Zahlen gelten nur für die zehn betrachteten Fälle.** Die Regeln wurden mit Kenntnis dieses Datensatzes entwickelt; die Labels wurden nicht unabhängig fachlich geprüft. Methodik, Einzelergebnisse und Risiken stehen in [docs/ergebnisse.md](docs/ergebnisse.md).

## Entwicklung und Tests

Die Tests prüfen Parsing und Validierung, die feste Auswahl, MongoDB-Upserts, Importartefakte, den Ausschluss des Referenzlabels aus der KI-Anfrage, Exportdaten und den Umgang mit einem ausgefallenen KI-Dienst. Die Integrationstests erstellen eigene temporäre Datenbanken und löschen diese danach.

```bash
cd ~/Mongo
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Lokale Umgebungsdateien, virtuelle Umgebungen und Test-Caches sind in `.gitignore` ausgeschlossen. Die Beispiel- und Ergebnisdateien sind bewusst versioniert, damit der Vergleich nachvollziehbar bleibt.

## Dokumentation und Präsentation

- [Aufgabenstellung](Aufgabe.md)
- [Datenmodell und MongoDB-Abfragen](docs/datenmodell.md)
- [Vergleich, Messwerte und Schlussfolgerung](docs/ergebnisse.md)
- [Präsentationsfolien mit Demo-Befehlen und Sprechhinweisen](docs/praesentation.md)
