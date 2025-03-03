import os

import graphviz

from directory_tree import DisplayTree
from PIL import Image, ImageFont, ImageDraw

dir_path = os.path.dirname(os.path.realpath(__file__))

# TODO license table?

dot = graphviz.Digraph()
dot.attr('node', shape='none')
table_html = open(f"{dir_path}/licenses.html", "r").read()
dot.node('table', label=table_html)
dot.render(f"{dir_path}/licenses", format='png', cleanup=True)
# dot.render(f"{dir_path}/licenses.gv")

# TODO storage option table?

dot = graphviz.Digraph()
dot.attr('node', shape='none')
table_html = open(f"{dir_path}/storage_options.html", "r").read()
dot.node('table', label=table_html)
dot.render(f"{dir_path}/storage_options", format='png', cleanup=True)
# dot.render(f"{dir_path}/storage_options.gv")

# TODO broken experimental workflow

# TODO better experimental workflow

# upload workflow

dot = graphviz.Digraph(comment="Experiment Archive Upload Workflow")
dot.node("1", "environment")
dot.node("2", "code")
dot.node("3", "data")
dot.node("4", "figures")
dot.node("5", "Package as reproducible artifact")
dot.node("6", "Upload to archive")

dot.edges(["15", "25", "35", "45", "56"])

dot.render(f"{dir_path}/upload.gv")


# usage workflow
dot = graphviz.Digraph(comment="Experiment Archive Upload Workflow")
dot.node("1", "install container runtime and git")
dot.node("2", "clone repo")
dot.node("3", "Run Containerfile")

dot.node("4", "Generate static plots")
dot.node("5", "Generate interactive plots")
dot.node("6", "Launch jupyter notebook")
dot.node("7", "Launch iPython kernel")

dot.edges(["12", "23", "34", "35", "36", "37"])

dot.render(f"{dir_path}/usage.gv")

ascii_files = DisplayTree(
    ".",
    stringRep=True,
    ignoreList=[
        "watch_calibration",
        "watch_calibration.egg-info",
        "*.wav",
        "build",
    ]
)

print(ascii_files)

# Create a new Image
# make sure the dimensions (W and H) are big enough for the ascii art
W, H = (400,950)
im = Image.new("RGBA",(W,H),"white")

font = ImageFont.truetype(f"{dir_path}/SourceCodePro-Regular.otf", 20)

# Draw text to image
draw = ImageDraw.Draw(im)
# w, h = draw.textsize(ascii_files)
# draws the text in the center of the image
# draw.text(((W-w)/2,(H-h)/2), ascii_text, fill="black")
draw.multiline_text((10, 10), ascii_files, font=font, fill=(0,0,0))

# Save Image
im.save(f"{dir_path}/file_structure.png", "PNG")
