
# current experimental workflow

dot = graphviz.Digraph("Current experimental workflow")
dot.attr(rankdir="LR", label=r"\G", labelloc="t")
dot.node("d1", "raw data")
dot.node("c1", "preprocessing code")
dot.node("d2", "derivative data")
dot.node("c2", "analysis code")
dot.node("f", "figures")
dot.node("g", "Github", shape="rect")
dot.node("a", "archive", shape="rect")
dot.node("p", "paper", shape="rect")

dot.edges([
    ("d1","d2"),
    ("d2","f"),
    ("c1", "g"),
    ("c2", "g"),
    ("f", "p"),
])
dot.edge("c1", "d2", weight="0")
dot.edge("c2", "f", weight="0")
dot.edge("d1", "a", weight="0")
dot.edge("d2", "a", weight="0")
dot.edge("f", "a", style="invis", weight="10")
dot.edge("f", "g", style="invis", weight="10")
dot.edge("c1", "c2", style="invis", weight="10")

dot.render(f"{dir_path}/current_workflow", format="svg", cleanup=True)


# updated experimental workflow

dot = graphviz.Digraph("Updated experimental workflow")
dot.attr(rankdir="LR", label=r"\G", labelloc="t")


dot.node("d1", "raw data")
dot.node("d2", "derivative data")
with dot.subgraph(name="cluster_container") as g:
    g.attr(label="container", style="dotted", labelloc="b")
    g.node("c1", "preprocessing code")
    g.node("c2", "analysis code")
    g.node("e", "environment")
dot.node("f", "figures")
dot.node("a", "archive", shape="rect")
dot.node("p", "paper", shape="rect")
dot.node("t", "timestamp authority", shape="hexagon")

dot.edges([("e", "a")])
dot.edge("t", "a", weight="0")
dot.edge("d1", "t", weight="0")
dot.edge("d2", "t", weight="0")
dot.edge("c1", "t", weight="10")
dot.edge("c2", "t", weight="10")
dot.edge("f", "p", weight="10")
dot.edge("d1","d2", weight="10")
dot.edge("c1", "d2", weight="0")
dot.edge("d2","f", weight="20")
dot.edge("c2", "f", weight="0")
dot.edge("d1", "a", weight="0")
dot.edge("d2", "a", weight="0")
# dot.edge("f", "a", style="invis", weight="10")
dot.edge("c1", "c2", style="invis", weight="1")
dot.edge("d1", "c2", style="invis", weight="1")
# dot.edge("c1", "e", style="invis", weight="10")

# with dot.subgraph(name="cluster_local") as g:
#     g.attr(label="local development environment", style="dotted")
#     # g.node("A1", "Node A1", style="invis", shape="point")
#     g.node("c0", "code", shape="box")
#     g.node("d0", "data", shape="box")
# with dot.subgraph(name="cluster_archive") as g:
#     g.attr(label="archive", style="dotted")
#     g.node("c1", "code", shape="box")
#     g.node("d1", "data", shape="box")
# with dot.subgraph(name="cluster_repr") as g:
#     g.attr(label="reproduction", style="dotted")
#     g.node("c2", "code", shape="box")
#     g.node("d2", "data", shape="box")
# dot.edge("c0", "c1")
# dot.edge("c1", "c2")


dot.render(f"{dir_path}/updated_workflow", format="svg", cleanup=True)
