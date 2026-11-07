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





