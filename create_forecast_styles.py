import copy
import os
from pathlib import Path
from dotenv import load_dotenv

from utils import load_config, load_template, write_layer, generate_short_names

# user-defined variables from .env file
load_dotenv()

STYLEDIR = os.getenv('STYLEDIR') # output directory
VAR_CONFIG_FILE = "https://git.ecmwf.int/projects/CDS/repos/cads-forms-cams/raw/cams-europe-air-quality-forecasts/regional_fc_definitions.yaml?at=refs%2Fheads%2Fprod"  # either local or URL
STYLE_CONFIG_FILE = "https://raw.githubusercontent.com/CopernicusAtmosphere/air-quality-plot-settings/refs/heads/main/plot_settings.yaml"  # URL or path to plot_settings.yaml
BITBUCKET_TOKEN = os.getenv("BITBUCKET_TOKEN")  # for access to CONFIG in private Bitbucket repo
BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME")
TYPES = ['web', 'eea'] # keywords as defined in STYLE_CONFIG_FILE

# Create output directory if it doesn't exist
Path(STYLEDIR).mkdir(parents=True, exist_ok=True)

def create_style(parameter, backend_api_name, style_config, template, type_='eea'):
    """create a new style definition for a given parameter."""
    new_style = copy.deepcopy(template)
    
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

def get_backend_api_name(frontend_name, var_config):
    """Get backend API name from frontend name in variable config."""
    for var in var_config["variable"]:
        if var["frontend_api_name"] == frontend_name:
            return var["backend_api_name"]
    return None

def main():
    # load configurations
    style_config = load_config(STYLE_CONFIG_FILE)
    var_config = load_config(VAR_CONFIG_FILE)
    template = load_template("./etc/style_template.json")

    # loop through each style type
    for type_ in TYPES:
        print(f"\nProcessing style type: {type_}")
        
        # skip if type doesn't exist in config
        if type_ not in style_config:
            print(f"Warning: Style type '{type_}' not found in configuration. Skipping...")
            continue

        # process each parameter in contour levels for current type
        for parameter in style_config[type_]["contour_levels"]:
            backend_api_name = get_backend_api_name(parameter, var_config)
            if backend_api_name is None:
                print(f"Warning: No backend API name found for frontend name: {parameter}. Skipping...")
                continue

            new_style = create_style(parameter, backend_api_name, style_config, template, type_)
            
            outfile = f'{STYLEDIR}/{new_style["name"]}.json'   
            print(f"Creating style: {outfile}")
            write_layer(outfile, new_style)

if __name__ == "__main__":
    main() 
