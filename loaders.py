"""Load and validate incidents, exporting rejected entries to config.PATH_ERROR."""

from copy import deepcopy
import json
from pathlib import Path
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker
from lxml import etree as ET

import config


def _write_atomic(path, body):
    """Replace a file only after its complete contents have been written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    try:
        temporary.write_bytes(body)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def move_to_done(source):
    """Archive a queue file after all its database writes succeeded."""
    source = Path(source)
    done_path = Path(config.PATH_DONE)
    done_path.mkdir(parents=True, exist_ok=True)
    destination = done_path / source.name
    if destination.exists():
        raise FileExistsError(f"Already archived: {destination}")
    source.rename(destination)


def move_to_failed(source):
    """Quarantine an unreadable or structurally invalid input file."""
    source = Path(source)
    failed_path = Path(config.PATH_ERROR)
    failed_path.mkdir(parents=True, exist_ok=True)
    destination = failed_path / f"{source.stem}_invalid_{uuid4().hex}{source.suffix}"
    source.rename(destination)
    return destination


def load_json(folder, name):
    source_path = Path(folder) / f"{name}.json"
    with source_path.open("r", encoding="utf-8") as datei:
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

    if failed:
        # Keep prior rejects intact when retrying the filtered import file.
        _write_atomic(
            Path(config.PATH_ERROR) / f"{name}_failed.json",
            json.dumps({"incidents": failed}, ensure_ascii=False, indent=2).encode("utf-8"),
        )
        data["incidents"] = incidents
        _write_atomic(source_path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    if not incidents:
        source_path.unlink()
    return incidents


def load_xml(folder, name):
    source_path = Path(folder) / f"{name}.xml"
    tree = ET.parse(str(source_path))

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
    done = ET.Element("incidents")
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
        done.append(deepcopy(incident))

    if len(failed):
        _write_atomic(
            Path(config.PATH_ERROR) / f"{name}_failed.xml",
            ET.tostring(failed, encoding="utf-8", xml_declaration=True, pretty_print=True),
        )
        _write_atomic(
            source_path,
            ET.tostring(done, encoding="utf-8", xml_declaration=True, pretty_print=True),
        )
    if not incidents:
        source_path.unlink()
    return incidents



