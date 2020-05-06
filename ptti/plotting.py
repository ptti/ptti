__all__ = ["plot", "plot_defaults"]

import matplotlib.pyplot as plt
import matplotlib.colors as mc
import numpy as np
from glob import glob
import yaml

yaml_plot_defaults = """
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
"""

plot_defaults = yaml.load(yaml_plot_defaults, yaml.FullLoader)

def plot(model, output, plots, interventions, title, envelope=True, **unused):

    colours = [mc.to_rgb(c) for c in mc.TABLEAU_COLORS.values()]

    arrays = [np.loadtxt(tsvfile, delimiter="\t")
              for tsvfile in glob("{}*.tsv".format(output))]
    times = [a[:,0] for a in arrays]
    trajectories = [a[:,1:] for a in arrays]

    time = times[0]

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

        for intv in interventions:
            ax.axvline(intv["time"], c=(0, 0, 0), lw=0.5, ls='--')

        ax.set_title("{}: {}".format(title, plot["title"]))
        ax.set_xlabel("Time")
        ax.legend()

        plt.savefig("{}-{}.png".format(output, plot["name"]))

