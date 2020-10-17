#!/usr/bin/env python

###
### This script generates the data for the plots in the Methods paper
###

from ptti.config import config_load
from ptti.model import runModel
from ptti.seirct_ode import SEIRCTODEMem
import logging as log
import sys
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pkg_resources
from glob import glob
import numpy as np

colours = [mcolors.to_rgb(c) for c in mcolors.TABLEAU_COLORS.values()]
def colour(i):
    return colours[i % len(colours)]

log.basicConfig(stream=sys.stdout, level=log.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s')

def basic_config():
    configfile = os.path.join(pkg_resources.get_distribution("ptti").location, "figures", "ptti-methods.yaml")
    return config_load(configfile)

def figure_testing(eta, frame):
    iseries = []
    rseries = []
    labels = []
    model = SEIRCTODEMem
    for x in np.linspace(0.0, 1.0, 11):
        theta = 1.0/(14**x)
        log.info("Figure: testing -- theta = {}".format(theta))

        cfg = basic_config()
        cfg["meta"]["model"] = model
        cfg["parameters"]["theta"] = theta
        cfg["parameters"]["eta"] = eta
        cfg["parameters"]["chi"] = 0.5

        t, traj, _, _ = runModel(**cfg["meta"], **cfg)

        E = traj[:,model.colindex("EU")]
        I = traj[:,model.colindex("IU")]
        R = traj[:,-1]

        iseries.append(E+I)
        rseries.append(R)

        if theta == 0: labels.append("never")
        else: labels.append("1/θ = %.01f days" % (1/theta))
    iseries.insert(0, t)
    rseries.insert(0, t)

    ## plot testing EI
    fig, ax = plt.subplots(1,1, figsize=(12,6))
    for i in range(1, len(iseries)):
        ax.plot(iseries[0], iseries[i], lw=1, color=colour(i-1), label=labels[i-1])
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 12000000)
    ax.set_xlabel("t")
    ax.set_ylabel("E + I")
    ax.legend(loc="upper right")
    ax.set_title("Testing with tracing success η = %.00f%%" % (100* eta))
    plt.savefig("testing-eta-%04d.png" % frame)

    fig, ax = plt.subplots(1,1, figsize=(12,6))
    for i in range(1, len(rseries)):
        ax.plot(rseries[0], rseries[i], lw=1, color=colour(i-1), label=labels[i-1])
    ax.axhline(y=1, xmin=0, xmax=300, lw=2, color=(0.9, 0.3, 0.3))
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 3)
    ax.set_xlabel("t")
    ax.set_ylabel("R")
    ax.legend(loc="upper right")
    ax.set_title("Testing with tracing success η = %.00f%%" % (100*eta))
    plt.savefig("testing-r-eta-%04d.png" % frame)

def figure_tracing(testing, frame):
    iseries = []
    rseries = []
    labels = []
    model = SEIRCTODEMem
    for eta in np.linspace(0.0, 1.0, 11):
        log.info("Figure: tracing -- eta = {}".format(eta))

        cfg = basic_config()
        cfg["meta"]["model"] = model
        cfg["parameters"]["theta"] = theta
        cfg["parameters"]["eta"] = eta
        cfg["parameters"]["chi"] = 0.5

        t, traj, _, _ = runModel(**cfg["meta"], **cfg)

        E = traj[:,model.colindex("EU")]
        I = traj[:,model.colindex("IU")]
        R = traj[:,-1]

        iseries.append(E+I)
        rseries.append(R)

        if eta == 0.0: labels.append("never")
        else: labels.append("η = %.00f%%" % (100*eta))

    iseries.insert(0, t)
    rseries.insert(0, t)

    ## plot tracing EI
    fig, ax = plt.subplots(1,1, figsize=(12,6))
    for i in range(1, len(iseries)):
        ax.plot(iseries[0], iseries[i], lw=1, color=colour(i-1), label=labels[i-1])
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 12000000)
    ax.set_xlabel("t")
    ax.set_ylabel("E + I")
    ax.legend(loc="upper right")
    ax.set_title("Tracing, on average, in two days with testing delay 1/θ = %.02f days" % (1/theta))
    plt.savefig("tracing-theta-%04d.png" % frame)

    fig, ax = plt.subplots(1,1, figsize=(12,6))
    for i in range(1, len(rseries)):
        ax.plot(rseries[0], rseries[i], lw=1, color=colour(i-1), label=labels[i-1])
    ax.axhline(y=1, xmin=0, xmax=300, lw=2, color=(0.9, 0.3, 0.3))
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 3)
    ax.set_xlabel("t")
    ax.set_ylabel("R")
    ax.legend(loc="upper right")
    ax.set_title("Tracing, on average, in two days with testing delay 1/θ = %.02f days" % (1/theta))
    plt.savefig("tracing-r-theta-%04d.png" % frame)

if __name__ == '__main__':
    i = 0
    for eta in np.linspace(0.0, 1.0, 101):
        figure_testing(eta, i)
        i += 1
    i = 0
    for x in np.linspace(0.0, 1.0, 101):
        theta = 1/(14**x)
        figure_tracing(theta, i)
        i += 1

    os.system("ffmpeg -y -r 5 -i testing-eta-%04d.png -c:v libx264 -vf 'fps=25,format=yuv420p' testing.mp4")
    os.system("ffmpeg -y -r 5 -i testing-r-eta-%04d.png -c:v libx264 -vf 'fps=25,format=yuv420p' testing-r.mp4")
    os.system("ffmpeg -y -r 5 -i tracing-theta-%04d.png -c:v libx264 -vf 'fps=25,format=yuv420p' tracing.mp4")
    os.system("ffmpeg -y -r 5 -i tracing-r-theta-%04d.png -c:v libx264 -vf 'fps=25,format=yuv420p' tracing-r.mp4")
