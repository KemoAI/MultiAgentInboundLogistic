
"""
   This data source represent the IBL Schema
"""
import json

def ibl_data_source(path: str , agent: str) -> dict[str : str]:
    try:
        with open(path, "r", encoding="utf-8") as config:
            config_file = json.load(config).get(agent, [])
    except FileNotFoundError:
        print(f"Error: {agent}_schema.json not found. Please create it.")
        exit()
    return config_file
