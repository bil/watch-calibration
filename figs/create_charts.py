import os

import graphviz

from directory_tree import DisplayTree
from PIL import Image, ImageFont, ImageDraw

dir_path = os.path.dirname(os.path.realpath(__file__))


def create_table(title, html_file, out_file):
    dot = graphviz.Digraph()
    dot.attr(label=title, labelloc="t")
    dot.attr("node", shape="none")
    # https://www.graphviz.org/doc/info/shapes.html
    table_html = open(html_file, "r").read()
    dot.node("table", label=table_html)
    dot.render(out_file, format="png", cleanup=True)
    dot.render(out_file, format="svg", cleanup=True)


# license table
create_table(
    "Open-source License Comparison",
    f"{dir_path}/licenses.html",
    f"{dir_path}/licenses"
)


# storage options table
create_table(
    "Accessible, Persistent, Trusted Archive Comparison",
    f"{dir_path}/storage_options.html",
    f"{dir_path}/storage_options"
)


# minimal file structure
def create_ascii_file_chart(
    filepath=".", outfile=f"{dir_path}/file_structure.svg", ignoreList=None
):

    if ignoreList is None:
        ignoreList = [
            "raw_data",
            "deriv_data",
            "watch_calibration.egg-info",
            "*.wav",
            "build",
        ]

    ascii_files = DisplayTree(
        filepath,
        stringRep=True,
        ignoreList=ignoreList
    )

    # draw ascii_files text to image using Pillow
    # make sure the dimensions (W and H) are big enough for the ascii art
    W, H = (400,25*ascii_files.count('\n'))
    im = Image.new("RGBA",(W,H),"white")
    font = ImageFont.truetype(f"{dir_path}/SourceCodePro-Regular.otf", 20)
    draw = ImageDraw.Draw(im)
    draw.multiline_text((10, 10), ascii_files, font=font, fill=(0,0,0))

    # save image
    im.save(outfile, "png")


create_ascii_file_chart(
    filepath=f"{dir_path}/arts-minimal-file-structure",
    outfile=f"{dir_path}/file_structure_minimal.svg",
    ignoreList=[]
)
