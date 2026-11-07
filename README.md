# Mongo
Projekt für IN258
Siehe [Aufgabenstellung](Aufgabe.md) für Projektaufgabe und Anforderungen.

## Voraussetzungen

MongoDB als Speicher für Incident-Daten.
Beispiel zum Starten von MongoDB:

```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongodb/mongodb-community-server:latest
```

KI-Endpunkt zur Verarbeitung der Anfragen.
Beispiel mit llama.cpp und gemma3:4b mit Q8_0-Quantisierung:

```powershell
llama-server `
    -hf ggml-org/gemma-3-4b-it-GGUF:Q8_0 `
    --alias "gemma3:4b" `
    -ngl all `
    -c 8192 `
    --port 8080
```

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

### 1. Voraussetzungen

- Python 3.12 oder neuer. Der Quellcode verwendet die f-String-Syntax von Python 3.12.
- Docker mit laufender Docker Engine für den unten gezeigten MongoDB-Befehl
  oder ein bereits vorhandener MongoDB-Server.
- `llama-server` aus llama.cpp, installiert und im Terminal verfügbar, oder
  ein anderer kompatibler KI-Server. Die Anwendung erwartet
  `/v1/chat/completions` mit strukturierten Antworten nach einem JSON-Schema.
- Genügend Arbeitsspeicher für das gewählte Modell. Für den ersten Download
  werden ausserdem eine Internetverbindung und freier Speicherplatz benötigt.

Die folgenden Befehle verwenden **PowerShell**. Führe Python-Befehle im
Hauptverzeichnis dieses Projekts aus, damit relative Pfade auf die richtigen
Ordner zeigen.

Erstelle eine virtuelle Umgebung und installiere die Python-Abhängigkeiten:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Wenn du eine neuere Python-Version verwendest, ersetze `-3.12` durch diese
Version. Die Beispiele verwenden Python direkt aus der virtuellen Umgebung;
deren Aktivierung ist daher optional.

### 2. Benötigte Dienste starten

Starte Docker. Erstelle und starte anschliessend einmalig den MongoDB-Container:

```powershell
docker run -d --name mongodb -p 27017:27017 -v mongodb_data:/data/db mongodb/mongodb-community-server:latest
```

Verwende bei späteren Starts den vorhandenen Container:

```powershell
docker start mongodb
docker ps
```

Das Volume `mongodb_data` bewahrt die Datenbank auch dann auf, wenn der
Container gestoppt wird.

Starte den KI-Server in einem separaten Terminal und lasse ihn laufen:

```powershell
llama-server `
    -hf ggml-org/gemma-3-4b-it-GGUF:Q8_0 `
    --alias "gemma3:4b" `
    -ngl all `
    -c 8192 `
    --port 8080
```

Dieser Befehl fordert die Auslagerung der Modellberechnung auf die GPU an.
Passe die GPU-Auslagerung und die Modelleinstellungen an deine Hardware an,
falls der Server das Modell nicht laden kann. Beim ersten Start wird das
Modell heruntergeladen.

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

### 4. Anwendung starten: API und Hauptverarbeitung

Lasse MongoDB und den KI-Server laufen. Starte die folgenden beiden
Python-Prozesse in separaten Terminals, jeweils im Hauptverzeichnis des Projekts.

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
