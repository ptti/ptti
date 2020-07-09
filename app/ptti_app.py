from ptti.config import config_load
from ptti.model import runModel
from ptti.economic import calcEconOutputs, calcArgumentsODE
from ptti.seirct_ode import SEIRCTODEMem
from datetime import date, datetime, timedelta
import os
from math import log
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
    thisdate = start+timedelta(days=x)
    return(thisdate.strftime("%b %Y"))

if 'app' not in os.getcwd():
    os.chdir('app')


st.title("UK COVID-19 Policy Simulator")

st.sidebar.title("Interactive PTTI Policy Creator")
st.sidebar.markdown(
    """
Run different epidemic control policies for COVID-19 in the UK. This uses the  
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
# cfg_trig  = os.path.join("..", "examples", "structured", "ptti-trig.yaml")

intervention_list = []

start = date(int(cfg['meta']['start'][0:4]), int(cfg['meta']['start'][5:7]), int(cfg['meta']['start'][8:10]))

mask = st.sidebar.checkbox("Wear Masks")
if mask:
    intervention_list.append(cfg_mask)


end_shutdown = True #st.sidebar.checkbox("End Shutdown")
if end_shutdown:
    intervention_list.append(cfg_relax)
end_date = st.sidebar.date_input("Shutdown End Date",
                                     value=(start+timedelta(days=199)), min_value=start+timedelta(days=90), max_value=start+timedelta(days=cfg['meta']['tmax']))

TTI = st.sidebar.radio("Test and Trace (Starting Mid-May 2020, fully in place by September 2020)", ['None','Untargeted','Targeted'], index=0)
if TTI == 'Targeted':
    intervention_list.append(cfg_flu)
    intervention_list.append(cfg_tti)
elif TTI == 'Untargeted':
    intervention_list.append(cfg_uti)
    #TTI_Launch = st.sidebar.date_input("Test and Trace Ramp-up Period (Start and End)",
    #                                 value=((start+timedelta(days=152)), start+timedelta(days=257)), max_value=start+timedelta(days=cfg['meta']['tmax']))
    # Error with too-close dates needs to be fixed before this is put in.
TTI_chi_trans = st.sidebar.slider("Percentage of traces complete on day 1", value=0.55, min_value=0.1,
                            max_value=0.99)
TTI_chi = -1*log(1-TTI_chi_trans)
TTI_eta = st.sidebar.slider("Trace Success (eta = Percentage of contacts traced)", value=0.8, min_value=0.1,
                            max_value=1.0)
                              #mouseover="System starts at 10% operational, scales to 100% over this many days."
triggers = st.sidebar.checkbox("Reimpose Shutdowns As Needed")
#dance = False
#dance = st.sidebar.checkbox("Dance!")

cfg = config_load(filename=os.path.join("..", "examples", "structured", "ptti-past.yaml"),
                  interventions=[[i, 0] for i in intervention_list])

cfg["meta"]["model"] = SEIRCTODEMem
defaults = {}
defaults.update(cfg["initial"])
defaults.update(cfg["parameters"])

graph_end_date = st.sidebar.date_input("Graph End",
                                     value=(start+timedelta(days=cfg['meta']['tmax'])))

graph_ending = (graph_end_date-start).days

if not triggers:
    for i in cfg['interventions']:
        if i['name' ] == "Lockdown Trigger":
            i['after'] = 900 #Just make them never happen

if end_shutdown:
    for i in cfg['interventions']:
        if i['name' ]== "Relax Lockdown":
            i['time'] = (end_date-start).days+i['delay']
        if triggers: # This works now.
            if i['name'] == "Lockdown Trigger":
                i['after'] = (end_date - start).days
        # But lockdowns don't always trigger at first...

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
    ax.set_xlim([0, graph_ending])
    ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))
    ax.xaxis.set_major_formatter(FuncFormatter(date_fmt))
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    # ax.set_xlim([70, ax.get_xlim()[1]])
    ax.set_xlabel('Date')
    ax.set_ylabel('People')
    maxy = ax.get_ylim()[1]
    # st.write(str(maxy))
    ax_r = ax.twinx()  # instantiate a second axes that shares the same x-axis

    if Graph_Interventions:
        intervention_lines = [(i['time'], i['parameters']['c']) for i in cfg['interventions'] if
                              ('c' in i['parameters'].keys() and i['name'] != 'Flu' and 'time' in i.keys())]
        intervention_lines_2 = [(i['time'], i['parameters']['c']) for i in events]
        intervention_lines.extend(intervention_lines_2)
        #Cantact Rate items for colors
        c_min = min([c['parameters']['c'] for c in cfg['interventions'] if 'c' in c['parameters']])
        c_max = max([c['parameters']['c'] for c in cfg['interventions'] if 'c' in c['parameters']])
        c_midpoint = 5.5
        # for i in intervention_lines:
        #     c = i[1]
        #     plt.plot([i[0], i[0]], [0, maxy], lw=1.25, ls='--',  # c=(1, (c - c_min)/(c_midpoint-c_min), 0))
        #              c=(min((c_max - c) / (c_max - c_midpoint), 1), min((c - c_min)/(c_midpoint-c_min), 1), 0))
        #     else: # Shouldn't fix this, should use correct value
        #         plt.plot([i[0], i[0]], [0, maxy], lw=1.25, ls='--', c=((c_max - c) / (c_max - c_midpoint), 1, 0))
        Begin = 0
        c = c_max
        for i in intervention_lines:
            End = i[0]
            #st.write(Begin, End, 3*(t[1]/full))
            ax_r.plot([Begin, End], [-.35, -.35], lw=2, ls=':',
                      c=(min((c_max - c) / (c_max - c_midpoint), 1), min((c - c_min)/(c_midpoint-c_min), 1), 0))
            c = i[1]
            Begin = End
        ax_r.plot([Begin, ax_r.get_xlim()[1]], [-.35, -.35], lw=2, ls=':',
                  c=(min((c_max - c) / (c_max - c_midpoint), 1), min((c - c_min) / (c_midpoint - c_min), 1), 0))

    ax.legend(To_Graph, loc='upper center')
    ax_r.set_ylabel('Reproductive Number (Effective)')
    ax_r.plot(traj[:, -1], label="R(t)", color="Black")
    ax_r.set_ylim([-.5, 5])
    ax.set_ylim([ax.get_ylim()[0]-(ax.get_ylim()[1]-ax.get_ylim()[0])/20, ax.get_ylim()[1]]) #Give room for the indicators
    if Graph_Interventions:
        if TTI != 'None':
            ax_r.legend([Line2D([0], [0], c="Black", lw=1, ls='-'), Line2D([0], [0], c="Grey", lw=2.75, ls=':'),
                              Line2D([0], [0], c=(1, 0, 0), lw=1.25, ls='--'), Line2D([0], [0], c=(0, 1, 0), lw=1.25, ls='--')],
                             ["R(t)", "Test and Trace", "Economy Closed", "Economy Opened"], loc='upper right')
            # Actually Graph TTI startup now.
            times = [(i['time'], i['parameters']['tested'] if "tested" in i['parameters'] else i['parameters']['testedBase']) for i in cfg['interventions'] if ("Testing" in i['name'])]
            #st.write(times)
            start = min([time[0] for time in times])
            full = max([T[1] for T in times])
            #st.write(full)
            Begin = start
            for t in times: # Plot segments for TTI Ramp-up.
                End = t[0]
                #st.write(Begin, End, 3*(t[1]/full))
                ax_r.plot([Begin, End], [-.15, -.15], lw=3*(t[1]/full), ls=':', c="Grey")
                Begin = End
            ax_r.plot([Begin, ax.get_xlim()[1]*.955], [-.15, -.15], lw=3, ls=':', c="Grey")
        else:
            ax_r.legend([Line2D([0], [0], c="Black", lw=1, ls='-'),
                         Line2D([0], [0], c=(1, 0, 0), lw=1.25, ls='--'),
                         Line2D([0], [0], c=(0, 1, 0), lw=1.25, ls='--')],
                        ["R(t)", "Close Economy", "Open Economy"], loc='upper right')

    else:
        ax_r.legend([Line2D([0], [0], c="Black", lw=1, ls='-')], ["R(t)"], loc='upper right')

    st.pyplot()


#Econ Outputs / Graph:
st.write("Total COVID-19 Deaths: " + f"{int(round(econ['Medical']['Deaths'],0)):,}")
st.write("Total Economic Loss from COVID-19: " + f"{round(econ['Economic']['Total_Productivity_Loss']/1000000000):,}" + " billion GBP")
st.write("")
st.write("Test and Trace Results:")
st.write("Maximum Tracers Needed: " + f"{round(econ['Tracing']['Max_Tracers'])}")
st.write("Total Tracer Budget: " + f"{round(econ['Tracing']['Tracing_Total_Costs']/1000000):,}" + " million GBP")
st.write("Total Testing Budget: " + f"{round(econ['Testing']['Testing_Total_Costs']/1000000) :,}" + " million GBP")

# st.write(str(econ))
