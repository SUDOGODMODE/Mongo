# Vergleich und Schlussfolgerung

## Versuchsaufbau

Die Analyseaufgabe ist **B: Schweregrad bestimmen**. Vor dem Vergleich wurden zehn Incident-IDs mit fünf JSON- und fünf XML-Quellen sowie vier Schweregradstufen festgelegt. Die zehn Fälle gehören zum ausgewählten 30er-Korpus. Beide Verfahren sehen ausschließlich den betroffenen Service und die Fehlermeldung. Sie sehen weder das vorhandene Schweregradlabel noch Kategorie, Status oder bekannte Lösung. Das klassische Verfahren wendet geordnete Schlüsselwortregeln an; wenn keine passt, liefert es `unbestimmt`. Die KI ist das lokal in Ollama laufende Modell `gemma3:4b` mit JSON-Schema, Temperatur 0 und Seed 42.

Vor dem Lauf wurden diese Kriterien festgelegt: Qualität = Übereinstimmung mit dem vorhandenen Label; Zeitaufwand = Laufzeit pro Aufruf und Gesamtdauer; Nachvollziehbarkeit = Regelkennung beziehungsweise Modellbegründung; Zuverlässigkeit = gültige Antwort, Fehlerzahl und Übereinstimmung über drei Wiederholungen je Incident; Risiken = fachliche Fehleinstufungen, erfundene Begründungen und Abhängigkeit vom Modellserver. Die Referenzlabels stammen aus dem bereitgestellten Datensatz und wurden nicht unabhängig von Fachleuten geprüft.

## Messergebnis

Die vollständige maschinenlesbare Tabelle steht in [comparison.csv](../exports/comparison.csv), alle 60 Einzelläufe in [runs.csv](../exports/runs.csv), die aggregierten Kennzahlen in [summary.json](../exports/summary.json).

| Incident | Erwartet | Regeln | Ollama | Bewertung |
| --- | --- | --- | --- | --- |
| INC-2026-00010 | niedrig | niedrig | hoch | Regeln korrekt |
| INC-2026-00016 | kritisch | kritisch | hoch | Regeln korrekt |
| INC-2026-00021 | hoch | hoch | hoch | beide korrekt |
| INC-2026-00031 | mittel | mittel | hoch | Regeln korrekt |
| INC-2026-00050 | niedrig | niedrig | hoch | Regeln korrekt |
| INC-2026-00051 | hoch | hoch | mittel | Regeln korrekt |
| INC-2026-00062 | mittel | mittel | hoch | Regeln korrekt |
| INC-2026-00076 | kritisch | kritisch | hoch | Regeln korrekt |
| INC-2026-00081 | mittel | mittel | hoch | Regeln korrekt |
| INC-2026-00091 | hoch | hoch | hoch | beide korrekt |

Die Regeln trafen 30/30 Referenzlabels über drei Wiederholungen; Ollama 6/30. Beide Verfahren gaben für alle 30 Aufrufe eine gültige Einstufung ohne technischen Fehler zurück und waren bei allen zehn Incidents über die Wiederholungen konsistent. Die Regeln benötigten im Median 0,000012 s pro Aufruf und insgesamt 0,000378 s; Ollama 5,613542 s im Median und insgesamt 170,719985 s. Diese Laufzeiten wurden auf dem konkreten Fedora-Host gemessen und sind nicht auf andere Hardware übertragbar. Die Regelkennung zeigt die auslösenden Begriffe. Das Modell liefert freie Begründungen, die gelesen, aber nicht als Beweis für die Einstufung verstanden werden dürfen.

## Schlussfolgerung

Auf diesen zehn Fällen war die KI bei der Übereinstimmung mit den vorhandenen Schweregradlabels **in keinem Fall besser** als die klassische Lösung. Sie traf zwei Fälle, die auch die Regeln trafen. In acht Fällen waren die Regeln besser. Besonders auffällig ist die Tendenz des Modells, fast alles als `hoch` zu bewerten: Es überschätzte beispielsweise den einzelnen falschen Tenant und den WLAN-Verlust nach Standby, unterschätzte aber die als `kritisch` markierten Fälle mit ausgefallenem Switchport und vollem Backup-Repository. Die Regelbewertung war hier schnell und über ihre Kennung direkt nachvollziehbar.

Beobachtet wurden auch Begründungen mit unbelegten Details. Bei einem PostgreSQL-Fall sprach das Modell von einem „verwaisten“ Server, obwohl das nicht in den übergebenen Angaben stand. Bei einem Exchange-Fall unterstellte es einen nicht authentifizierten Benutzer. Solche Aussagen können Entscheider in die Irre führen. Ein technischer Modellfehler trat im echten Vergleich nicht auf; ein separater Test zeigt, dass ein Ausfall als Fehler protokolliert wird. Das Modell erhielt keine Berechtigung, Befehle auszuführen.

Der 100%-Wert der Regeln ist **kein Beleg für Überlegenheit bei neuen Daten**. Die Regeln wurden mit Kenntnis dieses kleinen Beispieldatensatzes entwickelt; die zehn Fälle sind daher keine unabhängige Testmenge. Zudem können vorhandene Labels selbst fragwürdig sein: Ein einzelner ausgefallener Switchport wird beispielsweise als `kritisch` geführt, ohne dass die Zahl betroffener Nutzer klar ist. Der Vergleich misst zunächst Übereinstimmung mit diesen Labels, nicht objektive fachliche Richtigkeit. Für belastbare Aussagen braucht es eine unabhängige Stichprobe, fachlich geprüfte Labels und eine vorher festgelegte Rubrik für Auswirkung und Dringlichkeit.

Für den produktiven Einsatz würde ich die KI nur als zusätzliche Empfehlung einführen, nicht als automatische Eskalations- oder Ausführungsinstanz. Menschen müssen die Einstufung besonders bei `hoch` und `kritisch` prüfen und freigeben. Erforderlich sind ein festes Ausgabeformat mit Validierung, Zeitlimits und Fehlerbehandlung, Protokolle der Eingaben und Modellversion, Schutz sensibler Incident-Daten, regelmäßige Stichproben gegen Expertenurteile sowie ein Fallback auf manuelle Bearbeitung. Erst nach einem unabhängigen Vergleich mit deutlich mehr Incidents und geklärter Bewertungsrubrik wäre eine weitergehende Automatisierung vertretbar.
