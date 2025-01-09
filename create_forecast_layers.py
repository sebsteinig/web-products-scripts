"""
################################################################################
Function: create_forecast_layers.py
Purpose: This function generates ecCharts layer definition for CAMS variables 
         based on a ADS variables YAML configuration file and a JSON layer 
         template.
Authors: Miha Razinger, Sebastian Steinig
Version History:
    - 1.0 (2024-02): Initial creation of the function.
    - 1.1 (2025-01): Refactoring and switch to ADS variables master file for loop.
################################################################################
"""

#! /usr/bin/env python
import copy
import re
from pathlib import Path
from dotenv import load_dotenv
import os
from utils import load_config, load_template, write_layer, generate_short_names

################################################################################
# user-defined variables from .env file
load_dotenv()

LAYERDIR = os.getenv("LAYERDIR") # directory to store generated layers
VAR_CONFIG_FILE = "https://git.ecmwf.int/projects/CDS/repos/cads-forms-cams/raw/cams-europe-air-quality-forecasts/regional_fc_definitions.yaml?at=refs%2Fheads%2Fprod"  # either local or URL
BITBUCKET_TOKEN = os.getenv("BITBUCKET_TOKEN")  # for access to CONFIG in private Bitbucket repo
BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME")

Path(LAYERDIR).mkdir(parents=True, exist_ok=True)
################################################################################

def create_style_list(var_name, short_name):
    AQI_PARAMS = ["nitrogen_dioxide", "ozone", "particulate_matter_2p5um", "particulate_matter_10um", "sulphur_dioxide"]
    style = f"sh_{short_name}_web_surface_concentration"
    style_list = [style]
    if var_name in AQI_PARAMS:
        style_list.append(f"sh_{short_name}_aqi_surface_concentration")
    style_list.extend([
        "sh_Reds_surface_concentration",
        "sh_Purples_surface_concentration",
        "sh_Greens_surface_concentration",
        "sh_Oranges_surface_concentration"
    ])
    return style_list

def create_model_variable(config):
    model_var = {
        "name": "originating_centre",
        "title": "Model",
        "type": "choice",
        "menu": "true",
        "values": []
    }
    for model in sorted(config["model"]):
        cc = config["model"][model]["grib_representations"][0]
        key = f"{cc['centre']}_{cc['subCentre']}"
        model_var["values"].append(key)
    return model_var

def create_layer(var_name, var_data, template, config):
    # get variable details and handle some special cases
    unit = var_data["var_table_units"].split("netCDF:")[-1].replace("<sup>", "").replace("</sup>", "") if "netCDF:" in var_data["var_table_units"] else var_data["var_table_units"].replace("<sup>", "").replace("</sup>", "")
    short_name, short_name_with_spaces = generate_short_names(var_data["backend_api_name"])
    long_name = f"PM{var_name.split('_')[-1][:-2]}" if var_name.startswith("particulate") else var_name.replace("_", " ")

    # create list of styles based on variable name
    style_list = create_style_list(var_name, short_name)

    new_layer = copy.deepcopy(template)
    
    # update layer with variable details
    new_layer.update({
        "description": f"European {long_name} ground- and upper-level forecast",
        "keywords": f"deterministic, air quality, {short_name_with_spaces}, {long_name}, surface concentrations",
        "name": f"composition_europe_{short_name}_forecast_surface",
        "title": f'Ground- and upper-level {long_name} (provided by CAMS)',
        "style": f"sh_{short_name}_web_surface_concentration",
        "styles": style_list,
        "units": {"data": unit, "display": unit}
    })

    constituent_type = var_data["grib_representations"][-1]["constituentType"]
    new_layer["retrieve"]["data"].update({
        "constituentType": f"key_{constituent_type}",
        "expver": "5001"
    })

    # add list of models layer and stream definitions
    new_layer["variables"].append(create_model_variable(config))
    new_layer["variables"].append({
        "name": "stream",
        "title": "Statistics type",
        "type": "choice",
        "menu": "true",
        "values": ["oper", "dame", "damx"]
    })
    new_layer["variables"].append({
        "name": "type",
        "title": "Data type",
        "type": "choice",
        "menu": "true",
        "values": ["fc", "an"]
    })
    new_layer["variables"].append({
        "name": "level",
        "title": "Height level",
        "type": "choice",
        "menu": "true",
        "values": ["key_0", "key_100", "key_1000", "key_3000", "key_5000"]
    })

    return new_layer

def main():
    var_config_ = load_config(VAR_CONFIG_FILE)
    template = load_template("./etc/layer_template.json")

    # convert models and variables from list to dict
    var_config = {key: {item["frontend_api_name"]: item for item in var_config_[key]} for key in ["model", "variable"]}

    # process each non-hidden variable
    for var_name, var_data in var_config["variable"].items():
        if var_data.get("hidden", True):
            continue

        new_layer = create_layer(var_name, var_data, template, var_config)
        outfile = f"{LAYERDIR}/{new_layer['name']}.json"
        print(outfile)
        write_layer(outfile, new_layer)

if __name__ == "__main__":
    main()