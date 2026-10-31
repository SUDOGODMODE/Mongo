"""Import validated incidents, retain errors, and export the chosen corpus."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ingest import (
    EVAL_IDS, REQUIRED, choose_incidents, load_json, load_xml,
    normalize_incident,
)
from storage import save_incidents


def _sample_record(document: dict) -> dict:
    record = {key: document[key] for key in (*REQUIRED, "bekannte_loesung")}
    record["zeitpunkt"] = record["zeitpunkt"].isoformat()
    return record


def import_dataset(json_path: Path, xml_path: Path, db, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    inputs = ((Path(json_path), "json", load_json), (Path(xml_path), "xml", load_xml))
    valid = []
    rejected = []
    seen_ids = set()
    read_count = 0

    for path, source, loader in inputs:
        for position, raw in enumerate(loader(path), start=1):
            read_count += 1
            document, errors = normalize_incident(raw, source)
            incident_id = raw.get("incident_id") if isinstance(raw, dict) else None
            if incident_id:
                if incident_id in seen_ids:
                    errors.append("incident_id: duplicate across input files")
                seen_ids.add(incident_id)
            if errors:
                rejected.append({
                    "source_file": path.name,
                    "source_position": position,
                    "incident_id": incident_id,
                    "errors": errors,
                    "raw": raw,
                })
            else:
                document["source_file"] = path.name
                valid.append(document)

    selection_path = output_dir / "dataset_ids.json"
    by_id = {document["incident_id"]: document for document in valid}
    if selection_path.exists():
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        selected_ids = selection["dataset_ids"]
        if (len(selected_ids) != 30 or len(set(selected_ids)) != 30
                or set(EVAL_IDS) - set(selected_ids) or set(selected_ids) - by_id.keys()):
            raise ValueError("dataset_ids.json does not match the valid input")
        selected = [by_id[incident_id] for incident_id in selected_ids]
    else:
        selected = choose_incidents(valid)
        selection = {
            "dataset_ids": [document["incident_id"] for document in selected],
            "evaluation_ids": list(EVAL_IDS),
        }

    if selection.get("evaluation_ids") != list(EVAL_IDS):
        raise ValueError("evaluation IDs changed in dataset_ids.json")

    save_incidents(db, selected)
    output_dir.mkdir(parents=True, exist_ok=True)
    selection_path.write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")

    failed_dir = output_dir / "failed"
    failed_dir.mkdir(exist_ok=True)
    (failed_dir / "import_errors.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in rejected),
        encoding="utf-8",
    )

    samples_dir = output_dir / "samples"
    samples_dir.mkdir(exist_ok=True)
    json_rows = [_sample_record(d) for d in selected if d["source_format"] == "json"]
    xml_rows = [_sample_record(d) for d in selected if d["source_format"] == "xml"]
    (samples_dir / "incidents_selected.json").write_text(
        json.dumps({"incidents": json_rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    root = ET.Element("incidents")
    for row in xml_rows:
        node = ET.SubElement(root, "incident")
        for key, value in row.items():
            child = ET.SubElement(node, key)
            if value is None:
                child.set("fehlend", "true")
            else:
                child.text = value
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(
        samples_dir / "incidents_selected.xml", encoding="utf-8", xml_declaration=True
    )

    return {"read": read_count, "valid": len(valid),
            "invalid": len(rejected), "selected": len(selected)}
