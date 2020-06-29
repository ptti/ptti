from ptti.config import config_load
from ptti.model import runModel
from ptti.economic import calcEconOutputs, calcArgumentsODE
from ptti.seirct_ode import SEIRCTODEMem
from datetime import date, datetime, timedelta
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
# import matplotlib.colors as mcolors
# import matplotlib.dates as mdates
from pandas import DataFrame as pd_df
import streamlit as st
# from plotting.py import yaml_plot_defaults


@st.cache(suppress_st_warning=True) #Enable caching to get this to run faster, esp. for pre-run scenarios.
def cachedRun(*av, **kw):
    t, traj, events, paramtraj = runModel(*av, **kw)
    tseries = np.concatenate([t[:, None], traj], axis=1)
    return tseries, events, paramtraj

######################
# Graphing misc:     #
######################

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

if 'app' not in os.getcwd():
    os.chdir('app')


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

cfg_mask = os.path.join("..", "examples", "structured", "ptti-masks.yaml")
cfg_relax = os.path.join("..", "examples", "structured", "ptti-relax.yaml")
cfg_flu   = os.path.join("..", "examples", "structured", "ptti-fluseason.yaml")
# Add flu season to TTI...
cfg_tti   = os.path.join("..", "examples", "structured", "ptti-tti.yaml")
cfg_uti   = os.path.join("..", "examples", "structured", "ptti-uti.yaml")
cfg_trig  = os.path.join("..", "examples", "structured", "ptti-trig.yaml")

intervention_list = []

start = date(int(cfg['meta']['start'][0:4]), int(cfg['meta']['start'][5:7]), int(cfg['meta']['start'][8:10]))

mask = st.sidebar.checkbox("Wear Masks")
if mask:
    intervention_list.append(cfg_mask)


end_shutdown = st.sidebar.checkbox("End Shutdown")
if end_shutdown:
    intervention_list.append(cfg_relax)
end_date = st.sidebar.date_input("Shutdown End Date",
                                     value=(start+timedelta(days=199)), max_value=start+timedelta(days=cfg['meta']['tmax']))

TTI = st.sidebar.radio("Test and Trace", ['None','Untargeted','Targeted'], index=0)
if TTI == 'Targeted':
    intervention_list.append(cfg_flu)
    intervention_list.append(cfg_tti)
elif TTI == 'Untargeted':
    intervention_list.append(cfg_uti)
    #TTI_Launch = st.sidebar.date_input("Test and Trace Ramp-up Period (Start and End)",
    #                                 value=((start+timedelta(days=152)), start+timedelta(days=257)), max_value=start+timedelta(days=cfg['meta']['tmax']))
    # Error with too-close dates needs to be fixed before this is put in.
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
        if triggers: # TODO: We need to make sure triggers don't start until after lockdown ends...
            if i['name'] == "Lockdown Trigger":
                i['after'] = (end_date - start).days + 7  # Cannot trigger for one week.
                pass
            pass

if TTI != 'None':
    for i in cfg['interventions']:
        if "Testing" in i['name']:
            i['parameters']['chi'] = TTI_chi
            i['parameters']['eta'] = TTI_eta
            # Set dates? No - Not currently allowing rollout speed changes.

cfg['interventions'].sort(key=lambda k: ("time" not in k, k.get("time", 100000))) #Otherwise, time changes can make things go backwards.

# to_run = st.sidebar.button("Run Model")
# model_load_state = st.info(f"Loading policy '{base_policy}'...")

# This will be modified below.

# We want to show the intervention details and timing.
# For preconfigured interventions, For now only allow changing times.
# NOTE: The first four interventions are fixed past events.
Graph_Interventions = st.sidebar.checkbox("Graph Interventions", value=True)

To_Graph = st.sidebar.multiselect("Outcomes To Plot", ["Susceptible", "Exposed", "Infected", "Recovered", "Isolated"],
                                  default=["Infected", "Isolated"])

# Intervention_Start = st.sidebar.date_input("Intervention Start (Not working.)")

Now = datetime.now()
Today = date(Now.year, Now.month, Now.day) #<- No changing the past.
Model_Today = (Today-start).days
# "How you think you gonna move time while you're standin' in it you dumb ass three-dimensional monkey ass dummies?"

#import os
# st.text(os.getcwd())

# if dance: st.image('GIPHY_Dance.gif', caption=None, format='GIF')

#if to_run:
# samples = [(i, cfg) for i in range(cfg["meta"]["samples"])]

traj, events, paramtraj = cachedRun(**cfg["meta"], **cfg)
Latest_run = True

econ_args = calcArgumentsODE(traj, paramtraj, cfg)
econ = calcEconOutputs(**econ_args)
Update_Graph=True
# st.write(str(events))

if len(To_Graph)>0:
    pop = cfg['initial']['N']
    df_plot_results = pd_df()
    Out_Columns = [col['name'] for col in cfg['meta']['model'].observables]
    for Compartment in To_Graph:
        if Compartment == "Isolated":
            C_list = [i+1 for i in range(len(Out_Columns)) if Out_Columns[i][1]=="D"]
        else:
            Leftmost = Compartment[0]
            C_list = [i+1 for i in range(len(Out_Columns)) if Out_Columns[i][0] == Leftmost]
        C_total = list()
        for x in traj:
            C_total.append(abs(sum([x[c] for c in C_list])))

        df_plot_results[Compartment] = C_total.copy()

    plt.plot(df_plot_results)
    ax = plt.gca()
    ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))
    ax.xaxis.set_major_formatter(FuncFormatter(date_fmt))
    ax.set_xlabel('Date')
    ax.set_ylabel('People')
    maxy = ax.get_ylim()[1]
    # st.write(str(maxy))

    if Graph_Interventions:
        intervention_lines = [(i['time'], i['parameters']['c']) for i in cfg['interventions'] if
                              ('c' in i['parameters'].keys() and i['name'] != 'Flu' and 'time' in i.keys())]

        intervention_lines_2 = [(i['time'], i['parameters']['c']) for i in events]
        intervention_lines.extend(intervention_lines_2)
        #Cantact Rate items for colors
        c_min = 3.3
        c_max = 8.9
        c_midpoint = 5.5
        for i in intervention_lines:
            c = i[1]
            if c<c_midpoint: # Shouldn't fix this, should use shutdown value
                plt.plot([i[0], i[0]], [0, maxy], color='red', lw=1.25, ls='--', c=(1, (c - c_min)/(c_midpoint-c_min), 0))
            else: # Shouldn't fix this, should use correct value
                plt.plot([i[0], i[0]], [0, maxy], lw=1.25, ls='--', c=((c_max - c) / (c_max - c_midpoint), 1, 0))
    leg = plt.legend(To_Graph, loc='upper center')
    ax_r = ax.twinx()  # instantiate a second axes that shares the same x-axis
    ax_r.set_ylabel('Reproductive Number (Effective)')
    ax_r.plot(traj[:, -1], label="R(t)", color="Grey")
    ax_r.set_ylim([ax_r.get_ylim()[0], 5])
    if Graph_Interventions:
        ax_r.legend([Line2D([0], [0], c="Grey", lw=0.75, ls='-'), Line2D([0], [0], c=(0, 0, 0), lw=0.75, ls=':'),
                          Line2D([0], [0], c=(1, 0, 0), lw=1.25, ls='--'), Line2D([0], [0], c=(0, 1, 0), lw=1.25, ls='--')],
                         ["R(t)", "Test and Trace", "Close Economy", "Open Economy"], loc='upper right')
    else:
        ax_r.legend([Line2D([0], [0], c="Grey", lw=0.75, ls='-')], ["R(t)"], loc='upper right')

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
