"""
################################################################################
Function: resource_utils.py
Purpose: Utility functions for creating and managing all resources (products, 
         layers, and styles).
Authors: Sebastian Steinig
Version History:
    - 1.0 (2024-02): Initial creation of the function.
################################################################################
"""

import copy
from file_utils import generate_short_names

def create_package(package_name, package_data, template):
    """Create a new package definition file."""
    new_package = copy.deepcopy(template)
    
    # Update package metadata
    new_package.update({
        "name": package_name,
        "title": package_data["title"],
        "description": package_data["description"]
    })

    return new_package

def create_models_variable(var_config):
    """Create the models variable definition."""
    model_values = []
    model_labels = []

    # Add ensemble model first
    model_label = var_config["model"]["ensemble"]["form_label"]
    oc = var_config["model"]["ensemble"]["grib_representations"][0]
    model_values.append(f"{oc['centre']}_{oc['subCentre']}")
    model_labels.append(model_label)

    # Add other models
    for model in sorted(var_config["model"]):
        if model != "ensemble":
            model_label = var_config["model"][model]["form_label"]
            oc = var_config["model"][model]["grib_representations"][0]
            model_labels.append(model_label)
            model_values.append(f"{oc['centre']}_{oc['subCentre']}")

    return {
        "name": "originating_centre",
        "title": "Model",
        "type": "choice",
        "values": model_values,
        "labels": model_labels
    }

def create_single_product(var_name, var_data, template, var_config, type_='web'):
    """Create a new product definition for a single parameter."""
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
            "style": f"sh_{short_name}_{type_}_surface_concentration"
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
        "package": "cams_air_quality",
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

def create_grouped_product(group_name, group_data, template, var_config, type_='web'):
    """Create a new product definition for a group of parameters."""
    new_product = copy.deepcopy(template)
    
    # Get first variable to use as reference for layer name and style
    first_var = group_data["variables"][0]
    var_data = var_config["variable"][first_var]
    short_name, _ = generate_short_names(var_data["backend_api_name"])
    layer_name = f"composition_europe_{short_name}_forecast_surface"

    # Set layers
    new_product["layers"] = [
        {
            "class": "data",
            "layer_type": "eccharts",
            "name": layer_name,
            "style": f"sh_{short_name}_{type_}_surface_concentration"
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
        "name": f"europe-{group_name}-forecast",
        "title": f"European air quality {group_data['title']} forecast",
        "package": "cams_air_quality",
        "description": f"CAMS European {group_data['title']} forecast",
        "click_features": {
            "options": [{
                "product": f"plume_cams_eu_{first_var}",
                "title": f"Ground-level {group_data['title']} concentrations"
            }],
            "products": [f"plume_cams_eu_{first_var}"],
            "tooltip": f"Ground-level {group_data['title']} concentrations"
        }
    })

    # Add models variable
    new_product["variables"].append(create_models_variable(var_config))

    return new_product

def create_layer(var_name, var_data, template, var_config):
    """Create a new layer definition for a given parameter."""
    # get variable details and handle some special cases
    unit = var_data["var_table_units"].split("netCDF:")[-1].replace("<sup>", "").replace("</sup>", "") if "netCDF:" in var_data["var_table_units"] else var_data["var_table_units"].replace("<sup>", "").replace("</sup>", "")
    short_name, short_name_with_spaces = generate_short_names(var_data["backend_api_name"])
    long_name = f"PM{var_name.split('_')[-1][:-2]}" if var_name.startswith("particulate") else var_name.replace("_", " ")

    # create list of styles based on variable name
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
    new_layer["variables"].append(create_models_variable(var_config))
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

def create_style(parameter, backend_api_name, style_config, template, type_='web'):
    """Create a new style definition for a given parameter."""
    short_name, short_name_with_spaces = generate_short_names(backend_api_name)
    
    # get contour settings
    contour_list = style_config[type_]["contour_levels"][parameter]
    contour_level_list = "/".join([str(l) for l in contour_list])
    contour_min = contour_list[0]
    contour_max = contour_list[-1]
    
    # Determine colours based on the presence of "common" attribute
    if "common" in style_config[type_]["colours"]:
        contour_shade_colour_list = "/".join(style_config[type_]["colours"]["common"])
    else:
        cols = style_config[type_]["colours"][parameter]
        contour_shade_colour_list = "/".join(cols)

    new_style = copy.deepcopy(template)
    
    # update style with parameter details
    title = f"Contour shade (Range: {contour_min:.0f} / {contour_max:.0f}, Multihue {short_name} {type_})"
    new_style.update({
        "title": title,
        "name": f"sh_{short_name}_{type_}_surface_concentration",
        "description": f"Method: contour shade\r\nLevel range : {contour_min:.0f} to {contour_max:.0f}\r\nColour    : Multihue {short_name} {type_}"
    })

    # update contour settings
    new_style["data"]["contour"].update({
        "contour_legend_text": title,
        "contour_level_list": contour_level_list,
        "contour_shade_colour_list": contour_shade_colour_list,
        "contour_shade_min_level": contour_min
    })

    return new_style 