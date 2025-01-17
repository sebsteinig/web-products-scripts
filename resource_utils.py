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
from file_utils import (
    generate_short_names,
    generate_long_name,
    generate_layer_name,
    load_template,
    write_layer,
)

# Load templates used in this module
_PACKAGE_TEMPLATE = load_template("./etc/package_template.json")
_PRODUCT_TEMPLATE = load_template("./etc/product_template.json")
_LAYER_TEMPLATE = load_template("./etc/layer_template.json")
_STYLE_TEMPLATE = load_template("./etc/style_template.json")


def create_package(package_name, package_data):
    """Create a new package definition file."""
    new_package = copy.deepcopy(_PACKAGE_TEMPLATE)

    # Update package metadata
    new_package.update(
        {
            "name": package_name,
            "title": package_data["base_title"],
            "description": package_data["description"],
        }
    )

    return new_package


def create_click_features(var_list, var_config, suffix):
    if len(var_list) == 1:
        # For single variable products
        var_name = var_list[0]
        var_data = var_config["variable"].get(var_name)
        if var_data is None:
            raise ValueError(f"No variable metadata found for '{var_name}'.")

        long_name = generate_long_name(var_name)

        return {
            "feature": "cams_plumes",
            "options": [
                {
                    "product": f"plume_cams_eu_{var_name}{suffix.replace('-', '_')}",
                    "title": f"Ground-level {long_name} concentrations",
                }
            ],
            "tooltip": f"Click on the map to see the graph of forecasted ground-level {long_name} concentrations for that location",
        }
    else:
        # For grouped products with multiple variables
        options = []
        for var_name in var_list:
            var_data = var_config["variable"].get(var_name)
            if var_data is None:
                raise ValueError(f"No variable metadata found for '{var_name}'.")

            short_name, _ = generate_short_names(var_data["backend_api_name"])
            long_name = generate_long_name(var_name)

            layer_name = generate_layer_name(
                "composition_europe", short_name, "forecast", "surface", suffix
            )

            options.append(
                {
                    "key": "layer_name",
                    "product": f"plume_cams_eu_{var_name}{suffix}",
                    "title": f"Ground-level {long_name} concentrations",
                    "value": layer_name,
                }
            )

        return {
            "feature": "cams_plumes",
            "options": options,
            "tooltip": "Click to generate a plume plot",
        }


def create_layer_name_variable(var_list, var_config, suffix):
    labels = []
    values = []

    for var_name in var_list:
        label = var_name.replace("_", " ").title()
        labels.append(label)

        var_data = var_config["variable"].get(var_name)
        short_name, _ = generate_short_names(var_data["backend_api_name"])
        layer_name = generate_layer_name(
            "composition_europe", short_name, "forecast", "surface", suffix
        )
        values.append(layer_name)

    return {
        "name": "layer_name",
        "title": "Parameter",
        "type": "choice",
        "labels": labels,
        "values": values,
    }


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
        "labels": model_labels,
    }


def create_height_variable(levels):
    """Create height level variable configuration for a product."""
    if levels == "surface" or levels == ["surface"]:
        return None

    if isinstance(levels, str):
        levels = [levels]

    # Create mapping for labels
    label_mapping = {
        "surface": "Surface",
        "100m": "100 m",
        "1000m": "1000 m",
        "3000m": "3000 m",
        "5000m": "5000 m",
    }

    # Create mapping for values
    value_mapping = {
        "surface": "key_0",
        "100m": "key_100",
        "1000m": "key_1000",
        "3000m": "key_3000",
        "5000m": "key_5000",
    }

    return {
        "name": "level",
        "title": "Height level",
        "type": "choice",
        "labels": [label_mapping[level] for level in levels],
        "values": [value_mapping[level] for level in levels],
    }


def create_product(
    input_vars, var_config, package_dir, package_data, type, group_name=""
):
    """Create a new product definition file."""

    # check the type of product we are creating
    suffix = "-eea" if package_data["flag"] == "eea" else ""

    if isinstance(input_vars, str):
        # single product
        var_list = [input_vars]
        product_type = "single"
        product_name = f"{package_data['base_name']}-{input_vars}-{type}{suffix}"
        product_title = f"{package_data['base_title']} {generate_long_name(input_vars)} {type.replace('-', ' ')}"
    elif isinstance(input_vars, list) and len(input_vars) > 1:
        # grouped product
        var_list = input_vars
        product_type = "grouped"
        product_name = f"{package_data['base_name']}-{type}-{group_name}{suffix}"
        product_title = f"{package_data['base_title']} {type.replace('-', ' ')} of {package_data['title']}"
    else:
        raise ValueError("Invalid input variable formatfor product creation.")

    new_product = copy.deepcopy(_PRODUCT_TEMPLATE)

    # update global metadata first
    new_product.update(
        {
            "name": product_name,
            "title": product_title,
            "package": f"{package_data['package_name']}",
            "description": f"{package_data['description']}",
        }
    )

    # add click_features for plume plots
    new_product["click_features"] = create_click_features(var_list, var_config, suffix)

    if product_type == "grouped":
        new_product["variables"].append(
            create_layer_name_variable(var_list, var_config, suffix)
        )

    if package_data["flag"] == "web":
        # add model selection variable
        new_product["variables"].append(create_models_variable(var_config))
        # add height selection variable
        new_product["variables"].append(create_height_variable(package_data["levels"]))

    # # add metadata for each variable
    # for var_name in var_list:
    #     print(var_name)
    #     var_data = var_config["variable"].get(var_name)
    #     if var_data is None:
    #         raise ValueError(f"No variable metadata found for '{var_name}'.")

    #     short_name, _ = generate_short_names(var_data["backend_api_name"])
    #     long_name = (
    #         f"PM{var_name.split('_')[-1][:-2]}"
    #         if var_name.startswith("particulate")
    #         else var_name.replace("_", " ")
    #     )

    # layer_name = f"composition_europe_{short_name}_forecast_surface"

    #     new_product["layers"] = [
    #         {
    #             "class": "data",
    #             "layer_type": "eccharts",
    #             "name": layer_name,
    #             "style": f"sh_{short_name}_{type_}_surface_concentration",
    #         },
    #         {
    #             "class": "data",
    #             "layer_type": "eccharts",
    #             "name": "foreground",
    #             "style": "medium_res_foreground",
    #         },
    #         {"class": "data", "layer_type": "eccharts", "name": "grid"},
    #         {
    #             "class": "data",
    #             "layer_type": "eccharts",
    #             "name": "boundaries",
    #             "style": "black_boundaries",
    #         },
    #     ]

    #     "click_features": {
    #     "options": [
    #         {
    #             "product": f"plume_cams_eu_{var_name}",
    #             "title": f"Ground-level {long_name} concentrations",
    #         }
    #     ],
    #     "products": [f"plume_cams_eu_{var_name}"],
    # },

    outfile = f"{package_dir}/{new_product['name']}.json"
    print(f"Creating product: {outfile}")
    write_layer(outfile, new_product)
    # return new_product


def create_layer(var_name, var_config):
    """Create a new layer definition for a given parameter."""
    var_data = var_config["variable"].get(var_name)
    if var_data is None:
        raise ValueError(f"No variable metadata found for '{var_name}'.")

    # get variable details and handle some special cases
    unit = (
        var_data["var_table_units"]
        .split("netCDF:")[-1]
        .replace("<sup>", "")
        .replace("</sup>", "")
        if "netCDF:" in var_data["var_table_units"]
        else var_data["var_table_units"].replace("<sup>", "").replace("</sup>", "")
    )
    short_name, short_name_with_spaces = generate_short_names(
        var_data["backend_api_name"]
    )
    long_name = (
        f"PM{var_name.split('_')[-1][:-2]}"
        if var_name.startswith("particulate")
        else var_name.replace("_", " ")
    )

    # create list of styles based on variable name
    AQI_PARAMS = [
        "nitrogen_dioxide",
        "ozone",
        "particulate_matter_2p5um",
        "particulate_matter_10um",
        "sulphur_dioxide",
    ]
    style = f"sh_{short_name}_web_surface_concentration"
    style_list = [style]
    if var_name in AQI_PARAMS:
        style_list.append(f"sh_{short_name}_aqi_surface_concentration")
    style_list.extend(
        [
            "sh_Reds_surface_concentration",
            "sh_Purples_surface_concentration",
            "sh_Greens_surface_concentration",
            "sh_Oranges_surface_concentration",
        ]
    )

    new_layer = copy.deepcopy(_LAYER_TEMPLATE)

    # update layer with variable details
    new_layer.update(
        {
            "description": f"European {long_name} ground- and upper-level forecast",
            "keywords": f"deterministic, air quality, {short_name_with_spaces}, {long_name}, surface concentrations",
            "name": f"composition_europe_{short_name}_forecast_surface",
            "title": f"Ground- and upper-level {long_name} (provided by CAMS)",
            "style": f"sh_{short_name}_web_surface_concentration",
            "styles": style_list,
            "units": {"data": unit, "display": unit},
        }
    )

    constituent_type = var_data["grib_representations"][-1]["constituentType"]
    new_layer["retrieve"]["data"].update(
        {"constituentType": f"key_{constituent_type}", "expver": "5001"}
    )

    # add list of models layer and stream definitions
    new_layer["variables"].append(create_models_variable(var_config))
    new_layer["variables"].append(
        {
            "name": "stream",
            "title": "Statistics type",
            "type": "choice",
            "menu": "true",
            "values": ["oper", "dame", "damx"],
        }
    )
    new_layer["variables"].append(
        {
            "name": "type",
            "title": "Data type",
            "type": "choice",
            "menu": "true",
            "values": ["fc", "an"],
        }
    )
    new_layer["variables"].append(
        {
            "name": "level",
            "title": "Height level",
            "type": "choice",
            "menu": "true",
            "values": ["key_0", "key_100", "key_1000", "key_3000", "key_5000"],
        }
    )

    return new_layer


def create_style(var_name, style_config, type_="web"):
    """Create a new style definition for a given parameter."""
    # Get backend_api_name from var_name
    var_data = style_config["variable"].get(var_name)
    if var_data is None:
        raise ValueError(f"No variable metadata found for '{var_name}'.")

    short_name, short_name_with_spaces = generate_short_names(
        var_data["backend_api_name"]
    )

    # get contour settings
    contour_list = style_config[type_]["contour_levels"][var_name]
    contour_level_list = "/".join([str(l) for l in contour_list])
    contour_min = contour_list[0]
    contour_max = contour_list[-1]

    # Determine colours based on the presence of "common" attribute
    if "common" in style_config[type_]["colours"]:
        contour_shade_colour_list = "/".join(style_config[type_]["colours"]["common"])
    else:
        cols = style_config[type_]["colours"][var_name]
        contour_shade_colour_list = "/".join(cols)

    new_style = copy.deepcopy(_STYLE_TEMPLATE)

    # update style with parameter details
    title = f"Contour shade (Range: {contour_min:.0f} / {contour_max:.0f}, Multihue {short_name} {type_})"
    new_style.update(
        {
            "title": title,
            "name": f"sh_{short_name}_{type_}_surface_concentration",
            "description": f"Method: contour shade\r\nLevel range : {contour_min:.0f} to {contour_max:.0f}\r\nColour    : Multihue {short_name} {type_}",
        }
    )

    # update contour settings
    new_style["data"]["contour"].update(
        {
            "contour_legend_text": title,
            "contour_level_list": contour_level_list,
            "contour_shade_colour_list": contour_shade_colour_list,
            "contour_shade_min_level": contour_min,
        }
    )

    return new_style
