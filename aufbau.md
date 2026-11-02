
main.py
Aufruf der Teile in korrekter Abfolge

config.py
Globales config-File mit allen anpassbaren Parametern (Pfade, URLs, Liste legitimer Listenwerte für z.B. Kategorien)

llm.py
build_request -> IN: ticket-daten, auswahl, was ausgewertet wird, OUT: Anfrage für KI in Message-Format, Optional mit Schema
send_request -> GENERISCH! Nicht speziell für den Use-Case! IN: message, schema (optional), OUT: KI-Output, Optional in Schema-Format, sonst reiner String

import.py
load_xml -> IN: Xml-File, OUT: Liste von Incidents - Validierung von Layout bereits hier  (? TBD)
load_json -> IN: Json-File, OUT: Liste von Incidents - Validierung von Layout bereits hier  (? TBD)

db.py
write_incidents -> IN: Liste von Incidents, OUT: Sinnvolle Statuswerte (TBD)
read_incidents -> Suchfunktion für relevante Felder (z.B. alle nicht bewerteten Incidents) OUT: Gefundene Incidents als Dict

rateman.py
rate_manually -> IN: Einzelner Incident, OUT: Rating 1-10 (analog KI) und Reason / Einordnung

compare.py
TBD