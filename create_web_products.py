#! /usr/bin/env python
import copy
import json
from pathlib import Path
from dotenv import load_dotenv
import os

import aq_metadata

################################################################################
# user-defined variables from .env file
load_dotenv()

PACKAGE = "cams_air_quality"
PRODUCTDIR = os.getenv("PRODUCTDIR", f"/home/mod/git/web-products/catalogue/product/{PACKAGE}")
Path(PRODUCTDIR).mkdir(parents=True, exist_ok=True)

DEFAULT_STYLE = "web"
################################################################################

def create_areas_variable():
    """Create the areas variable definition."""
    return {
        "labels": [
            "Europe", "Central Europe", "North West Europe",
            "North East Europe", "South West Europe", "South East Europe"
        ],
        "name": "projection",
        "title": "Area",
        "type": "choice",
        "values": [
            "classical_europe", "cams_aq_central_europe",
            "cams_aq_nw_europe", "cams_aq_ne_europe",
            "cams_aq_sw_europe", "cams_aq_se_europe"
        ]
    }

def create_models_variable():
    """Create the models variable definition."""
    model_values = []
    model_labels = []

    # Add ensemble model first
    model_label = aq_metadata.config["model"]["ensemble"]["form_label"]
    oc = aq_metadata.config["model"]["ensemble"]["originating_centre"]
    model_values.append(oc)
    model_labels.append(model_label)

    # Add other models
    for model in sorted(aq_metadata.config["model"]):
        if model != "ensemble":
            model_label = aq_metadata.config["model"][model]["form_label"]
            oc = aq_metadata.config["model"][model]["originating_centre"]
            model_labels.append(model_label)
            model_values.append(oc)

    return {
        "name": "originating_centre",
        "title": "Model",
        "type": "choice",
        "values": model_values,
        "labels": model_labels
    }

def create_product(parameter, template):
    """Create a new product definition for a given parameter."""
    d = get_parameter_details(parameter)
    short_name = d["short_name"]
    short_name_underscores = d["short_name_underscores"]
    long_name = d["long_name"]

    new_product = copy.deepcopy(template)
    layer_name = f"composition_europe_{short_name_underscores}_forecast_surface"

    # Set layers
    new_product["layers"] = [
        {
            "class": "data",
            "layer_type": "eccharts",
            "name": layer_name,
            "style": f"sh_{short_name_underscores}_{DEFAULT_STYLE}_surface_concentration"
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
        "name": f"europe-{parameter}-forecast",
        "title": f"European air quality {long_name} forecast",
        "package": PACKAGE,
        "description": f"CAMS European {long_name} forecast",
        "click_features": {
            "options": [{
                "product": f"plume_cams_eu_{parameter}",
                "title": f"Ground-level {long_name} concentrations"
            }],
            "products": [f"plume_cams_eu_{parameter}"],
            "tooltip": f"Ground-level {long_name} concentrations"
        }
    })

    # Add variables
    new_product["variables"] = [
        create_areas_variable(),
        create_models_variable()
    ]

    return new_product

def main():
    # Load template
    with open("./etc/product_template.json") as f:
        template = json.loads(f.read())

    # Process each parameter
    for parameter in mapping:
        new_product = create_product(parameter, template)
        outfile = f"{PRODUCTDIR}/{new_product['name']}.json"
        print(outfile)
        
        with open(outfile, "w") as fo:
            json.dump(new_product, fo, sort_keys=True, indent=4)

if __name__ == "__main__":
    main()