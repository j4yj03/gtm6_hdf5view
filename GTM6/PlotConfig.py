import json
from pathlib import Path
import logging


class PlotConfig(dict):
    
    def __init__(self, filename):
        super().__init__()
        self.filename = Path(filename)
        self.data = self.load_data()
        #logging.debug(self.data)

    def load_data(self):
        try:
            with self.filename.open('r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"File '{self.filename}' not found.")
            return {}

    def get_names(self):
        return [str(self.data[key]['name']) for key in self.data]
    
    def get_active_names(self):
        """return a list of names with only active plot options"""
        return [self.data[key]['name'] for key in self.data if 'active' in self.data[key] and self.data[key]['active']]

    def get_active_states(self):
        return [self.data[key]['active'] if 'active' in self.data[key] else None for key in self.data]
    
    def get_id_by_name(self, search_name:str):
        for key, value in self.data.items():
            if "name" in value and value["name"] == search_name:
                return key, value
        return None
    
    def get_values_by_name(self, search_name:str):
        for value in self.data.values():
            if "name" in value and value["name"] == search_name:
                return value.get("value", {})
        return None

    def get_value_dicts(self):
        return [self.data[key]['value'] if 'value' in self.data[key] else {} for key in self.data]

    def get_value_pairs(self):
        value_pairs = []
        for key, item in self.data.items():
            if 'value' in item:
                value_pairs.extend(item['value'].items())
        return value_pairs
    
    def update_key(self, which_key: str, data: dict):
        self.data[which_key] = data