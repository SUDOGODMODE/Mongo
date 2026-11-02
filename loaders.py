"""Load and validate incidents, exporting rejected entries to config.PATH_ERROR."""

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from lxml import etree as ET

import config

def load_json(folder, name):
    with open(f"{folder}/{name}.json", "r", encoding="utf-8") as datei:
        data = json.load(datei)

    schema_path = Path(__file__).parent / "schemas" / "incidents.schema.json"
    with schema_path.open(encoding="utf-8") as source:
        schema = json.load(source)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    # Validate the file structure separately from its individual incidents.
    envelope = dict(data) if isinstance(data, dict) else data
    if isinstance(data, dict) and isinstance(data.get("incidents"), list):
        envelope["incidents"] = []
    validator.validate(envelope)

    incidents = []
    failed = []
    for index, incident in enumerate(data["incidents"]):
        errors = list(validator.iter_errors({"incidents": [incident]}))
        if errors:
            failed.append(incident)
            details = "; ".join(error.message for error in errors)
            print(f"{name}.json incident [{index}] rejected: {details}")
        else:
            incidents.append(incident)

    failed_path = Path(config.PATH_ERROR)
    failed_path.mkdir(parents=True, exist_ok=True)
    with (failed_path / f"{name}_failed.json").open("w", encoding="utf-8") as target:
        json.dump({"incidents": failed}, target, ensure_ascii=False, indent=2)

    return incidents


def load_xml(folder, name):
    tree = ET.parse(f"{folder}/{name}.xml")

    schema_path = Path(__file__).parent / "schemas" / "incidents.xsd"
    schema = ET.XMLSchema(ET.parse(str(schema_path)))
    root = tree.getroot()
    # Keep root validation, but validate each child in its own document.
    envelope = deepcopy(root)
    for child in list(envelope):
        envelope.remove(child)
    schema.assertValid(envelope)

    incidents = []
    failed = ET.Element("incidents")
    for index, incident in enumerate(root):
        if not isinstance(incident.tag, str):
            continue  # XML comments and processing instructions are not records.
        document = ET.Element("incidents")
        document.append(deepcopy(incident))
        if not schema.validate(document):
            failed.append(deepcopy(incident))
            details = "; ".join(error.message for error in schema.error_log)
            print(f"{name}.xml incident [{index}] rejected: {details}")
            continue
        incident_dict = {
            child.tag: child.text.strip() if child.text else None
            for child in incident
            if isinstance(child.tag, str)
        }
        incidents.append(incident_dict)

    failed_path = Path(config.PATH_ERROR)
    failed_path.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(failed).write(
        str(failed_path / f"{name}_failed.xml"),
        encoding="utf-8", xml_declaration=True, pretty_print=True,
    )

    return incidents



