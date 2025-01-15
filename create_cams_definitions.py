#! /usr/bin/env python
"""
################################################################################
Function: create_cams_definitions.py
Purpose: Master script to create packages, products, layers and styles in a 
         top-down approach based on package configurations.
Authors: Sebastian Steinig
Version History:
    - 1.0 (2024-02): Initial creation of the function.
################################################################################
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from file_utils import load_config, load_template, write_layer, generate_short_names
from summary_utils import create_summary
from resource_utils import (
    create_package,
    create_single_product,
    create_grouped_product,
    create_layer,
    create_style
)

################################################################################
# user-defined variables from .env file
load_dotenv()

OUTPUTDIR = os.getenv("OUTPUTDIR")  # Base output directory
PACKAGEDIR = os.path.join(OUTPUTDIR, "package")  # Derived from OUTPUTDIR
PRODUCTDIR = os.path.join(OUTPUTDIR, "product")  # Derived from OUTPUTDIR
LAYERDIR = os.path.join(OUTPUTDIR, "layer")  # Derived from OUTPUTDIR
STYLEDIR = os.path.join(OUTPUTDIR, "style")  # Derived from OUTPUTDIR
BITBUCKET_TOKEN = os.getenv("BITBUCKET_TOKEN")
BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME")

# Configuration files
PACKAGE_CONFIG = "./etc/packages.yaml"
VAR_CONFIG_FILE = "https://git.ecmwf.int/projects/CDS/repos/cads-forms-cams/raw/cams-europe-air-quality-forecasts/regional_fc_definitions.yaml?at=refs%2Fheads%2Fprod"
STYLE_CONFIG_FILE = "https://raw.githubusercontent.com/CopernicusAtmosphere/air-quality-plot-settings/refs/heads/main/plot_settings.yaml"

def process_package(package_name, package_data, templates, configs, type_='web'):
    """Process a single package and create all necessary products, layers, and styles."""
    print(f"\nProcessing package: {package_name}")
    
    # Initialize summary for this package
    package_summary = {
        'title': package_data['title'],
        'products': {}
    }
    
    # Create package file
    new_package = create_package(package_name, package_data, templates["package"])
    outfile = f"{PACKAGEDIR}/{package_name}.json"
    print(f"Creating package: {outfile}")
    write_layer(outfile, new_package)
    
    # Create package directory for products
    package_dir = f"{PRODUCTDIR}/{package_name}_{type_}"
    Path(package_dir).mkdir(parents=True, exist_ok=True)

    # Track all required layers and styles (using a set to avoid duplicates)
    required_layers = set()
    required_styles = set()

    # Process single products
    for group in package_data["products"]["single"]:
        for var_name in group["variables"]:
            var_data = configs["var_config"]["variable"][var_name]
            
            # Create product
            new_product = create_single_product(var_name, var_data, templates["product"], configs["var_config"], type_)
            outfile = f"{package_dir}/{new_product['name']}-{type_}.json"
            print(f"Creating product: {outfile}")
            write_layer(outfile, new_product)

            # Track required layer and style
            short_name, _ = generate_short_names(var_data["backend_api_name"])
            layer_name = f"composition_europe_{short_name}_forecast_surface"
            style_name = f"sh_{short_name}_{type_}_surface_concentration"
            required_layers.add(layer_name)
            required_styles.add(style_name)

            # Add to summary
            package_summary['products'][new_product['name']] = {
                'type': 'single',
                'layers': [layer_name],
                'styles': [style_name]
            }

    # Process grouped products
    for group_name, group_data in package_data["products"]["grouped"].items():
        # Create product
        new_product = create_grouped_product(group_name, group_data, templates["product"], configs["var_config"], type_)
        outfile = f"{package_dir}/{new_product['name']}-{type_}.json"
        print(f"Creating product: {outfile}")
        write_layer(outfile, new_product)

        # Track required layers and styles for all variables in group
        group_layers = []
        group_styles = []
        for var_name in group_data["variables"]:
            var_data = configs["var_config"]["variable"][var_name]
            short_name, _ = generate_short_names(var_data["backend_api_name"])
            layer_name = f"composition_europe_{short_name}_forecast_surface"
            style_name = f"sh_{short_name}_{type_}_surface_concentration"
            required_layers.add(layer_name)
            required_styles.add(style_name)
            group_layers.append(layer_name)
            group_styles.append(style_name)

        # Add to summary
        package_summary['products'][new_product['name']] = {
            'type': 'grouped',
            'layers': group_layers,
            'styles': group_styles
        }

    # Create required layers
    print("\nCreating required layers...")
    for var_name in configs["var_config"]["variable"]:
        var_data = configs["var_config"]["variable"][var_name]
        short_name, _ = generate_short_names(var_data["backend_api_name"])
        layer_name = f"composition_europe_{short_name}_forecast_surface"
        
        if layer_name in required_layers:
            new_layer = create_layer(var_name, var_data, templates["layer"], configs["var_config"])
            outfile = f"{LAYERDIR}/{layer_name}.json"
            print(f"Creating layer: {outfile}")
            write_layer(outfile, new_layer)

    # Create required styles
    print("\nCreating required styles...")
    for var_name in configs["var_config"]["variable"]:
        var_data = configs["var_config"]["variable"][var_name]
        short_name, _ = generate_short_names(var_data["backend_api_name"])
        style_name = f"sh_{short_name}_{type_}_surface_concentration"
        
        if style_name in required_styles:
            new_style = create_style(var_name, var_data["backend_api_name"], configs["style_config"], templates["style"], type_)
            outfile = f"{STYLEDIR}/{style_name}.json"
            print(f"Creating style: {outfile}")
            write_layer(outfile, new_style)

    return package_summary

def main():
    # Load configurations
    configs = {
        "package_config": load_config(PACKAGE_CONFIG),
        "var_config": load_config(VAR_CONFIG_FILE),
        "style_config": load_config(STYLE_CONFIG_FILE)
    }

    # Convert var_config into a dictionary for easier access
    configs["var_config"] = {key: {item["frontend_api_name"]: item for item in configs["var_config"][key]} for key in ["model", "variable"]}

    # Load templates
    templates = {
        "package": load_template("./etc/package_template.json"),
        "product": load_template("./etc/product_template.json"),
        "layer": load_template("./etc/layer_template.json"),
        "style": load_template("./etc/style_template.json")
    }

    # Create output directories if they don't exist
    for dir_ in [LAYERDIR, STYLEDIR, PRODUCTDIR, PACKAGEDIR]:
        if Path(dir_).exists():
            shutil.rmtree(dir_)
        Path(dir_).mkdir(parents=True, exist_ok=True)

    # Process each package and collect summaries
    package_summaries = {}
    for package_name, package_data in configs["package_config"]["packages"].items():
        # for type_ in ["web", "eea"]:
        for type_ in ["web"]:
            package_summaries[package_name] = process_package(package_name, package_data, templates, configs, type_)

    # Create summaries and visualizations
    create_summary(package_summaries, OUTPUTDIR)

if __name__ == "__main__":
    main() 