import streamlit as st
import argparse
import pkg_resources
from ptti.config import config_load, config_save, save_human
from ptti.model import runModel
from ptti.plotting import plot
from ptti.economic import calcEconOutputs, calcArgumentsODE
from multiprocessing import Pool
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging as log
import os
import sys
import numpy as np
import yaml
import collections
from collections import namedtuple
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import pandas as pd
import streamlit as st
# from plotting.py import yaml_plot_defaults

models = {}
for ep in pkg_resources.iter_entry_points(group='models'):
    models.update({ep.name: ep.load()})

def mkcfg(sample):
    cfg = config_load(args.yaml, sample)

    for meta in ("model", "tmax", "steps", "samples", "output", "date"):
        arg = getattr(args, meta)
        if arg is not None:
            cfg["meta"][meta] = arg
    for init in ("N", "IU"):
        arg = getattr(args, init)
        if arg is not None:
            cfg["initial"][init] = arg

    if isinstance(cfg["meta"]["model"], str):
        model = models.get(cfg["meta"]["model"])
        if model is None:
            log.error("Unknown model: {}".format(cfg["meta"]["model"]))
            sys.exit(255)
        cfg["meta"]["model"] = model

    log.debug("Config: {}".format(cfg))
    return cfg

def pmap(f, v): return list(map(f, v))

def runSample(arg):
    i, cfg = arg

    # set random seed for the benefit of stochastic simulations
    cfg["meta"]["seed"] = i

    # for indexed samples, select the right parameter:
    for k, v in cfg["parameters"].copy().items():
        if isinstance(v, list):
            cfg["parameters"][k] = v[i]
    for iv in cfg["interventions"]:
        for k, v in iv.copy().items():
            if isinstance(v, list):
                iv[k] = v[i]

    t, traj, events, paramtraj = runModel(**cfg["meta"], **cfg)

    tseries = np.concatenate([t[:, None], traj], axis=1)

    return tseries, events, paramtraj

st.title("PTTI Policy Simulator")

st.sidebar.title("Interactive PTTI Policy Creator")
st.sidebar.markdown(
    """
Run different epidemic control policies for COVID-19. This uses the  
[PTTI](https://github.com/ptti/ptti) model.
"""
)

POLICY_NAMES = ["1", "2a", "2b", "4a", "4b"]
DEFAULT_TEXT = "Model Goes Here."
HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""

base_policy = st.sidebar.selectbox("Policy name", POLICY_NAMES)
to_run = st.sidebar.button("Run Model")
# model_load_state = st.info(f"Loading policy '{base_policy}'...")

arglist = namedtuple('arglist', 'model, yaml, tmax, steps, samples, output, date, N, IU, save_param, econ, statistics, plot')
args = arglist('SEIRCTODEMem', '..\examples\scenarios\ptti-scenario-'+ str(base_policy) + '.yaml', 365, 365, None, None, None, 10000, 1, [], False, False, False)

import os

st.text(os.getcwd())

if to_run:
    cfg = mkcfg(0)
    samples = [(i, mkcfg(i)) for i in range(cfg["meta"]["samples"])]
    results = pmap(runSample, samples)

    for s, (traj, events, paramtraj) in zip(samples, results):
        econ_args = calcArgumentsODE(traj, paramtraj, cfg)
        econ = calcEconOutputs(**econ_args)

    # for i in plots:

    i = 2
    chart_data = pd.DataFrame([x[i] for x in traj], columns=[[col['name'] for col in cfg['meta']['model'].observables][i]])
    plt.plot(chart_data)
    st.pyplot()