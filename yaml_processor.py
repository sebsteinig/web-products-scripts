import yaml


def load_yaml_config(file_path):
    """Load the YAML configuration from a file."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def apply_defaults(package):
    """Apply parent properties to children and check for local overwrites."""
    parent_properties = {key: package[key] for key in package if key != "products"}

    for product_type, product_details in package["products"].items():
        for product_name, product_info in product_details.items():
            # Debugging: Print the product_info to check its structure
            # print(f"Processing {product_name} in {product_type}: {product_info}")

            # Ensure product_info is a dictionary
            if not isinstance(product_info, dict):
                print(
                    f"Warning: {product_name} in {product_type} is not a dictionary. Skipping."
                )
                continue

            # Create a merged properties dictionary
            merged_properties = parent_properties.copy()

            # Check if 'variables' is present and handle it accordingly
            if "variables" in product_info:
                # If 'variables' is a list, we can keep it as is
                merged_properties["variables"] = product_info["variables"]
            else:
                # If 'variables' is not present, we can add an empty list or handle it as needed
                merged_properties["variables"] = []

            # Update with any other properties from product_info
            merged_properties.update(product_info)

            # Update the product with merged properties
            package["products"][product_type][product_name] = merged_properties


def process_yaml_config(config):
    """Process the entire YAML configuration."""
    for package_name, package_data in config["packages"].items():
        apply_defaults(package_data)
    return config
