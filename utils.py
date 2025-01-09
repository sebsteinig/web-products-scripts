import os
import yaml
import json
import requests
from urllib.parse import urlparse
import re

def load_config(config_path):
    """Load configuration from either local file or remote Bitbucket URL"""
    if 'git.ecmwf.int' in config_path:
        username = os.getenv('BITBUCKET_USERNAME')
        token = os.getenv('BITBUCKET_TOKEN')
        auth = (username, token)
        
        response = requests.get(config_path, auth=auth)
        response.raise_for_status()
        
        return yaml.safe_load(response.text)
    else:
        # Assume it's a public GitHub repo or local file
        response = requests.get(config_path)
        response.raise_for_status()
        
        return yaml.safe_load(response.text)
    

def load_template(template_path):
    with open(template_path) as f:
        return json.loads(f.read())
    

def write_layer(outfile, new_layer):
    with open(outfile, "w") as fo:
        json.dump(new_layer, fo, sort_keys=True, indent=4)

def generate_short_names(backend_api_name: str) -> tuple[str, str]:
    # Generates standardized short names from a backend API name.
    short_name = re.sub(r"^C_|_USI$", "", backend_api_name).lower().replace("pm25", "pm2p5")
    short_name_with_spaces = short_name.replace("_", " ")
    return short_name, short_name_with_spaces