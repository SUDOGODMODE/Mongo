# Mongo
Project for IN258
Siehe [Aufgabenstellung](Aufgabe.md) für Projektaufgabe und Anforderungen


## Voraussetzungen
MongoDB als Storage für Incident-Daten.
Beispiel-Start für MongoDB:
```
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongodb/mongodb-community-server:latest
```


AI-Endpoint als Verarbeiter für Anfragen.
Beispiel-Start mit llama.cpp und gemma3:4b mit Q8_0 Quantisierung:
```
llama-server `
    -hf ggml-org/gemma-3-4b-it-GGUF:Q8_0 `
    --alias "gemma3:4b" `
    -ngl all `
    -c 8192 `
    --port 8080
```


## Architektur
Unten als Vorschlag grober Aufbau.

### Ablauf Verarbeitung
1. Daten aus JSON einlesen und in Liste von Python Dicts umwandeln.
2. Daten aus XML einlesen und in Liste von Python Dicts umwandeln.
3. Daten in noSQL DB schreiben.
4. Datensätze einzeln aus noSQL DB auslesen.
5a. Einzelnen Datensatz an manuellen Verarbeiter schicken.
6a. Ergebnis zurück in DB schreiben.
5b. Einzelnen Datensatz an AI-Endpoint schicken.
6b. Ergebnis zurück in DB schreiben.
7. Ergebnisse exportieren

## Practical setup and usage guide

This app imports IT incidents from JSON or XML, stores them in MongoDB, and
rates their impact from 1 (very low) to 10 (critical). It creates two ratings:
an AI rating and an automatic rule-based rating. The code calls the rule-based
rating "manual"; you do not need to enter scores yourself.

### 1. Prerequisites

- Python 3.12 or newer. The source uses Python 3.12 f-string syntax.
- Docker with a running Docker engine for the MongoDB command below, or an
  existing MongoDB server.
- `llama-server` from llama.cpp, installed and available in your terminal, or
  another compatible AI server. The app expects `/v1/chat/completions` with
  JSON-schema structured responses.
- Enough memory for the selected model. The first model download also needs
  internet access and disk space.

The commands below use **PowerShell**. Run Python commands from this project's
root directory so that relative paths point to the correct folders.

Create a virtual environment and install the Python dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If you use a newer Python version, replace `-3.12` with that version. The examples
use the virtual environment's Python directly, so activation is optional.

### 2. Start the prerequisites

Start Docker, then create and start MongoDB once:

```powershell
docker run -d --name mongodb -p 27017:27017 -v mongodb_data:/data/db mongodb/mongodb-community-server:latest
```

For subsequent starts, reuse the existing container:

```powershell
docker start mongodb
docker ps
```

The `mongodb_data` volume keeps the database when the container is stopped.

In a separate terminal, start the AI server and leave it running:

```powershell
llama-server `
    -hf ggml-org/gemma-3-4b-it-GGUF:Q8_0 `
    --alias "gemma3:4b" `
    -ngl all `
    -c 8192 `
    --port 8080
```

This requests GPU offloading. Adjust the offloading and model settings to your
hardware if the server cannot load the model. The first launch downloads it.

### 3. Configure the app

The settings are in [config.py](config.py):

| Setting | Default | Purpose |
| --- | --- | --- |
| `LLM_MODEL` | `gemma3:4b` | Must match the model name or alias served by the AI server. |
| `LLM_URL` | `http://localhost:8080/v1` | AI base URL, including `/v1`. |
| `MONGO_URL` | `mongodb://localhost:27017/` | MongoDB connection string. |
| `API_PORT` | `8000` | Upload API port when started with `python api.py`. |
| `PATH_IMPORT` | `./import` | Folder the worker scans for incoming files. |
| `PATH_DONE` | `./done` | Archive for successfully imported files. |
| `PATH_ERROR` | `./failed` | Rejected records and invalid files. |

Only `LLM_URL` and `MONGO_URL` support environment overrides. For example:

```powershell
$env:LLM_URL = "http://localhost:8080/v1"
$env:MONGO_URL = "mongodb://localhost:27017/"
```

Set overrides in each terminal that needs them before starting Python. Other
settings must be edited in `config.py`. A `.env` file is not loaded automatically.
Restart the affected Python processes after changing configuration.

The database name `incident_db` and collection name `incidents` are set in
`main.py` and `compare.py`. Rule weights and keyword mappings are in
[manual.py](manual.py); the AI instructions are in [llm.py](llm.py).

### 4. Run the app: API and main worker

Keep MongoDB and the AI server running. Start these two Python processes in
separate terminals, both from the project root.

**Terminal A: upload API**

```powershell
.\.venv\Scripts\python.exe api.py
```

The API listens on `http://127.0.0.1:8000` by default. Its interactive API docs
are at `http://127.0.0.1:8000/docs`. Alternatively, use
`.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000`;
with this command, the command-line port determines the port, not `API_PORT`.

**Terminal B: import and rating worker**

```powershell
.\.venv\Scripts\python.exe main.py
```

The worker creates the import folder and a unique index on `incident_id`. It
pauses for two seconds between processing cycles, imports queued files, then
runs AI scoring followed by rule-based scoring. AI requests can make a cycle
take substantially longer than two seconds.

The API only saves uploaded files. A successful upload response does not mean
that validation, database import, or rating has completed. The worker must be
running for those steps to happen. You can also use the worker without the API
by placing complete JSON or XML files directly into `import/`.

### 5. Upload incidents and check the results

With the API and worker running, send the included JSON and XML samples:

```powershell
.\.venv\Scripts\python.exe example_upload.py
```

Some sample records contain invalid data, so files appearing in `failed/` during
this demonstration are expected.

To upload your own file:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/upload" -H "Content-Type: application/json" --data-binary "@samples/incidents_sample_batch_01.json"
```

For XML, use an XML file and `Content-Type: application/xml` (or `text/xml`). Send
the file as the raw request body, not as multipart form data. The response
contains the generated filename, for example `{"filename":"INC_...json"}`.

Use the structures in [samples/](samples/) as templates. JSON requires an
`incidents` array; XML requires an `<incidents>` root containing `<incident>`
elements. Both formats require `incident_id`, `zeitpunkt`, `system_service`,
`fehlermeldung`, `schweregrad`, `status`, and `kategorie`. `bekannte_loesung` is
optional. Exact validation rules are in
[the JSON schema](schemas/incidents.schema.json) and
[the XML schema](schemas/incidents.xsd).

Check the worker terminal for progress and validation messages:

| Location | Meaning |
| --- | --- |
| `import/` | Files waiting for import, or retained for retry after certain failures. |
| `done/` | Valid records have been written to MongoDB. Ratings may still be pending. |
| `failed/*_failed.json` or `*_failed.xml` | Individual rejected records from an otherwise readable batch. Valid records continue through import. |
| `failed/*_invalid_*` | A whole file was quarantined because it could not be parsed or its structure was invalid. |
| MongoDB `incident_db.incidents` | Imported incidents, ratings, completion flags, and AI timing/token metrics. |

When a batch contains rejected records, the archived file contains only the
valid records. If every record is rejected, no file is archived in `done/`.
Correct rejected records before uploading them again.

An existing `incident_id` updates the stored incident instead of creating a
duplicate. Existing rating flags are preserved: re-uploading an incident does
**not** automatically recalculate completed ratings, even if its contents or the
configured model changed.

### 6. Manually run a comparison

Once incidents have both ratings, run:

```powershell
.\.venv\Scripts\python.exe compare.py
```

This creates or overwrites `comparison.csv` in the current directory. It reads
existing results from MongoDB; it does not trigger new ratings. The API and
worker do not need to be running for this export, but MongoDB must be available.

The CSV contains `incident_id`, `manual`, `ai`, `difference`, `manual_reason`,
and `ai_reason`. `difference` is the absolute difference between the two scores;
zero means agreement. Only incidents with both `rated_ai` and `rated_manual` set
to `True` are included. A file containing only headers means no incidents have
both completion flags yet. The worker does not export comparisons automatically.








