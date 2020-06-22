import streamlit as st
from ptti.config import config_load
from ptti.model import runModel
from ptti.economic import calcEconOutputs, calcArgumentsODE
from ptti.seirct_ode import SEIRCTODEMem
from ptti.plotting import iplot
from datetime import date, datetime, timedelta
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import pandas as pd
import streamlit as st
# from plotting.py import yaml_plot_defaults


@st.cache(allow_output_mutation=True) #Enable caching to get this to run faster, esp. for pre-run scenarios.
def cachedRun(*av, **kw):
    t, traj, events, paramtraj = runModel(*av, **kw)
    tseries = np.concatenate([t[:, None], traj], axis=1)
    return tseries, events, paramtraj

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

cfg = config_load(os.path.join("..", "examples", "structured", "ptti-past.yaml"))

cfg_relax = os.path.join("..", "examples", "structured", "ptti-relax.yaml")
cfg_flu   = os.path.join("..", "examples", "structured", "ptti-fluseason.yaml")
# Add flu season to TTI...
cfg_tti   = os.path.join("..", "examples", "structured", "ptti-tti.yaml")
cfg_trig  = os.path.join("..", "examples", "structured", "ptti-trig.yaml")

intervention_list = []

start = date(int(cfg['meta']['start'][0:4]), int(cfg['meta']['start'][5:7]), int(cfg['meta']['start'][8:10]))

end_shutdown = st.sidebar.checkbox("End Shutdown")
if end_shutdown:
    intervention_list.append(cfg_relax)
end_date = st.sidebar.date_input("Shutdown End Date",
                                     value=(start+timedelta(days=199)), max_value=start+timedelta(days=cfg['meta']['tmax']))
TTI = st.sidebar.checkbox("Test and Trace")
if TTI:
    intervention_list.append(cfg_flu)
    intervention_list.append(cfg_tti)
    #TTI_Launch = st.sidebar.date_input("Test and Trace Ramp-up Period (Start and End)",
    #                                 value=((start+timedelta(days=152)), start+timedelta(days=257)), max_value=start+timedelta(days=cfg['meta']['tmax']))
    # Error with too-close dates needs to be fixed before this is put in.
TTI_rate_inf = st.sidebar.slider("Symptomatic percentage tested (at end of ramp-up)", value=0.8,
                                        min_value=0.1, max_value=1.0)
TTI_chi = st.sidebar.slider("Trace Speed (chi = Percentage of traces complete on day 1)", value=0.8, min_value=0.1,
                            max_value=1.0)
TTI_eta = st.sidebar.slider("Trace Success (eta = Percentage of contacts traced)", value=0.8, min_value=0.1,
                            max_value=1.0)
                              #mouseover="System starts at 10% operational, scales to 100% over this many days."
triggers = st.sidebar.checkbox("Reimpose Shutdowns As Needed")
if triggers:
    intervention_list.append(cfg_trig)
#dance = False
#dance = st.sidebar.checkbox("Dance!")

cfg = config_load(filename=os.path.join("..", "examples", "structured", "ptti-past.yaml"),
                  interventions=[[i, 0] for i in intervention_list])
cfg["meta"]["model"] = SEIRCTODEMem
defaults = {}
defaults.update(cfg["initial"])
defaults.update(cfg["parameters"])

if end_shutdown:
    for i in cfg['interventions']:
        if i['name' ]== "End Lockdown":
            i['time'] = (end_date-start).days

if TTI:
    Phases = max([i['phase'] if i['name'] == "Targeted Testing" else 0 for i in cfg['interventions']])
    for i in cfg['interventions']:
        if i['name'] == "Targeted Testing":
            i['parameters']['chi'] = TTI_chi
            i['parameters']['eta'] = TTI_eta
            # Set date based on number of phases (3)
            pct_implemented = i['phase'] / Phases
            i['parameters']['tested'] = TTI_rate_inf * pct_implemented
            # Set dates. (Error for bad dates. Need to fix before making this part live.)

cfg['interventions'].sort(key=lambda k: ("time" not in k, k.get("time", 100000))) #Otherwise, time changes can make things go backwards.

# to_run = st.sidebar.button("Run Model")
# model_load_state = st.info(f"Loading policy '{base_policy}'...")

# This will be modified below.

# We want to show the intervention details and timing.
# For preconfigured interventions, For now only allow changing times.
# NOTE: The first four interventions are fixed past events.

# Intervention_Start = st.sidebar.date_input("Intervention Start (Not working.)")

Now = datetime.now()
Today = date(Now.year, Now.month, Now.day) #<- No changing the past.
Model_Today = (Today-start).days
# "How you think you gonna move time while you're standin' in it you dumb ass three-dimensional monkey ass dummies?"


traj, events, paramtraj = cachedRun(**cfg["meta"], **cfg)
interventions = sorted(events + [i for i in cfg["interventions"] if "time" in i],
                       key=lambda x: x["time"])

Latest_run = True

econ_args = calcArgumentsODE(traj, paramtraj, cfg)
econ = calcEconOutputs(**econ_args)
Update_Graph=True

fig, axes = iplot(cfg["meta"]["model"], traj, interventions, paramtraj, cfg)
st.pyplot()



#Econ Outputs / Graph:
st.write("Total COVID-19 Deaths: " + str(econ['Medical']['Deaths']))
st.write("")
st.write("Economic Results:")
st.write("Maximum Tracers Needed: " + str(econ['Tracing']['Max_Tracers']))
st.write("Total Tracer Budget: " + str(econ['Tracing']['Tracing_Total_Costs']/1000000) + " million GBP")
st.write("Total Testing Budget: " + str(econ['Testing']['Testing_Total_Costs']/1000000) + " million GBP")
st.write("Total Economic Loss from COVID-19: " + str(econ['Economic']['Total_Productivity_Loss']/1000000) + " million GBP")
# st.write(str(econ))
