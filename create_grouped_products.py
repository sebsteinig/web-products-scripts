#! /usr/bin/env python
import copy
import json
from pathlib import Path
from dotenv import load_dotenv
import os
from utils import load_config, load_template, load_grouping, write_layer, generate_short_names

################################################################################
# user-defined variables from .env file
load_dotenv()

PACKAGE = "cams_air_quality"
PRODUCTDIR = os.getenv("PRODUCTDIR")
GROUPING_FILE = "./etc/air_quality_parameter_grouping.yaml"
VAR_CONFIG_FILE = "https://git.ecmwf.int/projects/CDS/repos/cads-forms-cams/raw/cams-europe-air-quality-forecasts/regional_fc_definitions.yaml?at=refs%2Fheads%2Fprod"  # either local or URL
BITBUCKET_TOKEN = os.getenv("BITBUCKET_TOKEN")  # for access to CONFIG in private Bitbucket repo
BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME")
TYPES = ['web', 'eea']

DATATYPES = {
    "fc": "forecast",
    "an": "analysis"
}

PRODUCTTYPES = {
    "hourly": {"stream": "oper"},
    "daily aggregated": {"stream": "$stream"}
}
################################################################################


def create_models_variable(config):
    """Create the models variable definition."""
    model_values = []
    model_labels = []

    # Add ensemble model first
    model_label = config["model"]["ensemble"]["form_label"]
    oc = config["model"]["ensemble"]["grib_representations"][0]
    model_values.append(f"{oc['centre']}_{oc['subCentre']}")
    model_labels.append(model_label)

    # Add other models
    for model in sorted(config["model"]):
        if model != "ensemble":
            model_label = config["model"][model]["form_label"]
            oc = config["model"][model]["grib_representations"][0]
            model_labels.append(model_label)
            model_values.append(f"{oc['centre']}_{oc['subCentre']}")

    return {
        "name": "originating_centre",
        "title": "Model",
        "type": "choice",
        "values": model_values,
        "labels": model_labels
    }

def create_product(var_name, var_data, template, var_config, type):
    """Create a new product definition for a given parameter."""
    short_name, short_name_with_spaces = generate_short_names(var_data["backend_api_name"])
    long_name = f"PM{var_name.split('_')[-1][:-2]}" if var_name.startswith("particulate") else var_name.replace("_", " ")

    new_product = copy.deepcopy(template)
    layer_name = f"composition_europe_{short_name}_forecast_surface"

    # Set layers
    new_product["layers"] = [
        {
            "class": "data",
            "layer_type": "eccharts",
            "name": layer_name,
            "style": f"sh_{short_name}_{type}_surface_concentration"
        },
        {
            "class": "data",
            "layer_type": "eccharts",
            "name": "foreground",
            "style": "medium_res_foreground"
        },
        {
            "class": "data",
            "layer_type": "eccharts",
            "name": "grid"
        },
        {
            "class": "data",
            "layer_type": "eccharts",
            "name": "boundaries",
            "style": "black_boundaries"
        }
    ]

    # Update product metadata
    new_product.update({
        "name": f"europe-{var_name}-forecast",
        "title": f"European air quality {long_name} forecast",
        "package": PACKAGE,
        "description": f"CAMS European {long_name} forecast",
        "click_features": {
            "options": [{
                "product": f"plume_cams_eu_{var_name}",
                "title": f"Ground-level {long_name} concentrations"
            }],
            "products": [f"plume_cams_eu_{var_name}"],
            "tooltip": f"Ground-level {long_name} concentrations"
        }
    })

    # Add models variable
    new_product["variables"].append(create_models_variable(var_config))

    return new_product

def main():
    var_config_ = load_config(VAR_CONFIG_FILE)
    template = load_template("./etc/product_template.json")
    
    # convert models and variables from list to dict
    var_config = {key: {item["frontend_api_name"]: item for item in var_config_[key]} for key in ["model", "variable"]}

    # loop through each style type
    for type_ in TYPES:
        grouping = load_grouping(GROUPING_FILE)
        if type_ == "eea":
            # only keep pollen variables for eea
            grouping = dict(filter(lambda item: "pollen" in item[0], grouping.items()))

        print(f"\nProcessing style type: {type_}")
        outdir = f"{PRODUCTDIR}/{PACKAGE}_{type_}"
        Path(outdir).mkdir(parents=True, exist_ok=True)

        # process each non-hidden variable
        for var_name, var_data in var_config["variable"].items():
            if var_data.get("hidden", True):
                continue
            new_product = create_product(var_name, var_data, template, var_config, type_)
            outfile = f"{outdir}/{new_product['name']}-{type_}.json"
            print(outfile)
            write_layer(outfile, new_product)

if __name__ == "__main__":
    main()