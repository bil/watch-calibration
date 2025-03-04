import os

import graphviz

from directory_tree import DisplayTree
from PIL import Image, ImageFont, ImageDraw

dir_path = os.path.dirname(os.path.realpath(__file__))


def create_table(html_file, out_file):
    dot = graphviz.Digraph()
    dot.attr("node", shape="none")
    # https://www.graphviz.org/doc/info/shapes.html
    table_html = open(html_file, "r").read()
    dot.node("table", label=table_html)
    dot.render(out_file, format="png", cleanup=True)

# license table

create_table(
    f"{dir_path}/licenses.html",
    f"{dir_path}/licenses"
)

# storage options table

create_table(
    f"{dir_path}/storage_options.html",
    f"{dir_path}/storage_options"
)

# current experimental workflow

dot = graphviz.Digraph("Title", comment="current experimental workflow")
dot.attr(rankdir="LR")
dot.node("d1", "raw data")
dot.node("c1", "preprocessing code")
dot.node("d2", "derivative data")
dot.node("c2", "analysis code")
dot.node("f", "figures")

dot.edges([("d1","d2"), ("d2","f")])
dot.edge("c1", "d2", weight="0")
dot.edge("c2", "f", weight="0")

# with dot.subgraph(name="cluster A") as g:
#     g.attr(style="dotted", shape="circle")
#     g.node("c", shape="box")
#     g.node("c1", shape="box")
dot.render(f"{dir_path}/current_workflow", format="png", cleanup=True)


# updated experimental workflow

dot = graphviz.Digraph("Title", comment="updated experimental workflow")
# dot.attr(label=r"\G")
with dot.subgraph(name="cluster_local") as g:
    g.attr(label="local development environment", style="dotted")
    # g.node("A1", "Node A1", style="invis", shape="point")
    g.node("c0", "code", shape="box")
    g.node("d0", "data", shape="box")
with dot.subgraph(name="cluster_archive") as g:
    g.attr(label="archive", style="dotted")
    g.node("c1", "code", shape="box")
    g.node("d1", "data", shape="box")
with dot.subgraph(name="cluster_repr") as g:
    g.attr(label="reproduction", style="dotted")
    g.node("c2", "code", shape="box")
    g.node("d2", "data", shape="box")
dot.edge("c0", "c1")
dot.edge("c1", "c2")
dot.render(f"{dir_path}/updated_workflow", format="png", cleanup=True)

# upload workflow

dot = graphviz.Digraph(comment="Experiment Archive Upload Workflow")
dot.node("1", "environment")
dot.node("2", "code")
dot.node("3", "data")
dot.node("4", "figures")
dot.node("5", "Package as reproducible artifact")
dot.node("6", "Upload to archive")

dot.edges(["15", "25", "35", "45", "56"])

dot.render(f"{dir_path}/upload", format="png", cleanup=True)


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

dot.render(f"{dir_path}/usage", format="png", cleanup=True)

def create_ascii_file_chart(filepath=".", outfile=f"{dir_path}/file_structure.png", ignoreList=None):

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

    print(ascii_files)

    # Create a new Image
    # make sure the dimensions (W and H) are big enough for the ascii art
    W, H = (400,25*ascii_files.count('\n'))
    im = Image.new("RGBA",(W,H),"white")

    font = ImageFont.truetype(f"{dir_path}/SourceCodePro-Regular.otf", 20)

    # Draw text to image
    draw = ImageDraw.Draw(im)
    # w, h = draw.textsize(ascii_files)
    # draws the text in the center of the image
    # draw.text(((W-w)/2,(H-h)/2), ascii_text, fill="black")
    draw.multiline_text((10, 10), ascii_files, font=font, fill=(0,0,0))

    # Save Image
    im.save(outfile, "PNG")

create_ascii_file_chart()
create_ascii_file_chart(
    filepath=f"{dir_path}/arts-min-req-file-structure",
    outfile=f"{dir_path}/file_structure_minimal.png",
    ignoreList=[]
)
