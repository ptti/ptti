from ptti.config import config_load
from ptti.model import runModel
from ptti.economic import calcEconOutputs, calcArgumentsODE
from ptti.seirct_ode import SEIRCTODEMem
from ptti.fit import dgu, dgu_cases
from datetime import date, datetime, timedelta
import os
from math import log
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
from pandas import DataFrame as pd_df
import streamlit as st

if 'app' not in os.getcwd():
    os.chdir('app')

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
    suffix  = ["B", "M", "k", "" , "m" , "u", "n"  ]
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


def fmt_ax(ax): # Perform all axis formatting operations
    ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))
    ax.xaxis.set_major_formatter(FuncFormatter(date_fmt))
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    # ax.set_xlim([70, ax.get_xlim()[1]])
    ax.set_xlabel('Date')
    return


st.title("UK COVID-19 Policy Simulator")
st.markdown(
    """
Compare COVID-19 control policies in the UK using the  [PTTI](https://github.com/ptti/ptti) model.
"""
)
st.sidebar.title("COVID-19 Policy Choices")


HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""

cfg = config_load(os.path.join("..", "examples", "structured", "ptti-past.yaml")) # To pull basics - actual load below.
start = date(int(cfg['meta']['start'][0:4]), int(cfg['meta']['start'][5:7]), int(cfg['meta']['start'][8:10]))

cfg_1 = os.path.join("..", "examples", "bowie", "cal2809test8dur5eta9chi9.yaml") # Need High / Low Compliance.
cfg_2 = os.path.join("..", "examples", "bowie", "recal5_dur7_lock10beta23c167pow16mob1.yaml")
cfg_3 = os.path.join("..", "examples", "bowie", "recal2809dur7beta23c167pow16hols155.yaml")

Scenario = st.sidebar.radio("Scenario to use", ['Scenario 1','Scenario 2','Scenario 3'], index=0)

if Scenario == 'Scenario 1':
    cfg = config_load(cfg_1)
elif Scenario == 'Scenario 2':
    cfg = config_load(cfg_2)
elif Scenario == 'Scenario 3':
    cfg = config_load(cfg_3)


st.sidebar.text("Display Options")
fixed_y = st.sidebar.checkbox("Fixed maximum y-axis")
log_y = st.sidebar.checkbox("Log-scale y-axis")


Scenario_Title = Scenario


#cfg2 = config_load(filename=os.path.join("..", "examples", "scenarios", "ptti-2_Universal_PTTI.yaml"))

cfg["meta"]["model"] = SEIRCTODEMem
defaults = {}
defaults.update(cfg["initial"])
defaults.update(cfg["parameters"])



# Now fix overlapping day issues:
intervention_times = [i['time'] for i in cfg['interventions'] if 'time' in i.keys()]
duplicates = [x for n, x in enumerate(intervention_times) if x in intervention_times[:n]]

for i in cfg['interventions']:
    if 'time' in i.keys():
        if i['time'] in duplicates:
            for i_dup in cfg['interventions']:
                if i_dup != i:
                    if 'time' in i_dup.keys():
                        if i['time'] == i_dup['time']:
                            i['parameters'].update(i_dup['parameters'])
                            i['name'] = i['name'] + " " + i_dup['name']
                            cfg['interventions'].remove(i_dup)

for i in cfg['interventions']: #Run a second time to clean up a weird issue.
    if 'time' in i.keys():
        if i['time'] in duplicates:
            for i_dup in cfg['interventions']:
                if i_dup != i:
                    if 'time' in i_dup.keys():
                        if i['time'] == i_dup['time']:
                            i['parameters'].update(i_dup['parameters'])
                            i['name'] = i['name'] + " " + i_dup['name']
                            cfg['interventions'].remove(i_dup)

cfg['interventions'].sort(key=lambda k: ("time" not in k, k.get("time", 100000))) #Otherwise, time changes can make things go backwards.


graph_end_date = st.sidebar.date_input("Graph End",
                                     value=(start+timedelta(days=cfg['meta']['tmax'])))
graph_ending = (graph_end_date-start).days

Graph_Interventions = st.sidebar.checkbox("Graph Interventions", value=True)
Graph_Rt = st.sidebar.checkbox("Graph R_t", value=True)
# Graph_Economics = st.sidebar.checkbox("Graph Economics", value=True)

# To_Graph = ["Exposed", "Infected", "Recovered"]
To_Graph = st.sidebar.multiselect("Outcomes To Plot", ["Susceptible", "Exposed", "Infectious", "Recovered", "Isolated", "Dead", "Death Data"],
                                  default=["Infectious", "Isolated", "Dead", "Death Data"])

Graph_Columns = {
  "Susceptible": ["SU", "SD"],
  "Exposed": ["EU", "ED"],
  "Infectious": ["IU", "ID"],
  "Removed": ["RU", "RD"],
  "Isolated": ["SD", "ED", "ID", "RD"],
  "Dead": ["M"]
}



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
#Latest_run = True

econ_args = calcArgumentsODE(traj, paramtraj, cfg)
# econ = calcEconOutputs(**econ_args)
#Update_Graph=True
# st.write(str(events))

#st.write(paramtraj['theta_U'])

if len(To_Graph)>0:
    pop = cfg['initial']['N']
    df_plot_results = pd_df()
    Out_Columns = [col['name'] for col in cfg['meta']['model'].observables]
    for Compartment in To_Graph:
        if Compartment not in Graph_Columns: continue ## data columns do not appear as compartments
        C_list = Graph_Columns[Compartment]
        C_total = list()
        for x in traj:
            C_total.append(abs(sum([x[cfg['meta']['model'].colindex(c) + 1] for c in C_list])))

        df_plot_results[Compartment] = C_total.copy()

    # if Graph_Economics:
    #     fig, (ax, ax_e) = plt.subplots(2,1, figsize=(6.4,10))
    #     fig.subplots_adjust(top=0.95, hspace=0.3) # More space between
    # else:
    fig,ax = plt.subplots()

    ## add data
    #cases = dgu_cases("coronavirus-cases_latest.csv")
    #first_case = cases[0,0]
    #last_case = cases[-1,0]
    #caseplot = np.pad(cases[:,1], (first_case - 1, len(df_plot_results) - last_case), mode="edge")
    #df_plot_results["Case Data"] = caseplot
    deaths = dgu("coronavirus-deaths_latest.csv")
    first_death = deaths[0,0]
    last_death  = deaths[-1,0]
    deathplot = np.pad(deaths[:,1], (first_death-1, len(df_plot_results) - last_death), mode="edge")
    df_plot_results["Death Data"] = deathplot

    ax.plot(df_plot_results)
    ax.set_xlim([0, graph_ending])
    fmt_ax(ax)
    ax.set_ylabel('People')
    miny = ax.get_ylim()[0]
    if log_y:
        ax.semilogy()
        miny = 1
    elif Graph_Interventions:
        miny = ax.get_ylim()[0]-300000
    if fixed_y:
        maxy = 3000000 # 3m.
        ax.set_ylim(miny, maxy)
    maxy = ax.get_ylim()[1]
    # st.write(str(maxy))
    ax_r = ax.twinx()  # instantiate a second axes that shares the same x-axis

    # if Graph_Interventions:
    #     intervention_lines = [(i['time'], i['parameters']['c']) for i in cfg['interventions'] if
    #                           ('c' in i['parameters'].keys() and i['name'] != 'Flu' and 'time' in i.keys())]
    #     intervention_lines_2 = [(i['time'], i['parameters']['c']) for i in events]
    #     intervention_lines.extend(intervention_lines_2)
    #     #Cantact Rate items for colors
    #     c_min = min([c['parameters']['c'] for c in cfg['interventions'] if 'c' in c['parameters']])
    #     c_max = max([c['parameters']['c'] for c in cfg['interventions'] if 'c' in c['parameters']])
    #     c_midpoint = 5.5
    #     # for i in intervention_lines:
    #     #     c = i[1]
    #     #     plt.plot([i[0], i[0]], [0, maxy], lw=1.25, ls='--',  # c=(1, (c - c_min)/(c_midpoint-c_min), 0))
    #     #              c=(min((c_max - c) / (c_max - c_midpoint), 1), min((c - c_min)/(c_midpoint-c_min), 1), 0))
    #     #     else: # Shouldn't fix this, should use correct value
    #     #         plt.plot([i[0], i[0]], [0, maxy], lw=1.25, ls='--', c=((c_max - c) / (c_max - c_midpoint), 1, 0))
    #     Begin = 0
    #     c = c_max
    #     for i in intervention_lines:
    #         End = i[0]
    #         #st.write(Begin, End, 3*(t[1]/full))
    #         ax_r.plot([Begin, End], [-.35, -.35], lw=2, ls=':',
    #                   c=(min((c_max - c) / (c_max - c_midpoint), 1), min((c - c_min)/(c_midpoint-c_min), 1), 0))
    #         c = i[1]
    #         Begin = End
    #     ax_r.plot([Begin, ax_r.get_xlim()[1]], [-.35, -.35], lw=2, ls=':',
    #               c=(min((c_max - c) / (c_max - c_midpoint), 1), min((c - c_min) / (c_midpoint - c_min), 1), 0))

    plt.suptitle(t=Scenario_Title)
    #plt.title()
    ax.legend(To_Graph, loc='upper center')
    if Graph_Rt:
        ax_r.set_ylabel('Reproductive Number (Effective)')
        ax_r.plot(traj[:, -1], label="R(t)", color="Black")
    ax_r.set_ylim([-.5, 5])
    ax.set_ylim([ax.get_ylim()[0]-(ax.get_ylim()[1]-ax.get_ylim()[0])/20, ax.get_ylim()[1]]) #Give room for the indicators
    if Graph_Interventions:
        if Graph_Rt:
            ax_r.legend([Line2D([0], [0], c="Black", lw=1, ls='-'),
                          Line2D([0], [0], c=(1, 0, 0), lw=1.25, ls='--'), Line2D([0], [0], c=(0, 1, 0), lw=1.25, ls='--')],
                         ["R(t)", "Economy Closed", "Economy Opened"], loc='upper right')
        else:
            ax_r.legend([Line2D([0], [0], c=(1, 0, 0), lw=1.25, ls='--'),
                         Line2D([0], [0], c=(0, 1, 0), lw=1.25, ls='--')],
                        ["Economy Closed", "Economy Opened"], loc='upper right')

    elif Graph_Rt:
        ax_r.legend([Line2D([0], [0], c="Black", lw=1, ls='-')], ["R(t)"], loc='upper right')

    # if round(econ['Tracing']['Max_Tracers'])>1000000: # Infeasible Number of Tracers.
    #     plt.text(0.025, 0.965, 'Tracing Program \n Infeasibly Large', horizontalalignment='left',
    #              verticalalignment='top', transform=ax_r.transAxes,bbox=dict(facecolor='red', alpha=0.5))

    # if Graph_Economics:
    #     cost_tracing = econ['Daily']['Tracing']
    #     cost_testing = econ['Daily']['Testing']
    #     cost_nhs     = econ['Daily']['NHS']
    #     cost_loss    = econ['Daily']['Productivity_Loss']
    #     ax_e.plot(cost_tracing, label='Tracing')
    #     ax_e.plot(cost_testing, label='Testing')
    #     ax_e.plot(cost_nhs, label='NHS')
    #     ax_e.plot(cost_loss, label='GDP')
    #
    #     fmt_ax(ax_e)
    #     ax_e.set_ylabel('Daily Cost (£)')
    #     ax_e.legend(loc='upper right')

    st.pyplot()


#Debug:
#st.write(intervention_list)
#st.write(cfg['interventions'])
#st.write("Chi:" + str(TTI_chi) )
#st.write("Chi_T:" + str(TTI_chi_trans) )
# st.write(str(econ))

from math import log10, floor
def round_sigfigs(x,n,i=False):
    if i:
        return int(round(x, int(floor(log10(abs(x))))*-1+(n-1)))
    else:
        if x != 0:
            return round(x, int(floor(log10(abs(x)))) * -1 + (n - 1))
        else:
            return 0

#Econ Outputs / Graph:
# st.write("Total COVID-19 Deaths: " + f"{int(round_sigfigs(econ['Medical']['Deaths'],2)):,}")
# st.write("Total Economic Loss from COVID-19: " + f"{round_sigfigs(econ['Economic']['Total_Productivity_Loss']/1000000000,3, True):,}" + " billion GBP")
# st.write("")
# st.write("TTI Results:")
# if econ['Tracing']['Tracing_Total_Costs'] < 1: # No costs.
#     st.write("No Tracing")
# else:
#     st.write("Total Tracer Budget: " + f"{round_sigfigs(econ['Tracing']['Tracing_Total_Costs']/1000000000,2):,}" + " billion GBP")
#     st.write("Maximum Tracers Needed: " + f"{round_sigfigs(econ['Tracing']['Max_Tracers']/1000,2,True)}" + " thousand")
# st.write("Total Testing Budget: " + f"{round_sigfigs(econ['Testing']['Testing_Total_Costs']/1000000000,3) :,}" + " billion GBP")
# if econ['Testing']['Max_Laboratories']*10*2*9*2*96 > 1000000:
#     st.write("Maximum Daily Tests: " + f"{int(round_sigfigs(econ['Testing']['Max_Laboratories']*10*2*9*2*96,2,True)/1000000) :,}" + " million")
# else:
#     st.write(
#         "Maximum Daily Tests: " + f"{int(round_sigfigs(econ['Testing']['Max_Laboratories'] * 10 * 2 * 9 * 2 * 96, 2) / 1000) :,}" + " thousand")
# st.write(econ['Economic']['tests'])

# st.write(cfg)
