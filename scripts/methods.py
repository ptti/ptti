#!/usr/bin/env python

###
### This script generates the data for the plots in the Methods paper
###

from ptti.config import config_load
from ptti.model import runModel
from ptti.seirct_ode import SEIRCTODEMem
from ptti.seirct_abm import SEIRCTABM

import logging as log
import pkg_resources
import sys
import os
import numpy as np

log.basicConfig(stream=sys.stdout, level=log.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s')

def basic_config():
    configfile = os.path.join(pkg_resources.get_distribution("ptti").location, "examples", "ptti-methods.yaml")
    return config_load(configfile)

def figure_testing():
    iseries = []
    rseries = []
    model = SEIRCTODEMem
    for theta in np.linspace(0.0, 0.55, 12):
        log.info("Figure: testing -- theta = {}".format(theta))

        cfg = basic_config()
        cfg["meta"]["model"] = model
        cfg["parameters"]["theta"] = theta

        t, traj = runModel(**cfg["meta"], **cfg)

        E = traj[:,model.colindex("EU")]
        I = traj[:,model.colindex("IU")]
        R = traj[:,-1]

        iseries.append(E+I)
        rseries.append(R)

    iseries.insert(0, t)
    rseries.insert(0, t)

    np.savetxt("testing-theta.tsv", np.vstack(iseries).T, delimiter="\t")
    np.savetxt("testing-r.tsv", np.vstack(rseries).T, delimiter="\t")

def figure_c_testing():
    model = SEIRCTODEMem
    with open("c-testing.tsv", "w") as fp:
        for theta in np.linspace(0.0, 0.55, 25):
            for c in np.linspace(0.0, 20.0, 25):
                log.info("Figure: c testing -- theta = {}, c = {}".format(theta, c))

                cfg = basic_config()
                cfg["meta"]["model"] = model
                cfg["parameters"]["theta"] = theta
                cfg["parameters"]["c"] = c

                t, traj = runModel(**cfg["meta"], **cfg)

                R30 = traj[30, -1]

                line = "%e\t%e\t%e\n" % (theta, c, R30)
                fp.write(line)
            fp.write("\n")

def figure_tracing():
    iseries = []
    rseries = []
    model = SEIRCTODEMem
    for eta in np.linspace(0.0, 1.0, 11):
        log.info("Figure: tracing -- eta = {}".format(eta))

        cfg = basic_config()
        cfg["meta"]["model"] = model
        cfg["parameters"]["theta"] = 0.0714
        cfg["parameters"]["eta"] = eta
        cfg["parameters"]["chi"] = 0.5

        t, traj = runModel(**cfg["meta"], **cfg)

        E = traj[:,model.colindex("EU")]
        I = traj[:,model.colindex("IU")]
        R = traj[:,-1]

        iseries.append(E+I)
        rseries.append(R)

    iseries.insert(0, t)
    rseries.insert(0, t)

    np.savetxt("tracing-theta.tsv", np.vstack(iseries).T, delimiter="\t")
    np.savetxt("tracing-r.tsv", np.vstack(rseries).T, delimiter="\t")

def figure_testing_tracing():
    model = SEIRCTODEMem
    with open("testing-tracing.tsv", "w") as fp:
        for theta in np.linspace(0.0, 0.55, 25):
            for eta in np.linspace(0.0, 1.0, 25):
                log.info("Figure: testing tracing -- theta = {}, eta = {}".format(theta, eta))

                cfg = basic_config()
                cfg["meta"]["model"] = model
                cfg["parameters"]["theta"] = theta
                cfg["parameters"]["eta"] = eta
                cfg["parameters"]["chi"] = 0.5

                t, traj = runModel(**cfg["meta"], **cfg)

                R30 = traj[30, -1]

                line = "%e\t%e\t%e\n" % (theta, eta, R30)
                fp.write(line)
            fp.write("\n")

def compare_abm(mkcfg, desc, out):
    trajectories = []
    samples = 10
    for i in range(samples):
        log.info("Figure: {} sample {}/{}".format(desc, i+1, samples))

        cfg = mkcfg()
        cfg["meta"]["model"] = SEIRCTABM
        t, traj = runModel(**cfg["meta"], **cfg)

        trajectories.append(traj)

    avg = np.average(trajectories, axis=0)
    std = np.std(trajectories, axis=0)
    np.savetxt(out.format("abm-avg"), np.vstack([t, avg.T]).T, delimiter="\t")
    np.savetxt(out.format("abm-std+1"), np.vstack([t, avg.T+std.T]).T, delimiter="\t")
    np.savetxt(out.format("abm-std-1"), np.vstack([t, avg.T-std.T]).T, delimiter="\t")
    np.savetxt(out.format("abm-std+2"), np.vstack([t, avg.T+2*std.T]).T, delimiter="\t")
    np.savetxt(out.format("abm-std-2"), np.vstack([t, avg.T-2*std.T]).T, delimiter="\t")

    cfg = mkcfg()
    cfg["meta"]["model"] = SEIRCTODEMem
    t, traj = runModel(**cfg["meta"], **cfg)
    np.savetxt(out.format("ode"), np.vstack([t, traj.T]).T, delimiter="\t")

def figure_abm1():
    def mkcfg():
        cfg = basic_config()
        cfg["initial"]["N"] = 50000
        cfg["initial"]["IU"] = 100
        cfg["parameters"]["theta"] = 0.0714
        cfg["parameters"]["eta"] = 0.5
        cfg["parameters"]["chi"] = 0.5
        return cfg

    compare_abm(mkcfg, "ABM 1", "compare-{}-1.tsv")


def figure_abm2():
    def mkcfg():
        cfg = basic_config()
        cfg["initial"]["N"] = 1000
        cfg["initial"]["IU"] = 10
        cfg["parameters"]["theta"] = 0.0001
        cfg["parameters"]["eta"] = 1.0
        cfg["parameters"]["chi"] = 1.0
        return cfg

    compare_abm(mkcfg, "ABM 2", "lowtheta-{}-1.tsv")

def figure_abm3():
    def mkcfg():
        cfg = basic_config()
        cfg["initial"]["N"] = 1000
        cfg["initial"]["IU"] = 10
        cfg["parameters"]["theta"] = 2.0
        cfg["parameters"]["eta"] = 1.0
        cfg["parameters"]["chi"] = 2.0
        return cfg

    compare_abm(mkcfg, "ABM 2", "strongtesting-{}-1.tsv")


#figure_testing()
#figure_c_testing()
#figure_tracing()
#figure_testing_tracing()
figure_abm1()
#figure_abm2()
#figure_abm3()
