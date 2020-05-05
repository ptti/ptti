__all__ = ["plot", "plot_defaults"]

import matplotlib.pyplot as plt
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

def plot(model, output, plots, interventions, title, **unused):
    arrays = [np.loadtxt(tsvfile, delimiter="\t")
              for tsvfile in glob("{}*.tsv".format(output))]
    times = [a[:,0] for a in arrays]
    trajectories = [a[:,1:] for a in arrays]

    time = times[0]

    for plot in plots:
        fig, ax = plt.subplots(dpi=300)

        for ts in plot["timeseries"]:
            cols = [model.colindex(c) for c in ts["columns"]]
            series = [np.sum(traj[:,c] for c in cols) for traj in trajectories]
            meanseries = np.average(series, axis=0)
            ax.plot(time, meanseries, lw=1.0, label=ts["title"])

        for intv in interventions:
            ax.axvline(intv["time"], c=(0, 0, 0), lw=0.5, ls='--')

        ax.set_title("{}: {}".format(title, plot["title"]))
        ax.set_xlabel("Time")
        ax.legend()

        plt.savefig("{}-{}.png".format(output, plot["name"]))

