# Beschreibung des NoSQL-Datenmodells

## Inhaltsverzeichnis

- [1. Überblick](#1-überblick)
- [2. Aufbau der Datenbank](#2-aufbau-der-datenbank)
- [3. Struktur eines Incident-Dokuments](#3-struktur-eines-incident-dokuments)
  - [3.1 Störungsdaten](#31-störungsdaten)
  - [3.2 Analyseergebnisse und Verarbeitungsinformationen](#32-analyseergebnisse-und-verarbeitungsinformationen)
- [4. Beispieldokument](#4-beispieldokument)
  - [Erklärung des Beispiels](#erklärung-des-beispiels)
- [5. Begründung der Modellierung](#5-begründung-der-modellierung)
  - [5.1 Ein Dokument pro Incident](#51-ein-dokument-pro-incident)
  - [5.2 Eingebettete Unterdokumente](#52-eingebettete-unterdokumente)
  - [5.3 Erweiterung während der Verarbeitung](#53-erweiterung-während-der-verarbeitung)
- [6. Eindeutigkeit und Aktualisierung](#6-eindeutigkeit-und-aktualisierung)
- [7. Validierung der Daten](#7-validierung-der-daten)
- [8. Beispielabfragen](#8-beispielabfragen)
  - [Datenbank auswählen](#datenbank-auswählen)
  - [Einen bestimmten Incident suchen](#einen-bestimmten-incident-suchen)
  - [Incidents mit hoher KI-Bewertung suchen](#incidents-mit-hoher-ki-bewertung-suchen)
  - [Noch nicht durch die KI bewertete Incidents suchen](#noch-nicht-durch-die-ki-bewertete-incidents-suchen)
  - [Vollständig bewertete Incidents suchen](#vollständig-bewertete-incidents-suchen)

## 1. Überblick

Das Projekt verwendet die dokumentenorientierte NoSQL-Datenbank MongoDB, um IT-Störungsmeldungen, sogenannte Incidents, zu speichern.

Die Anwendung importiert Incidents aus JSON- oder XML-Dateien und überführt sie in eine gemeinsame interne Struktur. Anschliessend werden die Incidents regelbasiert und durch eine KI bewertet. Die Ergebnisse werden im jeweiligen Incident-Dokument ergänzt.

## 2. Aufbau der Datenbank

Die Incident-Daten werden folgendermassen organisiert:

incident_db
└── incidents
    ├── Dokument für INC-001
    ├── Dokument für INC-002
    └── Dokument für INC-003

| Bestandteil | Name | Bedeutung |
|---|---|---|
| Datenbank | incident_db | Enthält die Daten der Anwendung |
| Collection | incidents | Enthält die gespeicherten Incidents |
| Dokument | Ein einzelner Incident | Enthält Angaben zur Störung und ihre Bewertungen |

Eine Collection ist mit einer Sammlung von Datensätzen vergleichbar. Ein Dokument beschreibt jeweils eine Störung. MongoDB speichert die Dokumente intern im BSON-Format, das unter anderem verschachtelte Objekte unterstützt.

Die Datenbank- und Collection-Namen sind in main.py (https://github.com/SUDOGODMODE/Mongo/blob/main/main.py) festgelegt.

## 3. Struktur eines Incident-Dokuments

Ein Incident-Dokument besteht aus drei Teilen:

1. Störungsdaten: Importierte Angaben zum Incident.
2. Analyseergebnisse: Bewertungen durch Regeln und KI.
3. Verarbeitungsinformationen: Abschlussmarkierungen und Messwerte der KI.

### 3.1 Störungsdaten

| Feld | Datentyp im aktuellen Projekt | Beschreibung |
|---|---|---|
| _id | ObjectId | Automatisch erzeugte, eindeutige Dokumentkennung |
| incident_id | String | Eindeutige fachliche Kennung des Incidents |
| zeitpunkt | String | Zeitpunkt Format |
| system_service | String | Betroffenes System oder betroffener Dienst |
| fehlermeldung | String | Beschreibung der Störung oder Logmeldung |
| schweregrad | String | Mitgelieferter Schweregrad |
| status | String | Bearbeitungsstand des Incidents |
| kategorie | String | Fachliche Zuordnung der Störung |
| bekannte_loesung | String oder null, optional | Bereits bekannte Lösung |

Die Felder und ihre Importregeln sind im JSON-Schema (https://github.com/SUDOGODMODE/Mongo/blob/main/schemas/incidents.schema.json) definiert.

### 3.2 Analyseergebnisse und Verarbeitungsinformationen

| Feld | Datentyp | Beschreibung |
|---|---|---|
| rated_ai | Boolean | Gibt an, ob die KI-Bewertung abgeschlossen ist |
| rated_manual | Boolean | Gibt an, ob die regelbasierte Bewertung abgeschlossen ist |
| impact_rating_ai | Unterdokument | KI-Bewertung und Begründung |
| rating_manual | Unterdokument | Regelbasierte Bewertung und Begründung |
| metrics_ai | Unterdokument | KI-Modell, Verarbeitungsdauer und Tokenverbrauch |

Beim erstmaligen Import setzt die Anwendung rated_ai und rated_manual auf false. Die Ergebnisfelder werden nach erfolgreicher Bewertung ergänzt.

Quellen: main.py (https://github.com/SUDOGODMODE/Mongo/blob/main/main.py), manual.py (https://github.com/SUDOGODMODE/Mongo/blob/main/manual.py), llm.py (https://github.com/SUDOGODMODE/Mongo/blob/main/llm.py).

## 4. Beispieldokument

Das folgende Beispiel beschreibt eine nicht erreichbare Shop-Datenbank. Die Werte dienen der Veranschaulichung; die Feldstruktur entspricht dem Projekt.

Die Darstellung verwendet die MongoDB-Shell-Schreibweise und ist daher kein reines JSON:

{
  _id: ObjectId("674000000000000000000001"),

  incident_id: "INC-001",
  zeitpunkt: "2026-11-12T09:15:00Z",
  system_service: "Shop-Datenbank",
  fehlermeldung: "Datenbank nicht erreichbar. Onlineshop ausgefallen.",
  schweregrad: "hoch",
  status: "in_bearbeitung",
  kategorie: "datenbank",
  bekannte_loesung: "Datenbankdienst prüfen und gegebenenfalls neu starten.",

  rated_ai: true,
  rated_manual: true,

  impact_rating_ai: {
    impact_rating: 8,
    impact_reason: "Der Onlineshop ist durch die Störung nicht verfügbar."
  },

  rating_manual: {
    impact_rating: 8,
    impact_reason: "impact=8; category=7; keywords=8; matched: nicht erreichbar"
  },

  metrics_ai: {
    model: "gemma3:4b",
    duration_seconds: 2.4,
    prompt_tokens: 350,
    completion_tokens: 45,
    total_tokens: 395
  }
}

### Erklärung des Beispiels

Der Incident besitzt die fachliche Kennung INC-001. Die Störung betrifft die Shop-Datenbank und wird aktuell bearbeitet.

Der importierte Schweregrad lautet hoch. Zusätzlich haben sowohl die KI als auch die regelbasierte Analyse eine Bewertung von 8 auf einer Skala von 1 bis 10 erzeugt.

Die beiden Bewertungen enthalten jeweils eine Begründung. Dadurch lässt sich nachvollziehen, warum ein bestimmter Wert vergeben wurde.

Das Unterdokument metrics_ai dokumentiert im Beispiel das verwendete Modell, die Dauer der KI-Anfrage und den Tokenverbrauch.

## 5. Begründung der Modellierung

### 5.1 Ein Dokument pro Incident

Alle Informationen zu einer Störung werden in einem gemeinsamen Dokument gespeichert. So können die Störungsdaten und die zugehörigen Analyseergebnisse zusammen abgerufen werden.

### 5.2 Eingebettete Unterdokumente

Die Bewertungen werden direkt im Incident gespeichert. Diese Modellierung wird als Embedding bezeichnet.

Beispiel:

impact_rating_ai: {
  impact_rating: 8,
  impact_reason: "Der Onlineshop ist durch die Störung nicht verfügbar."
}

Die Einbettung ist sinnvoll, weil eine Bewertung unmittelbar zu genau einem Incident gehört und üblicherweise gemeinsam mit diesem gelesen wird. Eine zusätzliche Collection für die Bewertungen ist für den aktuellen Anwendungsfall nicht erforderlich.

Die aktuelle Struktur speichert jeweils eine KI- und eine regelbasierte Bewertung pro Incident. Eine Historie mehrerer Bewertungsdurchläufe ist nicht vorgesehen. Quelle: main.py (https://github.com/SUDOGODMODE/Mongo/blob/main/main.py)

### 5.3 Erweiterung während der Verarbeitung

Ein frisch importierter Incident besitzt noch keine Analyseergebnisse. Diese werden erst nach erfolgreicher Verarbeitung ergänzt.

Das Dokument entwickelt sich somit während der Verarbeitung:

Importierte Störungsdaten
        ↓
Ergänzung der KI-Bewertung und KI-Messwerte
        ↓
Ergänzung der regelbasierten Bewertung

## 6. Eindeutigkeit und Aktualisierung

MongoDB erzeugt für jedes Dokument eine eindeutige _id. Zusätzlich verwendet die Anwendung die fachliche Kennung incident_id.

Auf incident_id wird ein eindeutiger Index erstellt:

db.incidents.createIndex(
  { incident_id: 1 },
  { unique: true }
)

Dadurch kann dieselbe Incident-ID nicht mehrfach in der Collection vorkommen.

Die Anwendung verwendet beim Import ein Upsert:

- Existiert die Incident-ID noch nicht, wird ein neues Dokument angelegt.
- Existiert die Incident-ID bereits, werden die importierten Angaben im vorhandenen Dokument aktualisiert.

Bereits abgeschlossene Bewertungen werden bei einem erneuten Import nicht automatisch neu berechnet. Wenn sich die Störungsdaten ändern, können die vorhandenen Bewertungen deshalb auf einem früheren Datenstand beruhen. Quelle: main.py (https://github.com/SUDOGODMODE/Mongo/blob/main/main.py)

## 7. Validierung der Daten

Die Anwendung prüft die Daten vor dem Speichern anhand eines JSON-Schemas beziehungsweise XML-Schemas.

Für den JSON-Import gelten unter anderem folgende Regeln:

- Alle grundlegenden Störungsfelder ausser bekannte_loesung sind Pflichtfelder.
- zeitpunkt muss eine gültige Datums- und Zeitangabe enthalten.
- schweregrad muss niedrig, mittel, hoch oder kritisch sein.
- status muss neu, in_bearbeitung, wartend, geloest oder geschlossen sein.
- Nicht vorgesehene zusätzliche Felder werden abgewiesen.

Ungültige Datensätze werden ausgesondert. Gültige Datensätze aus derselben Datei können weiterhin importiert werden.

Die Validierung erfolgt in der Anwendung. In der aktuellen Datenbankinitialisierung wird kein zusätzlicher MongoDB-Collection-Validator eingerichtet.

Quellen: JSON-Schema (https://github.com/SUDOGODMODE/Mongo/blob/main/schemas/incidents.schema.json), loaders.py (https://github.com/SUDOGODMODE/Mongo/blob/main/loaders.py), main.py (https://github.com/SUDOGODMODE/Mongo/blob/main/main.py).

## 8. Beispielabfragen

Die folgenden Abfragen können in der MongoDB-Shell mongosh ausgeführt werden.

### Datenbank auswählen

use incident_db

### Einen bestimmten Incident suchen

db.incidents.findOne({
  incident_id: "INC-001"
})

Diese Abfrage liefert den Incident mit der Kennung INC-001 einschliesslich seiner gespeicherten Bewertungen.

### Incidents mit hoher KI-Bewertung suchen

db.incidents.find({
  "impact_rating_ai.impact_rating": { $gte: 8 }
})

Diese Abfrage liefert alle Incidents mit einer KI-Bewertung von mindestens 8.

Die Punktnotation greift auf ein Feld innerhalb eines Unterdokuments zu. Der Operator $gte bedeutet „grösser oder gleich“.

### Noch nicht durch die KI bewertete Incidents suchen

db.incidents.find({
  rated_ai: false
})

Diese Abfrage entspricht der Auswahl, die die Anwendung für ausstehende KI-Bewertungen verwendet.

### Vollständig bewertete Incidents suchen

db.incidents.find({
  rated_ai: true,
  rated_manual: true
})
