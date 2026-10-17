import Mongo.llm as llm
import Mongo.config as config
import json
import xml.etree.ElementTree as ET

def load_json(folder, name):
    with open(f"{folder}/{name}.json", "r", encoding="utf-8") as datei: 
        data = json.load(datei)
    return(data)

def load_xml(folder, name):
    tree = ET.parse(f"{folder}/{name}.xml")
    root = tree.getroot()
    return(root)

def write_mongo():

    return

def read_mongo():

    return

def update_mongo():

    return
