# Mongo
Project for IN258
Siehe [Aufgabenstellung](Audgabe.md) für Projektaufgabe und Anforderungen

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

### File-Struktur
/modules
    json_parse.py
    xml_parse.py
    write_db.py
    get_entry_db.py
    process_manual.py
    process_ai.py
    export.py
/samples
    sample.json
    sample.xml
/exports
    export.csv
main.py



