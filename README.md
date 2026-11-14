# Mongo
Projekt für IN258
Siehe [Aufgabenstellung](Aufgabe.md) für Projektaufgabe und Anforderungen.

## Voraussetzungen

Python 3.12+, Docker **oder** Podman für MongoDB und `llama-server` für die
lokale KI-Bewertung. Nach der einmaligen Installation startet [start.py](start.py)
die benötigten Dienste in der richtigen Reihenfolge. Die vollständigen Schritte
stehen unter [Einrichtung und Verwendung](#anleitung-zur-einrichtung-und-verwendung).

## Architektur

Der folgende Ablauf zeigt den groben Aufbau der Anwendung.

### Verarbeitungsablauf

1. Daten aus JSON oder XML einlesen und in eine Liste von Python-Dictionaries umwandeln.
2. Daten in der NoSQL-Datenbank speichern.
3. Noch nicht bewertete Datensätze einzeln aus der Datenbank lesen.
4. Datensätze an den KI-Endpunkt senden und die Ergebnisse in der Datenbank speichern.
5. Datensätze regelbasiert bewerten und die Ergebnisse in der Datenbank speichern.
6. Ergebnisse bei Bedarf mit `compare.py` exportieren.

## Anleitung zur Einrichtung und Verwendung

Diese Anwendung importiert IT-Incidents aus JSON oder XML, speichert sie in
MongoDB und bewertet ihre Auswirkungen von 1 (sehr gering) bis 10 (kritisch).
Sie erstellt zwei Bewertungen: eine KI-Bewertung und eine automatische,
regelbasierte Bewertung. Im Code heisst die regelbasierte Bewertung „manual“;
Bewertungen müssen also nicht von Hand eingegeben werden.

Das mitgelieferte Feld `schweregrad` dient als ergänzender Hinweis. Die
regelbasierte Bewertung gewichtet es mit 15 %, Schlüsselwörter mit 60 % und
die Kategorie mit 25 %. Fehlende oder unbekannte Komponenten werden
ausgelassen; die verbleibenden Gewichte werden entsprechend normalisiert.
Das Feld `schweregrad` wird nicht zusätzlich nach Schlüsselwörtern durchsucht.
Die KI wird angewiesen, zunächst die konkreten Incident-Angaben zu bewerten
und `schweregrad` nur schwach zu berücksichtigen. Diese Prompt-Anweisung
garantiert keine feste prozentuale Gewichtung beim Sprachmodell.

### 1. Voraussetzungen

- Python 3.12 oder neuer. Der Quellcode verwendet die f-String-Syntax von Python 3.12.
- Docker oder Podman mit funktionsfähiger Containerumgebung für MongoDB,
  oder ein bereits erreichbarer MongoDB-Server. Unter macOS und Windows
  benötigt Podman eine initialisierte Podman-Maschine.
- `llama-server` aus llama.cpp, installiert und im Terminal verfügbar, oder
  ein anderer kompatibler KI-Server. Die Anwendung erwartet
  `/v1/chat/completions` mit strukturierten Antworten nach einem JSON-Schema.
- Genügend Arbeitsspeicher für das gewählte Modell. Für den ersten Download
  werden ausserdem eine Internetverbindung und freier Speicherplatz benötigt.

Die manuellen Beispiele weiter unten verwenden **PowerShell**. Das Startskript
funktioniert unter macOS, Linux und Windows und setzt für alle Anwendungsprozesse
das Projektverzeichnis als Arbeitsverzeichnis.

Erstelle eine virtuelle Umgebung und installiere die Python-Abhängigkeiten:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Wenn du eine neuere Python-Version verwendest, ersetze `-3.12` durch diese
Version. Die Beispiele verwenden Python direkt aus der virtuellen Umgebung;
deren Aktivierung ist daher optional.

Unter macOS und Linux legst du `.venv` so an:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### 2. Produkt starten

Starte das gesamte Produkt mit einem Befehl im Projektverzeichnis:

```powershell
py -3.12 start.py
```

Unter macOS und Linux:

```bash
python3 start.py
```

`start.py` fragt im Terminal ausdrücklich, ob MongoDB mit **Docker** oder
**Podman** gestartet werden soll. Gib den Namen oder die angezeigte Nummer ein;
es gibt keine vorausgewählte Antwort. Docker und Podman verwalten **getrennte**
Container und Volumes. Wähle deshalb das System, in dem die Projektdaten liegen.
Das Skript wechselt bei einem Fehler nicht stillschweigend zum anderen System.

Beispiel, wenn beide Programme installiert sind:

```text
Wähle das Container-System für MongoDB. Docker und Podman haben getrennte Daten-Volumes.
  1) docker
  2) podman
Auswahl (Name oder Nummer): 2
Verwende podman für MongoDB.
```

Die Nummern richten sich nach den installierten Programmen. Du kannst auch
`docker` oder `podman` als Namen eingeben. Die Eingabe wird abgefragt, selbst
wenn auf dem lokalen MongoDB-Port bereits eine Datenbank erreichbar ist.

Nach der Auswahl startet es die gewählte Containerumgebung bei Bedarf,
startet einen vorhandenen Container `mongodb` oder erstellt ihn beim ersten Mal
mit dem Image `mongodb/mongodb-community-server:latest`. Die Daten liegen im
benannten Volume `mongodb_data`; es bleibt auch nach einem Containerstopp
erhalten. Fehlt der gewählte Container oder ist er gestoppt, bricht das Skript
bei belegtem MongoDB-Port ab, statt stillschweigend eine zweite Datenbank
anzulegen oder zu starten.

Für automatisierte Starts ohne Terminal kann die Auswahl als Argument erfolgen:

```powershell
py -3.12 start.py --runtime podman
```

Mögliche Werte für `--runtime` sind `docker` und `podman`. Ohne Argument und mit `CONTAINER_RUNTIME = None` ist
ein interaktives Terminal erforderlich; bei fehlender Eingabe startet kein
Container. Für einen bereits konfigurierten **externen** MongoDB-Server ist
keine Container-Auswahl nötig. Auf macOS und Windows versucht das Skript, eine
vorhandene Podman-Maschine zu starten; fehlt sie noch, muss sie einmalig mit
`podman machine init` angelegt werden.

Nach einer erfolgreichen MongoDB-Verbindung startet das Skript bei Bedarf
`llama-server` mit `ggml-org/gemma-3-4b-it-GGUF:Q8_0` (Alias `gemma3:4b`,
GPU-Auslagerung `all`, Kontext 8192, Port 8080). Fehlt das Modell im Cache,
wird es dabei heruntergeladen. Passe die Modell- oder GPU-Einstellungen in `config.py` an,
falls diese Vorgaben nicht zur Hardware passen. Danach starten Upload-API und
Importprozess. Jeder nächste Schritt beginnt erst nach einer Bereitschaftsprüfung
des vorherigen Dienstes. API-Dokumentation: `http://127.0.0.1:8000/docs`.

Mit Ctrl+C beendet das Skript die von ihm gestarteten Python- und KI-Prozesse.
MongoDB und bereits zuvor laufende Dienste bleiben aktiv. Die Zeitlimits sind
mit `--runtime-timeout`, `--mongo-timeout`, `--llm-timeout` und `--api-timeout`
in Sekunden einstellbar. Der erste Image-Download kann zusätzlich bis zu
zehn Minuten dauern. Fehlende Programme oder Python-Pakete meldet das
Skript; es installiert diese Voraussetzungen nicht automatisch.

Alle Start-Einstellungen stehen in `config.py`; `start.py` muss nicht angepasst
werden. `CONTAINER_RUNTIME = None` fragt nach Docker/Podman; mit `"docker"` oder
`"podman"` entf?llt die Nachfrage auch ohne CLI-Argument. CLI-Argumente k?nnen
die Konfiguration f?r einen einzelnen Start ?berschreiben.

Weitere Einstellungen: `MONGO_CONTAINER_NAME`, `MONGO_IMAGE`, `MONGO_VOLUME`,
`LLM_EXECUTABLE`, `LLM_HF_MODEL`, `LLM_GPU_LAYERS`, `LLM_CONTEXT_SIZE`,
`LLM_EXTRA_ARGS` und `VENV_PATH`. Startzeitlimits und Pr?fintervalle stehen
im selben Konfigurationsabschnitt, alle Zeitangaben sind in Sekunden.
Beim ?ndern von Containername oder Volume werden bestehende Daten nicht
automatisch ?bertragen.

### 3. Anwendung konfigurieren

Die Einstellungen befinden sich in [config.py](config.py):

| Einstellung | Standardwert | Zweck |
| --- | --- | --- |
| `LLM_MODEL` | `gemma3:4b` | Muss mit dem Modellnamen oder Alias des KI-Servers übereinstimmen. |
| `LLM_URL` | `http://localhost:8080/v1` | Basis-URL des KI-Servers, einschliesslich `/v1`. |
| `MONGO_URL` | `mongodb://localhost:27017/` | Verbindungsadresse für MongoDB. |
| `API_PORT` | `8000` | Port der Upload-API beim Start mit `python api.py`. |
| `PATH_IMPORT` | `./import` | Ordner, den der Verarbeitungsprozess nach neuen Dateien durchsucht. |
| `PATH_DONE` | `./done` | Archiv für erfolgreich importierte Dateien. |
| `PATH_ERROR` | `./failed` | Abgewiesene Datensätze und ungültige Dateien. |

Nur `LLM_URL` und `MONGO_URL` lassen sich durch Umgebungsvariablen überschreiben.
Zum Beispiel:

```powershell
$env:LLM_URL = "http://localhost:8080/v1"
$env:MONGO_URL = "mongodb://localhost:27017/"
```

Setze diese Variablen vor dem Python-Start in jedem Terminal, das sie benötigt.
Andere Einstellungen müssen in `config.py` angepasst werden. Eine `.env`-Datei
wird nicht automatisch geladen. Starte die betroffenen Python-Prozesse nach
Konfigurationsänderungen neu.

Der Datenbankname `incident_db` und der Collection-Name `incidents` sind in
`main.py` und `compare.py` festgelegt. Die Regelgewichtungen und
Schlüsselwortzuordnungen befinden sich in [manual.py](manual.py), die
Anweisungen für die KI in [llm.py](llm.py).

### 4. Optional: API und Hauptverarbeitung manuell starten

Für den normalen Betrieb übernimmt [start.py](start.py) diese Schritte.
Falls du die Dienste einzeln starten möchtest, lasse MongoDB und den KI-Server
laufen und starte die folgenden beiden Python-Prozesse in separaten Terminals,
jeweils im Hauptverzeichnis des Projekts.

**Terminal A: Upload-API**

```powershell
.\.venv\Scripts\python.exe api.py
```

Die API ist standardmässig unter `http://127.0.0.1:8000` erreichbar. Die
interaktive API-Dokumentation findest du unter `http://127.0.0.1:8000/docs`.
Alternativ kannst du
`.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000`
verwenden. Bei diesem Befehl bestimmt der angegebene Kommandozeilenparameter
den Port; die Einstellung `API_PORT` wird dabei nicht verwendet.

**Terminal B: Import und Bewertung**

```powershell
.\.venv\Scripts\python.exe main.py
```

Der Verarbeitungsprozess erstellt den Importordner und einen eindeutigen Index
auf `incident_id`. Zwischen den Verarbeitungsdurchläufen wartet er zwei
Sekunden. Er importiert wartende Dateien und führt danach zuerst die
KI-Bewertung und anschliessend die regelbasierte Bewertung aus. Durch
KI-Anfragen kann ein Durchlauf deutlich länger als zwei Sekunden dauern.

Die API speichert hochgeladene Dateien. Eine erfolgreiche Upload-Antwort
bedeutet noch nicht, dass Validierung, Datenbankimport oder Bewertung
abgeschlossen sind. Dafür muss der Verarbeitungsprozess laufen. Du kannst ihn
auch ohne API verwenden, indem du vollständige JSON- oder XML-Dateien direkt
im Ordner `import/` ablegst.

### 5. Incidents hochladen und Ergebnisse prüfen

Wenn API und Verarbeitungsprozess laufen, kannst du die mitgelieferten JSON-
und XML-Beispiele senden:

```powershell
.\.venv\Scripts\python.exe example_upload.py
```

Einige Beispieldatensätze enthalten ungültige Daten. Dass bei dieser
Demonstration Dateien in `failed/` erscheinen, ist daher zu erwarten.

Eine eigene Datei kannst du mit folgendem Befehl hochladen:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/upload" -H "Content-Type: application/json" --data-binary "@samples/incidents_sample_batch_01.json"
```

Verwende für XML eine XML-Datei und `Content-Type: application/xml` oder
`text/xml`. Sende den Dateiinhalt direkt als Anfrageinhalt, nicht als
Multipart-Formulardaten. Die Antwort enthält den erzeugten Dateinamen,
zum Beispiel `{"filename":"INC_...json"}`.

Verwende die Strukturen in [samples/](samples/) als Vorlagen. JSON benötigt
ein `incidents`-Array. XML benötigt ein Wurzelelement `<incidents>` mit
`<incident>`-Elementen. Beide Formate verlangen die Felder `incident_id`,
`zeitpunkt`, `system_service`, `fehlermeldung`, `schweregrad`, `status` und
`kategorie`. `bekannte_loesung` ist optional. Die genauen Validierungsregeln
stehen im [JSON-Schema](schemas/incidents.schema.json) und im
[XML-Schema](schemas/incidents.xsd).

Im Terminal des Verarbeitungsprozesses siehst du Fortschritts- und
Validierungsmeldungen:

| Speicherort | Bedeutung |
| --- | --- |
| `import/` | Dateien warten auf den Import oder bleiben nach bestimmten Fehlern für einen erneuten Versuch erhalten. |
| `done/` | Gültige Datensätze wurden in MongoDB gespeichert. Bewertungen können noch ausstehen. |
| `failed/*_failed.json` oder `*_failed.xml` | Einzelne abgewiesene Datensätze aus einer ansonsten lesbaren Datei. Gültige Datensätze werden weiter importiert. |
| `failed/*_invalid_*` | Eine ganze Datei wurde ausgesondert, weil sie nicht eingelesen werden konnte oder ihre Struktur ungültig war. |
| MongoDB `incident_db.incidents` | Importierte Incidents, Bewertungen, Abschlussmarkierungen sowie Zeit- und Token-Messwerte der KI. |

Enthält eine Datei abgewiesene Datensätze, enthält die archivierte Datei nur
die gültigen Datensätze. Werden alle Datensätze abgewiesen, wird keine Datei
in `done/` archiviert. Korrigiere abgewiesene Datensätze vor dem erneuten Upload.

Bei einer bereits vorhandenen `incident_id` wird der gespeicherte Incident
aktualisiert, statt ein Duplikat anzulegen. Vorhandene Bewertungsmarkierungen
bleiben erhalten: Ein erneuter Upload berechnet abgeschlossene Bewertungen
**nicht** automatisch neu, auch wenn sich der Inhalt oder das konfigurierte
Modell geändert hat.

### 6. Vergleich manuell ausführen

Sobald Incidents beide Bewertungen haben, führe folgenden Befehl aus:

```powershell
.\.venv\Scripts\python.exe compare.py
```

Dadurch wird `comparison.csv` im aktuellen Verzeichnis erstellt oder
überschrieben. Das Skript liest vorhandene Ergebnisse aus MongoDB und löst
keine neuen Bewertungen aus. API und Verarbeitungsprozess müssen für diesen
Export nicht laufen; MongoDB muss jedoch erreichbar sein.

Die CSV-Datei enthält `incident_id`, `manual`, `ai`, `difference`,
`manual_reason` und `ai_reason`. `difference` ist der absolute Unterschied
zwischen den beiden Bewertungen; null bedeutet Übereinstimmung. Es werden
nur Incidents berücksichtigt, bei denen sowohl `rated_ai` als auch
`rated_manual` auf `True` gesetzt sind. Enthält die Datei nur Spaltenüberschriften,
hat noch kein Incident beide Abschlussmarkierungen. Der Verarbeitungsprozess
exportiert Vergleiche nicht automatisch.
