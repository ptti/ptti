import streamlit as st
import argparse
import pkg_resources
from ptti.config import config_load, config_save, save_human
from ptti.model import runModel
from ptti.plotting import plot
from ptti.economic import calcEconOutputs, calcArgumentsODE
from ptti.seirct_ode import SEIRCTODEMem
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


@st.cache(suppress_st_warning=True) #Enable caching to get this to run faster, esp. for pre-run scenarios.
def cachedRun(*av, **kw):
    t, traj, events, paramtraj = runModel(*av, **kw)
    tseries = np.concatenate([t[:, None], traj], axis=1)
    return tseries, events, paramtraj

def merge_interventions(cfg, new):
    i1 = cfg.get("interventions", [])
    i2 = new.get("interventions", [])
    interventions = sorted(i1 + i2, key=lambda i: i.get("time", 0))
    cfg["interventions"] = interventions
    return cfg

######################
# Graphing misc:     #
######################
from matplotlib.ticker import FuncFormatter

def y_fmt(y, pos):
    decades = [1e9, 1e6, 1e3, 1e0, 1e-3, 1e-6, 1e-9 ]
    suffix  = ["G", "M", "k", "" , "m" , "u", "n"  ]
    if y == 0:
        return str(0)
    for i, d in enumerate(decades):
        if np.abs(y) >=d:
            val = y/float(d)
            signf = len(str(val).split(".")[1])
            if signf == 0:
                return '{val:d} {suffix}'.format(val=int(val), suffix=suffix[i])
            else:
                if signf == 1:
                    print(val, signf)
                    if str(val).split(".")[1] == "0":
                       return '{val:d} {suffix}'.format(val=int(round(val)), suffix=suffix[i])
                tx = "{"+"val:.{signf}f".format(signf = signf) +"} {suffix}"
                return tx.format(val=val, suffix=suffix[i])

    return y

def date_fmt(x, pos):  # formatter function takes tick label and tick position
    from datetime import date
    start = date(int(cfg['meta']['start'][0:4]), int(cfg['meta']['start'][5:7]), int(cfg['meta']['start'][8:10]))
    return start+timedelta(days=x)

st.title("PTTI Policy Simulator")

st.sidebar.title("Interactive PTTI Policy Creator")
st.sidebar.markdown(
    """
Run different epidemic control policies for COVID-19. This uses the  
[PTTI](https://github.com/ptti/ptti) model.
"""
)



HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""

end = st.sidebar.checkbox("End Shutdown")
TTI = st.sidebar.checkbox("Test and Trace")
triggers = st.sidebar.checkbox("Reimpose Shutdowns As Needed")
dance = st.sidebar.checkbox("Dance!")


cfg = config_load(os.path.join("..", "examples", "structured", "ptti-past.yaml"))
cfg["meta"]["model"] = SEIRCTODEMem
defaults = {}
defaults.update(cfg["initial"])
defaults.update(cfg["parameters"])

cfg_relax = config_load(os.path.join("..", "examples", "structured", "ptti-relax.yaml"), defaults=defaults)
cfg_tti   = config_load(os.path.join("..", "examples", "structured", "ptti-tti.yaml"),   defaults=defaults)
cfg_trig  = config_load(os.path.join("..", "examples", "structured", "ptti-trig.yaml"),  defaults=defaults)

if end: cfg = merge_interventions(cfg, cfg_relax)
if TTI: cfg = merge_interventions(cfg, cfg_tti)
if triggers: cfg = merge_interventions(cfg, cfg_trig)

to_run = st.sidebar.button("Run Model")
# model_load_state = st.info(f"Loading policy '{base_policy}'...")


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

if dance:
    st.image('GIPHY_Dance.gif', caption=None, format='GIF')

if to_run:
    samples = [(i, cfg) for i in range(cfg["meta"]["samples"])]

    traj, events, paramtraj = cachedRun(**cfg["meta"], **cfg)

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
        ax = plt.gca()
        ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))
        ax.xaxis.set_major_formatter(FuncFormatter(date_fmt))
        ax.set_xlabel('Date')
        ax.set_ylabel('People')

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
