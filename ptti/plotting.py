__all__ = ["plot", "plot_defaults"]

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

from datetime import datetime
import numpy as np
from glob import glob
import yaml

yaml_plot_defaults = """
- name: susceptibles
  title: Susceptible Individuals
  timeseries:
    - title: Unconfined
      columns: [SU]
    - title: Isolated
      columns: [SD]
- name: exposed
  title: Exposed Individuals
  timeseries:
    - title: Unconfined
      columns: [EU]
    - title: Isolated
      columns: [ED]
- name: infections
  title: Infectious Individuals
  timeseries:
    - title: Unconfined
      columns: [IU]
    - title: Isolated
      columns: [ID]
- name: removed
  title: Cumulative Infections
  timeseries:
    - title: Removed / Recovered
      columns: [RU, RD]
- name: reproduction
  title: Reproduction Number
  timeseries:
    - title: Reproduction Number
      columns: [-1]
"""

plot_defaults = yaml.load(yaml_plot_defaults, yaml.FullLoader)

def plot(model, output, plots, title, envelope=True, start=None, **unused):

    colours = [mcolors.to_rgb(c) for c in mcolors.TABLEAU_COLORS.values()]

    arrays = [np.loadtxt(tsvfile, delimiter="\t")
              for tsvfile in glob("{}*[0-9].tsv".format(output))]
    times = [a[:,0] for a in arrays]
    trajectories = [a[:,1:] for a in arrays]

    with open("{}-0-events.yaml".format(output)) as fp:
        interventions = yaml.load(fp.read(), yaml.FullLoader)

    time = times[0]

    if start is not None:
        time_offset = datetime.strptime(start, "%Y/%m/%d").toordinal()
        time += time_offset
    else:
        time_offset = 0

    for plot in plots:
        fig, ax = plt.subplots(dpi=300)

        for i, ts in enumerate(plot["timeseries"]):
            colour = colours[i % len(colours)]
            cols = [model.colindex(c) for c in ts["columns"]]
            series = [np.sum(traj[:,c] for c in cols) for traj in trajectories]
            meanseries = np.average(series, axis=0)
            if len(series) > 1 and envelope:
                stdseries = np.std(series, axis=0)
                ax.plot(time, meanseries, lw=1.0, color=colour, label=ts["title"])
                ax.fill_between(time, meanseries+stdseries, meanseries+stdseries, color=list(colour) + [0.3])
                ax.fill_between(time, meanseries+stdseries, meanseries-stdseries, color=list(colour) + [0.3])
            elif len(series) > 1:
                stdseries = np.std(series, axis=0)
                for traj in series:
                    ds = np.zeros(len(traj))
                    ds = np.true_divide(np.abs(traj - meanseries), stdseries, where=stdseries > 0)
                    dist = np.average(ds)
                    ax.plot(time, traj, color=list(colour) + [np.exp(-dist)])
            else:
                ax.plot(time, meanseries, lw=1.0, color=colour, label=ts["title"])

        for intv in [i for i in interventions if "time" in i]:
            ax.axvline(intv["time"] + time_offset, c=(0, 0, 0), lw=0.5, ls='--')

        ax.set_title("{}: {}".format(title, plot["title"]))

        if start is not None:
            months = mdates.MonthLocator()
            ym_fmt = mdates.DateFormatter('%Y/%m')
            ax.xaxis.set_major_locator(months)
            ax.xaxis.set_major_formatter(ym_fmt)
            fig.autofmt_xdate()
        else:
            ax.set_xlabel("Days since start of outbreak")

        ax.legend()

        plt.savefig("{}-{}.png".format(output, plot["name"]))


def iplot(model, traj, events, paramtraj, cfg):
    # model = cfg['meta']['model']
    colours = [mcolors.to_rgb(c) for c in mcolors.TABLEAU_COLORS.values()]

    time = traj[:, 0]

    start = cfg["meta"]["start"]
    time_offset = datetime.strptime(start, "%Y/%m/%d").toordinal()
    time += time_offset

    months = mdates.MonthLocator(interval=4)
    # ym_fmt = mdates.DateFormatter('%Y/%m')
    fig, axes = plt.subplots(3, 1, figsize=(8, 24))
    ((ax_sr, ax_ei, ax_r)) = axes

    for i, ts in enumerate(["SU", "SD", "RU", "RD"]):
        colour = colours[i % len(colours)]
        ax_sr.plot(time, traj[:, model.colindex(ts)], color=colour, label=ts)

    for i, ts in enumerate(["EU", "ED", "IU", "ID"]):
        colour = colours[i % len(colours)]
        ax_ei.plot(time, traj[:, model.colindex(ts)], color=colour, label=ts)

    ax_r.plot(time, traj[:, -1], color=colours[0], label="R(t)")

    legends = []
    # All plots have intervention lines, labels, legends...
    for plot_axis in [ax_sr, ax_ei, ax_r]:
        for intv in [i for i in events if ("time" in i and i['name'] != 'Flu')]:
            if 'c' in intv['parameters']:
                c = intv['parameters']['c']
                c_min = 3.3
                c_max = 8.9
                c_midpoint = 5.5
                if c < c_midpoint:
                    plot_axis.axvline(intv["time"] + time_offset, lw=1.25, ls='--', c=(1, (c - c_min)/(c_midpoint-c_min), 0))
                else:
                    plot_axis.axvline(intv["time"] + time_offset, lw=1.25, ls='--', c=((c_max - c) / (c_max - c_midpoint), 1, 0))
                # plot_axis.axvline(intv["time"] + time_offset, c=intervention_color, lw=0.5, ls='--')
                # print("Draw lines")
            elif intv['name'] == 'Targeted Testing':
                plot_axis.axvline(intv["time"] + time_offset, c=(0, 0, 0), lw=0.75, ls=':')
            elif intv['name'] == "Masks":
                plot_axis.axvline(intv["time"] + time_offset, c=(1, 1, 0), lw=0.75, ls=':')
            else:
                plot_axis.axvline(intv["time"] + time_offset, c=(0, 0, 0), lw=0.75, ls='--')
        plot_axis.xaxis.set_major_locator(months)
        # plot_axis.xaxis.set_major_formatter(ym_fmt)
        plot_axis.set_xlabel("Date")
        legends.append(plot_axis.legend())
        #legends.append(plot_axis.legend([Line2D([0], [0], c=(0, 0, 0), lw=0.75, ls=':'),
        #                            Line2D([0], [0], c=(1, 0, 0), lw=1.25, ls='--'),
        #                            Line2D([0], [0], c=(0, 1, 0), lw=1.25, ls='--')],
        #                           ["Test and Trace", "Close Economy", "Open Economy"], loc=7))

    fig.autofmt_xdate()
    return fig, axes
