import os


import graphviz
import ipywidgets as widgets
import numpy as np

from bokeh.layouts import column, gridplot
from bokeh.models import Legend, LegendItem, Span, ColumnDataSource, Title
from bokeh.io import show
from bokeh.plotting import figure, output_file, save
from jinja2 import Environment, PackageLoader, select_autoescape
from matplotlib import pyplot as plt

from .watch_calibration import OUTPUT_PATH

jinja_env = Environment(
    loader=PackageLoader("watch_calibration", "."),
    autoescape=select_autoescape()
)

def pad_wins(w1, w2, shift_amt):
    """Pad two signal windows with zeros to accomdate shift.

    Args:
        w1, w2 (Iterable): signal windows to plot
        shift_amt (int): number of samples to shift signals w.r.t each other

    Returns:
        (w1, w2) (tuple): padded windows
    """

    if shift_amt > 0:
        w1 = np.pad(w1, (0,shift_amt//2))
        w2 = np.pad(w2, (shift_amt//2,0))
    else:
        w2 = np.pad(w2, (0,-shift_amt//2))
        w1 = np.pad(w1, (-shift_amt//2,0))

    return w1, w2


def plot_wins(w1, w2, shift_amt=0, title=None):
    """Plot two signal windows.

    Args:
        w1, w2 (Iterable): signal windows to plot

    Keyword Args:
        shift_amt (int): number of samples to shift signals w.r.t. each other
        title (str): plot title
    """

    fig = plt.figure(figsize=(8,2))
    fig.canvas.header_visible = False

    w1, w2 = pad_wins(w1, w2, shift_amt)
    plt.plot(w1)
    plt.plot(w2)

    if title:
        plt.title(title)

    plt.show()


def plot_peaks(x, peaks, fs, display_sec=2):
    """Plot sliding plot of x with values in peaks marked by X"s

    Args:
        x (Iterable): signal to plot
        peaks (Iterable): signal peaks to mark with an "X"
        fs (int): sampling rate

    Keyword Args:
        display_sec (int): number of seconds to display in window at given time
    """

    if len(x) > fs * display_sec:
        fig, ax = plt.subplots(figsize=(10,6))
        fig.canvas.header_visible = False
        t = np.arange(len(x))/fs
        ax.plot(t, x)
        ax.plot(peaks/fs, x[peaks], "x")
        ax.set_xlim(0,2)
        ax.set_title(f"{len(peaks)} peaks detected")

        slider = widgets.FloatSlider(
            value=0, max=len(x) / fs - display_sec,
            step=0.1, continuous_update=True
        )
        def update(change):
            ax.set_xlim(change.new, (change.new+2))
            fig.canvas.draw_idle()
        slider.observe(update, names="value")

        return slider
    return None


def generate_figures(wcs, drift_rows):
        """
        Generate figures for watch-calibration section of ARTS open framework
        paper.

        Args:
            wcs (dict): keys are data names; values are WatchCalibration objects
            drift_rows (list): drift values per second for all experiment runs

        Outputs:
            table showing drift comparisons across trials
            plots visualizing drift between ideal watch and dataset
            interactive bokeh plot
        """

        # drift calculation table
        titles = list(wcs)
        drift_htmls = []
        template = jinja_env.get_template("drift_comparison.html.j2")
        for i, row in enumerate(drift_rows):
            drift_htmls.append(template.render(title=titles[i], rows=row))

        dot = graphviz.Digraph()
        dot.graph_attr["fontname"] = "helvetica"
        dot.node_attr["fontname"] = "helvetica"
        dot.edge_attr["fontname"] = "helvetica"
        dot.attr(
            label="Combined Drift Comparison",
            labelloc="t", fontsize="16", margin="0,.5"
        )
        dot.attr(pad="0,0")
        dot.attr("node", shape="none")

        with dot.subgraph(name="cluster_layout") as layout:
            layout.attr(style="invis")

            with layout.subgraph(name="cluster_top") as top_row:
                top_row.attr(rank="same", style="invis")
                top_row.node("table1", label=drift_htmls[1])
                top_row.node("table2", label=drift_htmls[3])
                top_row.edge("table1", "table2", style="invis")

            with layout.subgraph(name="cluster_bottom") as bottom_row:
                bottom_row.attr(rank="same", style="invis")
                bottom_row.node("table3", label=drift_htmls[0])
                bottom_row.node("table4", label=drift_htmls[2])
                bottom_row.edge("table3", "table4", style="invis")

        out_file = os.path.join(OUTPUT_PATH, "drift_table")
        dot.render(out_file, format="svg", cleanup=True)
        dot.render(out_file, format="png", cleanup=True)

        # ensure deriv data is created for each experiment
        for i, (name, w) in enumerate(wcs.items()):
            w.create_deriv_from_raw()

        # peak comparison figure
        fig, axs = plt.subplots(2, 2, figsize=(10, 6))
        axs = axs.flatten()

        # figure settings
        plt.style.use("grayscale")
        fig.set_facecolor("white")
        fig.canvas.header_visible = False

        # legend labels
        audio_label = "audio signal"
        peak_label = "peak calculated from waveform"
        click_label = "ideal peak with no drifts"

        # interactive bokeh plots
        plots = []

        # build plot and interactive bokeh plot
        for i, (name, w) in enumerate(wcs.items()):
            w_audio = w.trim_audio(w.load_audio()[0])

            drift_per_day = drift_rows[i][0][3]
            drift_samples = drift_per_day / (60 * 60 * 24) * w.audio_len

            peak = w.peaks[-2] # pick peak at end of recording given trim

            win = w._normalize(w_audio[peak-w.window_len:peak+w.window_len])
            t = np.arange(len(win)) / w.fs

            # matplotlib
            ax = axs[i]
            ax.set_title(f"{name}")
            ax.plot(t, win, color="gray", label=audio_label)
            ax.vlines(
                [w.window_len / w.fs],
                np.min(win), np.max(win),
                linestyles="dotted", label=peak_label
            )
            ax.vlines(
                [(w.window_len + drift_samples) / w.fs],
                np.min(win), np.max(win),
                linestyles="dashed", label=click_label
            )

            # bokeh
            p = figure(title=name, width=600, height=400)
            p.line(t, win, line_color="gray", line_width=2)
            peak_line = Span(
                location=w.window_len / w.fs, dimension="height",
                line_color="black", line_dash="dotted", line_width=2
            )
            click_line = Span(
                location=(w.window_len + drift_samples) / w.fs,
                dimension="height", line_color="black",
                line_dash="dashed", line_width=2,
            )
            p.add_layout(peak_line)
            p.add_layout(click_line)
            p.title.align = "center"
            plots.append(p)

        # matplotlib
        handles = [
            plt.Line2D([0], [0], color="gray", label=audio_label),
            plt.Line2D(
                [0], [0], color="black", linestyle="dashed", label=peak_label
            ),
            plt.Line2D(
                [0], [0], color="black", linestyle="dotted", label=click_label
            ),
        ]
        fig.legend(
            handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0),
            ncol=3, frameon=True, fontsize="small"
        )
        fig.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        fig.suptitle("Watch tick drift compared to ideal tick", y=1)
        plt.savefig(
            os.path.join(OUTPUT_PATH, "drift_figure.png"),
            dpi=300, bbox_inches="tight"
        )
        plt.savefig(
            os.path.join(OUTPUT_PATH, "drift_figure.svg"), bbox_inches="tight"
        )

        # bokeh
        grid = gridplot(
            [plots[0:2], plots[2:4]],
            toolbar_location="right",
        )
        # add legend
        legend_fig = figure(width=1200, height=100, toolbar_location=None)
        legend_fig.outline_line_color = None
        legend_fig.grid.grid_line_color = None
        legend_fig.axis.visible = False
        source = ColumnDataSource(data=dict(x=[0], y=[0]))
        legend = Legend(items=[
            LegendItem(label=audio_label, renderers=[
                legend_fig.line(
                    x="x", y="y", line_color="gray", line_width=2, source=source
                )
            ]),
            LegendItem(label=peak_label, renderers=[
                legend_fig.line(
                    x="x", y="y", line_color="black", line_dash="dotted",
                    line_width=2, source=source
                )
            ]),
            LegendItem(label=click_label, renderers=[
                legend_fig.line(
                    x="x", y="y", line_color="black", line_dash="dashed",
                    line_width=2, source=source
                )
            ])
        ], location="center", orientation="horizontal")
        legend_fig.add_layout(legend, "center")
        final_layout = column(grid, legend_fig, align="center")
        # save bokeh plot to html
        output_file(os.path.join(OUTPUT_PATH, "drift_figure.html"))
        save(final_layout)

        return f"{out_file}.svg"
