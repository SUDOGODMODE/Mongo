### Vorab-Definition für den Incident-Vergleich

#### Bewertung
Beide Methoden erhalten dieselben zehn Incidents. Das automatische Rating wird durchgeführt. Für jeden Incident erfolgt noch ein manuelles Rating anhand der Tabelle unten:

| Score | Auswirkung |
|---|---|
| 1–2 | Kaum Auswirkungen |
| 3–4 | Lokale Einschränkung |
| 5–6 | Spürbare Störung eines Teams oder Ablaufs |
| 7–8 | Erhebliche Folgen für Betrieb oder Sicherheit |
| 9–10 | Kritische Folgen, etwa Produktionsstillstand oder grosser Datenabfluss |


#### Verarbeitungszeit
Wir führen beide Methoden aus. Die Messung erfolgt für die KI-Methode via Metriken und für die klassische Methode manuell. (Zeit hier ist vernachlässigbar.)

#### Reproduzierbarkeit
Wir vergleichen Score und Begründung mit zwei Läufen. Bei gleichen Eingaben und Regeln erwarten wir klassisch 100 % Übereinstimmung. Für beide KI-Läufe verwenden wir dasselbe Modell, denselben Prompt und dasselbe Temperature-Setting.
