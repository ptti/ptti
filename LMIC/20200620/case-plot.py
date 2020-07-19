import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
from sys import argv
import os


colours = [mcolors.to_rgb(c) for c in mcolors.TABLEAU_COLORS.values()]

case = int(argv[1])
base = "lmic-case-{}".format(case)

cases = pd.read_csv("lmic-cases.tsv", delimiter="\t")


avg = pd.read_csv(base + "-avg.tsv", delimiter="\t")
std = pd.read_csv(base + "-std.tsv", delimiter="\t")

fig, axes = plt.subplots(2,4, figsize=(24,12))

((ax_s, ax_e, ax_i, ax_r), (ax_c, ax_tb, ax_t, _)) = axes

def plot(ax, col, label, colour):
    ax.plot(avg["t"], avg[col], lw=1, color=colour, label=label)
    ax.fill_between(avg["t"], avg[col], avg[col]+2*std[col], color=list(colour) + [0.15])
    ax.fill_between(avg["t"], avg[col], avg[col]-2*std[col], color=list(colour) + [0.15])
    ax.fill_between(avg["t"], avg[col], avg[col]+std[col], color=list(colour) + [0.3])
    ax.fill_between(avg["t"], avg[col], avg[col]-std[col], color=list(colour) + [0.3])

plot(ax_s, "Sn", "P(x{s}, q{n})", colours[0])
plot(ax_s, "Sy", "P(x{s}, q{y})", colours[1])
ax_s.set_title("Susceptible")

plot(ax_e, "Ey", "P(x{e}, q{y})", colours[0])
plot(ax_e, "En", "P(x{e}, q{n})", colours[1])
ax_e.set_title("Exposed")

plot(ax_i, "Iy", "P(x{i}, q{y})", colours[0])
plot(ax_i, "In", "P(x{i}, q{n})", colours[1])
plot(ax_i, "F", " P(f{y})", colours[3])
ax_i.set_title("Infectious")

plot(ax_r, "Rn", "P(x{r}, q{n})", colours[0])
plot(ax_r, "Ry", "P(x{r}, q{y})", colours[1])
ax_r.set_title("Removed")

plot(ax_c, "Cs", "C(x{s})", colours[0])
plot(ax_c, "Ce", "C(x{e})", colours[1])
plot(ax_c, "Ci", "C(x{i})", colours[2])
plot(ax_c, "Cr", "C(x{r})", colours[3])
plot(ax_c, "Cf", "C(x{f})", colours[4])
ax_c.set_title("Tracing events")

plot(ax_tb, "Tbusy", "T([_])", colours[0])
ax_tb.set_title("Tests pending")

plot(ax_t, "T", "T()", colours[1])
ax_t.set_title("Tests avail")

for ax in axes.flatten():
    ax.set_xlim(0)
    ax.set_ylim(0)
    ax.legend()


cdesc = cases.loc[lambda row: row["case"] == case-1]
title = "        ".join("{}: {}".format(c, cdesc[c].iloc[0]) for c in cdesc.columns)
fig.suptitle(title)

plt.savefig("{}.png".format(base))
