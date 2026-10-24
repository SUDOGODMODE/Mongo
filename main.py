import llm as llm
import config as config
import json
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from pathlib import Path


client = MongoClient("mongodb://localhost:27017/")
db = client["incident_db"]
incidents_raw = db["incidents_raw"]
incidents_rated = db["incidents_rated"]
incidents_rated_ai = db["incidents_rated_ai"]

def load_json(folder, name):
    with open(f"{folder}/{name}.json", "r", encoding="utf-8") as datei: 
        data = json.load(datei)

    incidents = []
    for incident in data:
        incidents.append(incident)

    return(incidents)


def load_xml(folder, name):
    tree = ET.parse(f"{folder}/{name}.xml")
    root = tree.getroot()

    incidents = []
    for incident in root.findall("incident"):
        incident_dict = {
            child.tag: child.text.strip() if child.text else None
            for child in incident
        }
        incidents.append(incident_dict)

    return incidents


def write_mongo(db, collection, data):

    return

def read_mongo(db, collection, data):

    return

def update_mongo(db, collection, data):

    return


incidents = []
import_path = Path(config.PATH_IMPORT)

for file in import_path.iterdir():
    if file.is_file():
        match file.suffix.lower():
            case ".xml":
                incidents.extend(load_xml(file.parent, file.stem))
            case ".json":
                incidents.extend(load_json(file.parent, file.stem))


print(incidents)