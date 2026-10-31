# Incident-Worker mit MongoDB und Ollama

Dieses Projekt verwendet den ursprünglichen Python-Code aus `main.py`, `llm.py` und `config.py`. Der Worker liest JSON- und XML-Dateien aus `import/`, speichert Incidents in MongoDB und ruft die vorhandene Ollama-Bewertung auf. Die Bewertung bleibt bei der ursprünglichen Skala **1 bis 10**; `llm.py` erzeugt sein JSON-Schema weiterhin selbst.

## Start auf Fedora mit Podman

Bei einem neuen Klon den Feature-Branch auswählen: `git clone --branch feat/incident-pipeline-20261031 https://github.com/SUDOGODMODE/Mongo.git`. Auf dem bereits eingerichteten Fedora-Host liegt das Repository unter `~/Mongo`.

```bash
cd ~/Mongo
mkdir -p failed
podman-compose -f compose.yaml up -d mongodb ollama
podman-compose -f compose.yaml exec ollama ollama pull gemma3:4b
podman-compose -f compose.yaml up -d --build worker
podman-compose -f compose.yaml ps
podman-compose -f compose.yaml logs -f worker
```

Compose startet drei Dienste: MongoDB, Ollama und den Python-Worker. Die Daten von MongoDB und das heruntergeladene Modell liegen in benannten Volumes. Die Hostports `27017` und `11434` sind nur an `127.0.0.1` gebunden. Der Worker nutzt innerhalb des Compose-Netzes die Dienstnamen `mongodb` und `ollama`. `restart: unless-stopped` startet einen beendeten Container erneut.

Für automatischen Start nach einem Fedora-Neustart ist die Datei `deploy/incident-stack.service` vorgesehen. Auf diesem Fedora-Host ist sie als User-Dienst installiert und aktiviert; `Linger` für Benutzer `max` ist eingeschaltet. Auf einem neuen Host:

```bash
mkdir -p ~/.config/systemd/user
cp deploy/incident-stack.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now incident-stack.service
sudo loginctl enable-linger "$USER"
systemctl --user status incident-stack.service
```

Nach Änderungen an `main.py`, `config.py` oder `llm.py` den Worker mit `podman-compose -f compose.yaml up -d --build --force-recreate worker` neu bauen und starten. Bereits bewertete unveränderte Incidents werden anhand ihrer Prüfsumme übersprungen.

Der Systemd-Dienst startet **nur Compose**; ein zweiter Python-Prozess wird dadurch nicht gestartet. Mit `systemctl --user stop incident-stack.service` wird der Stack gestoppt, die Datenvolumes bleiben erhalten.

Beim ersten Start verarbeitet der Worker die bereits vorhandenen Beispieldateien in `import/`. Das Modell kann pro Incident mehrere Sekunden benötigen. Neue oder geänderte `.json`- und `.xml`-Dateien werden anschließend ohne Neustart gefunden; die Schleife prüft den Ordner alle fünf Sekunden. Für einen manuellen Einmallauf auf Fedora kann `.venv/bin/python main.py --once` verwendet werden. Dafür werden `pymongo` und `requests` aus `requirements.txt` benötigt.

## Datenformat und Ablauf

JSON enthält ein Objekt mit einer Liste unter `incidents`; XML enthält `<incidents><incident>...</incident></incidents>`. Der Worker übernimmt die Felder aus der Datei und verlangt nur eine nichtleere `incident_id`. Für die KI-Bewertung müssen `system_service` und `fehlermeldung` vorhanden sein. Der vorhandene `schweregrad` wird **nicht** an Ollama gesendet.

Beim ersten geprüften Durchlauf der zwei mitgelieferten Dateien wurden 100 Einträge gelesen: 99 mit ID in `incidents_raw`, 97 mit KI-Ergebnis und drei Fehler im Verzeichnis `failed/`. Weitere Feldwerte werden aus der Quelle übernommen; der Worker erzwingt keine neue feste Status- oder Schweregradliste.

Die MongoDB-Datenbank `incident_db` enthält:

| Collection | Inhalt |
| --- | --- |
| `incidents_raw` | Eingelesene Incidents, per `incident_id` aktualisiert |
| `incidents_rated_ai` | Ollama-Ergebnis `impact_rating` (1–10) und `impact_reason`; neue Worker-Ergebnisse tragen `origin: "worker"` |
| `processed_files` | Prüfsumme je Datei, damit unveränderte Dateien nicht erneut verarbeitet werden |

Ändert sich eine Datei, verarbeitet der Worker sie erneut. Bereits erfolgreich bewertete, unveränderte Incidents werden dabei übersprungen. Schlägt Ollama vorübergehend fehl, versucht der Worker den betroffenen Eintrag beim nächsten Durchlauf erneut.

## Ergebnisse und Fehler ansehen

```bash
podman-compose -f compose.yaml logs --tail 50 worker
podman-compose -f compose.yaml exec mongodb mongosh incident_db --quiet \
  --eval 'db.incidents_rated_ai.find({origin:"worker"},{_id:0,incident_id:1,impact_rating:1,impact_reason:1}).limit(5).toArray()'
podman-compose -f compose.yaml exec mongodb mongosh incident_db --quiet \
  --eval 'db.incidents_raw.countDocuments({})'
ls -l failed/
```

Für eine defekte Datei oder einen nicht bewertbaren Incident schreibt der Worker `failed/DATEINAME.errors.jsonl`. Die Datei enthält Quelldatei, Position und Fehler. Fehler in einer Datei stoppen den Dienst nicht. Die Worker-Logs zeigen Verbindungs- und Modellfehler.

## Entwicklung

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt pytest
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Die Tests prüfen beide ursprünglichen Formate, MongoDB-Upserts, erneute Scans, geänderte Dateien und die Verarbeitung nach einer defekten Datei. MongoDB muss für die Integrationstests laufen. Die ursprünglichen Quellen in `import/` und die Aufgabenstellung in [Aufgabe.md](Aufgabe.md) bleiben erhalten.
