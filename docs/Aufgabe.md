
### Aufgabe:
1. Incident-Daten aus zwei unterschiedlichen Austauschformaten einlesen,
2. die Daten in ein gemeinsames internes Format überführen,
3. die normalisierten Daten in einer NoSQL-Datenbank speichern,
4. eine ausgewählte Analyseaufgabe klassisch und KI-gestützt lösen,
5. die beiden Lösungsansätze vergleichen.

Verwendet:
• JSON als erstes Austauschformat,
• YAML oder XML als zweites Austauschformat,
• eine dokumentenorientierte NoSQL-Datenbank, beispielsweise MongoDB,
• einen bereitgestellten oder selbst erstellten Datensatz mit ungefähr 20 bis 30 Incidents.

#### Daten
Enthalten mindestens:
• eindeutige Incident-ID
• Zeitpunkt
• betroffenes System oder betroffener Service
• Fehler- oder Logmeldung
• Schweregrad
• Status
• Kategorie
• bekannte Lösung, sofern vorhanden
Fehlende oder fehlerhafte Angaben müssen erkannt und sinnvoll behandelt werden.

#### Analyse Aufgabe
A) Incident einer Kategorie zuordnen
-> B) Schweregrad eines Incidents bestimmen
C) ähnliche frühere Incidents finden
D) eine kurze Zusammenfassung eines Incidents erzeugen
E) einen passenden Lösungsvorschlag aus bekannten Lösungen auswählen

- Variante A: Klassische Lösung, verwendet z.B.:
• Schlüsselwörter • Regeln
• reguläre Ausdrücke • Datenbankabfragen
• Volltextsuche
- Variante B: KI-gestützte Lösung: Verwendet ein Sprachmodell oder einen anderen geeigneten
KI-Dienst. Die KI darf nur Empfehlungen erzeugen. Sie darf keine Befehle auf einem System
ausführen

#### Der Vergleich
Testet beide Varianten mit mindestens zehn Incidents. Definiert vor dem Test, wie Ihr die
Resultate bewerten wollt. Vergleicht mindestens folgende Kriterien:
• Qualität der Ergebnisse
• Zeitaufwand für die Verarbeitung
• Nachvollziehbarkeit
• Zuverlässigkeit und Reproduzierbarkeit
• mögliche Fehler und Risiken
Haltet die Ergebnisse in einer übersichtlichen Tabelle fest.
Beispiel:
Incident Erw. Ergebnis Klassische Lösung KI-Lösung Bewertung
INC-001 Datenbankfehler Datenbankfehler Datenbankfehler beide korrekt
INC-002 Netzwerkfehler unbekannt Netzwerkfehler KI besser

#### Lieferobjekte
1. vollständiger Quellcode
2. Beispieldaten in beiden Austauschformaten
3. kurze Installations- und Startanleitung
4. Beschreibung des NoSQL-Datenmodells
5. Testresultate des Vergleichs
6. kurze Schlussfolgerung von ungefähr einer halben bis einer Seite
Die Schlussfolgerung muss folgende Fragen beantworten:
→ Wo war die KI besser als die klassische Lösung?
→ Wo war die klassische Lösung besser?
→ Welche Fehler oder Risiken wurden beobachtet?
→ Würden Sie die KI-Lösung in einem produktiven System einsetzen?
→ Welche Kontrollmechanismen wären dafür notwendig?

#### Präsentation
Die Präsentation enthält:
● eine kurze Erklärung des Datenflusses
● eine Demonstration des Imports und der Speicherung
● je ein Beispiel der klassischen und der KI-gestützten Analyse
● die wichtigsten Ergebnisse des Vergleichs
 Ergebnispräsentation mit einer möglichst klaren Antwort auf die Leitfrage:
 10 – 15 Min.

#### Bewertung
Bereich Gewichtung
Austauschformate, Import und Validierung 20 %
NoSQL-Datenmodell und Abfragen 20 %
Klassische und KI-gestützte Umsetzung 25 %
Systematischer Vergleich 20 %
Dokumentation und Präsentation 15 %