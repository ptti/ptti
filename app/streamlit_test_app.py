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

def mkcfg(filename, sample):
    cfg = config_load(filename, sample)

    if isinstance(cfg["meta"]["model"], str):
        model = models.get(cfg["meta"]["model"])
        if model is None:
            log.error("Unknown model: {}".format(cfg["meta"]["model"]))
            sys.exit(255)
        cfg["meta"]["model"] = model

    log.debug("Config: {}".format(cfg))
    return cfg

def pmap(f, v): return list(map(f, v))

# @st.cache(suppress_st_warning=True) #Enable caching to get this to run faster, esp. for pre-run scenarios.
def runSample(arg):
    i, cfg = arg

    # set random seed for the benefit of stochastic simulations
    cfg["meta"]["seed"] = i
    # cfg["meta"]["model"] = 'SEIRCTODEMem'

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

POLICY_NAMES = ["1", "2a", "2b", "4a", "4b", "4c", "4d"]
POLICY_NAMES = [name+append for name in POLICY_NAMES for append in ["","-Trig"]]
POLICY_NAMES.append("19")
DEFAULT_TEXT = "Model Goes Here."
HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""

base_policy = st.sidebar.selectbox("Policy name", POLICY_NAMES)
to_run = st.sidebar.button("Run Model")
# model_load_state = st.info(f"Loading policy '{base_policy}'...")

filename = '..\examples\scenarios\ptti-scenario-'+ str(base_policy) + '.yaml'
args = yaml.safe_load(open(filename))
args['meta']['model'] = 'SEIRCTODEMem'
args['yaml'] = filename
cfg = mkcfg(filename,0)

st.write("Scenario: " + cfg['meta']['title'])

# This will be modified below.

# We want to show the intervention details and timing.
# For preconfigured interventions, For now only allow changing times.
# NOTE: The first four interventions are fixed past events.
To_Graph = st.sidebar.multiselect("Outcomes To Plot", ["Susceptible", "Exposed", "Infected", "Recovered", "Quarantined"],
                                  default=["Susceptible", "Infected", "Quarantined"])

Intervention_Start = st.sidebar.date_input("Intervention Start (Not working.)")

# min_value=datetime.now() ) <- No changing the past.
# "How you think you gonna move time while you're standin in it you dumn ass three-dimensional monkey ass dummies?"

st.write(str(type(Intervention_Start)) + " " + str(Intervention_Start))

#import os
# st.text(os.getcwd())

if to_run:
    samples = [(i, cfg) for i in range(cfg["meta"]["samples"])]

    results = pmap(runSample, samples)

    for s, (traj, events, paramtraj) in zip(samples, results):
        econ_args = calcArgumentsODE(traj, paramtraj, cfg)
        econ = calcEconOutputs(**econ_args)

    # for i in plots: ["Susceptible", "Exposed", "Infected", "Recovered", "Quarantined"])
    if len(To_Graph)>0:
        df_plot_results = pd.DataFrame()
        Out_Columns = [col['name'] for col in cfg['meta']['model'].observables]
        for Compartment in To_Graph:
            if Compartment == "Quarantined":
                C_list = [i for i in range(len(Out_Columns)) if Out_Columns[i][1]=="D"]
            else:
                Leftmost = Compartment[0]
                C_list = [i for i in range(len(Out_Columns)) if Out_Columns[i][0] == Leftmost]
            C_total = list()
            for x in traj:
                C_total.append(sum([x[c] for c in C_list]))
            df_plot_results[Compartment] = C_total.copy()

        plt.plot(df_plot_results)
        pop = cfg['initial']['N']
        for i in cfg['interventions']:
            if ('c' in i['parameters'].keys() and 'time' in i.keys()):
                if i['parameters']['c'] == 3.3: # Shouldn't fix this, should use shutdown value
                    plt.plot([i['time'], i['time']], [0, pop], color='red', linestyle='-', linewidth=0.5)
                elif i['parameters']['c'] == 6.6: # Shouldn't fix this, should use correct value
                    plt.plot([i['time'], i['time']], [0, pop], color='yellow', linestyle='-', linewidth=0.5)
                elif i['parameters']['c'] == 8.8: # Shouldn't fix this, should use correct value
                    plt.plot([i['time'], i['time']], [0, pop], color='green', linestyle='-', linewidth=0.5)
                else:
                    plt.plot([i['time'], i['time']], [0, pop], color='k', linestyle='-', linewidth=0.5)
            else:
                pass # These are interventions other than changing distancing - like running PTTI. We should show that.

        plt.legend(To_Graph)
        st.pyplot()