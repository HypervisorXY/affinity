import pathlib
import svgelements
import base64
import json

# this script uses the python library svgelements to parse the svg 
# files for width/height info. please ensure it is installed 
# if you receive errors about svgelements when running the script. 
# see https://pypi.org/project/svgelements/

# *** BEGIN CONFIGURABLE SETTINGS ***

folder_svg = pathlib.Path.cwd() / "svg"
folder_output =  pathlib.Path.cwd() / "draw.io_libraries"

# set to True to exclude subvariant from title name in library. 
# ex: if library is circle_blue then title will not include blue
# in the title's name. instead of "camera blue", the title will just
# be "camera"
title_hide_subvariant = True

# set to True to remove first characters from filename when 
# generating titles of images for generated library see next variable
# title_substitutions for more details or to add new types
title_cleanup = True

# dict of style and the sequence of letters to
# remove or replace from title when title_cleanup is True. 
# To replace instead of just remove, include the replacement
# text as the second item in a tuple. ex "circle": ("c_", "circle ") 
# will replace "c_" with "circle "
title_substitutions = {"circle": "c_", "square": "sq_"}

# *** END CONFIGURABLE SETTINGS ***

# convenience class used to track individual style and subvariant 
# and generate name based on style (and subvariant if it exists)
class Style:
    def __init__(self, sty: str, subv=None):
        self.style = sty
        self.subvariant = subv
    def name(self) -> str:
        return f"{self.style}{'_' + self.subvariant if self.subvariant else ''}"


def convert_svg(svg_path: pathlib.Path, style: Style) -> dict:
    # svgelements object used for parsing svg image currently just for 
    # the width/height but possible to use for additional features
    svg = svgelements.SVG().parse(svg_path)
    svg_text = svg_path.read_text()

    # trim off beginning of document until reacing first "<svg" tag, 
    # trim any final newline in file, and replace newlines with &#xa;
    svg_text = svg_text[svg_text.index("<svg"):].rstrip("\n").replace("\n", "&#xa;")
    
    #base64 encoded string of svg used in library file
    b64str = str(base64.b64encode(svg_text.encode("ascii")), "ascii")

    title = svg_path.stem
    
    #if there is a subvariant and hide subvariant is enabled remove it from the title
    if style.subvariant and title_hide_subvariant:
        title = title.replace(style.subvariant, "", 1)
    
    #if cleanup enabled perform substitution when style in list of substitution keys
    if title_cleanup:
        if style.style in title_substitutions.keys():
            # if title_substitutions is tuple use second element for 
            # replacement instead of just removal. always only replaces first occurrence
            if isinstance(title_substitutions[style.style], tuple):
                title = title.replace(title_substitutions[style.style][0], title_substitutions[style.style][1], 1)
            else:
                title = title.replace(title_substitutions[style.style], "", 1)
    # replace underscore with space and trim any whitespace from title
    title = title.replace("_", " ").strip()

    # preserveAspectRatio could be pulled from svgelements object 
    # if needed, but instead it is currently always set to fixed
    return {"data": f"data:image/svg+xml;base64,{b64str}",
    "w": svg.width, 
    "h": svg.height, 
    "title": title, 
    "aspect": "fixed"}

def write_library(image_json: list, library_name: str):
    library_file = folder_output / f"{library_name}.xml"
    library_file.write_text(f"<mxlibrary>{json.dumps(image_json)}</mxlibrary>")

#takes path of folder containing all svg files, writes out template xml file
def generate_template(svg_path: pathlib.Path, style: Style):
    #add all svg files inside folder to template
    #list of images to use for libray creation
    print(f"Generating library for {style.name()}")
    images = []
    for svg in svg_path.glob("*.svg"):
        images.append(convert_svg(svg, style))
    write_library(images, style.name())    

# create output folder if not exist
folder_output.mkdir(exist_ok=True)

# loop through "svg_folder" find all styles/subvariants
# example of style folder is circle, example of subvariant 
# folder is blue folder inside circle folder
styles = [f for f in folder_svg.iterdir() if f.is_dir()]
for style_folder in styles:
    subvariants = [f for f in style_folder.iterdir() if f.is_dir()]
    if not subvariants:
        # no subfolders inside the style folder
        generate_template(style_folder, Style(style_folder.name))
    else:
        # assuming each subfolder inside the style's folder is a subvariant 
        # ex: red, blue, etc of current style 
        for subvariant in subvariants:
            generate_template(subvariant, Style(style_folder.name, subvariant.name))

print("Finished")
