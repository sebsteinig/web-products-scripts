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
import sys
from pathlib import Path
from dotenv import load_dotenv
from file_utils import load_config, write_layer, generate_short_names
from summary_utils import create_summary
from resource_utils import (
    create_package,
    create_product,
    create_single_product,
    create_grouped_product,
    create_layer,
    create_style,
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
PACKAGE_CONFIG = "./etc/cams_packages.yaml"
VAR_CONFIG_FILE = "https://git.ecmwf.int/projects/CDS/repos/cads-forms-cams/raw/cams-europe-air-quality-forecasts/regional_fc_definitions.yaml?at=refs%2Fheads%2Fprod"
STYLE_CONFIG_FILE = "https://raw.githubusercontent.com/CopernicusAtmosphere/air-quality-plot-settings/refs/heads/main/plot_settings.yaml"


def process_package(package_name, package_data, configs):
    """Process a single package and create all necessary products, layers, and styles."""
    print(f"\nProcessing package: {package_name}")

    # Initialize summary for this package
    package_summary = {"title": package_data["title"], "products": {}}

    # Create package definition file
    new_package = create_package(package_name, package_data)
    outfile = f"{PACKAGEDIR}/{package_name}.json"
    print(f"Creating package: {outfile}")
    write_layer(outfile, new_package)

    # Create subdirectory for products
    package_dir = (
        f"{PRODUCTDIR}/{package_name}_eea"
        if package_data["flag"] == "eea"
        else f"{PRODUCTDIR}/{package_name}"
    )
    Path(package_dir).mkdir(parents=True, exist_ok=True)

    # Track all required layers and styles (using a dictionary to avoid duplicates)
    required_layers = {}
    required_styles = {}

    # Process single products
    for var_name in package_data["products"]["single"]["variables"]:
        new_product = create_product(
            var_name,
            configs["var_config"],
            package_data["flag"],
        )
        outfile = f"{package_dir}/{new_product['name']}-{package_data['flag']}.json"
        print(f"Creating product: {outfile}")
        write_layer(outfile, new_product)

    # Process grouped products
    for group_name, group_data in package_data["products"]["grouped"].items():
        new_product = create_product(
            group_data["variables"],
            configs["var_config"],
            package_data["flag"],
        )
        outfile = f"{package_dir}/{new_product['name']}-{package_data['flag']}.json"
        print(f"Creating product: {outfile}")
        write_layer(outfile, new_product)

    sys.exit()

    # Process grouped products
    for group_name, group_data in package_data["products"]["grouped"].items():
        # Create product
        new_product = create_grouped_product(
            group_name,
            group_data,
            configs["var_config"],
            package_data["flag"],
        )
        outfile = f"{package_dir}/{new_product['name']}-{package_data['flag']}.json"
        print(f"Creating product: {outfile}")
        write_layer(outfile, new_product)

        # Track required layers and styles for all variables in group
        group_layers = []
        group_styles = []
        for var_name in group_data["variables"]:
            var_data = configs["var_config"]["variable"].get(var_name)
            if var_data is None:
                raise ValueError(
                    f"No variable data found for '{var_name}' in package '{package_name}'."
                )

            short_name, _ = generate_short_names(var_data["backend_api_name"])
            layer_name = f"composition_europe_{short_name}_forecast_surface"
            style_name = f"sh_{short_name}_{package_data['flag']}_surface_concentration"

            # Add to required_layers if not already present
            if layer_name not in required_layers:
                required_layers[layer_name] = var_name
                group_layers.append(layer_name)

            # Add to required_styles if not already present
            if style_name not in required_styles:
                required_styles[style_name] = var_name
                group_styles.append(style_name)

        # Add to summary
        package_summary["products"][new_product["name"]] = {
            "type": "grouped",
            "layers": group_layers,
            "styles": group_styles,
        }

    # Create required layers directly from required_layers
    print("\nCreating required layers...")
    for layer_name, var_name in required_layers.items():
        new_layer = create_layer(var_name, configs["var_config"])
        outfile = f"{LAYERDIR}/{layer_name}.json"
        print(f"Creating layer: {outfile}")
        write_layer(outfile, new_layer)

    # Create required styles directly from required_styles
    print("\nCreating required styles...")
    for style_name, var_name in required_styles.items():
        new_style = create_style(
            var_name,
            configs["style_config"],
            package_data["flag"],
        )
        outfile = f"{STYLEDIR}/{style_name}.json"
        print(f"Creating style: {outfile}")
        write_layer(outfile, new_style)

    return package_summary


def main():
    # Load configurations
    configs = {
        "package_config": load_config(PACKAGE_CONFIG),
        "var_config": load_config(VAR_CONFIG_FILE),
        "style_config": load_config(STYLE_CONFIG_FILE),
    }

    # Convert var_config into a dictionary for easier access
    configs["var_config"] = {
        key: {item["frontend_api_name"]: item for item in configs["var_config"][key]}
        for key in ["model", "variable"]
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
            package_summaries[package_name] = process_package(
                package_name, package_data, configs
            )

    # Create summaries and visualizations
    create_summary(package_summaries, OUTPUTDIR)


if __name__ == "__main__":
    main()
