import numpy as np
from scipy.interpolate import interp1d
from ptti.economic_data import econ_inputs

# def _calcTT(data):

#     theta = np.array(data['variables']['theta'])
#     c = np.array(data['variables']['c'])
#     gamma = np.array(data['variables']['gamma'])
#     chi = np.array(data['variables']['chi'])
#     eta = np.array(data['variables']['eta'])
#     IU = np.array(data['compartments'][:, 4])

#     return theta*IU, c*theta/(gamma+theta*(1+eta*chi))*IU

# def calcEconNew(time, trajectory, parameters, scenario):

#     Output = {}
#     Output['policy'] = scenario
#     Output['timesteps'] = time
#     Output['compartments'] = trajectory
#     Output['variables'] = dict(parameters)

#     # Compute daily amount of testing and tracing
#     Tested_TimeSeries, Traced_TimeSeries = _calcTraced(Output)

# Calculate the arguments of calcEconOutputs for the SEIRCT_ODE model


def calcArgumentsODE(traj, paramtraj, cfg):

    # First, get the time
    time = traj[:, 0]
    traj = traj[:, 1:]

    # Make it an integer time axis
    min_day = int(np.ceil(time[0]))
    max_day = int(np.floor(time[-1]))

    days = np.arange(min_day, max_day+1)

    # Now get the relevant bits of trajectory
    model = cfg['meta']['model']

    cpm = {}
    par = {}
    for c in ('SU', 'SD', 'EU', 'ED', 'IU', 'ID', 'RU', 'RD'):
        i = model.colindex(c)
        cpm[c] = interp1d(time, traj[:, i], kind='nearest')(days)
    for p in ('theta', 'c', 'eta', 'gamma', 'chi', 'testedBase'):
        traj = paramtraj.get(p)
        if traj is not None:
            par[p] = interp1d(time, traj, kind='nearest')(days)
        else:
            par[p] = np.zeros(len(days))

    ## Some useful compound quantities
    # average infectious time, used to work out how many contacts are traced
    avg_inftime = 1.0/(par['gamma']+par['theta']*(1+par['eta']*par['chi']))

    # Now derive the relevant quantities
    args = {'time': days}
    args['contacts'] = par['c']
    args['tested'] = cpm['IU']*par['theta'] + (cpm['SU']+cpm['EU']+cpm['RU'])*par['testedBase']
    # traced are: the number of contacts of infectives that have been tested - IF tracing is done, i.e. if chi > 0.
    args['traced'] = cpm['IU']*par['theta']*par['c']*avg_inftime * (par['chi'] > 0)
    args['recovered'] = cpm['RU']+cpm['RD']
    args['infected'] = cpm['IU']+cpm['ID']
    args['isolated'] = cpm['SD'] + cpm['ED'] + cpm['ID'] + cpm['RD']
    args['population'] = cfg['initial']['N']

    return args


def calcEconOutputs(time, contacts, infected, recovered, tested, traced, isolated, population):

    output = {}
    days = len(time)

    # Tracing
    bw = int(econ_inputs['Trace']['Tracer_Contract_Length'])
    # Split by blocks
    tracing_blocks = []
    for i0 in range(0, days, bw):
        tblock = traced[i0:i0+bw]
        # Tracers needed?
        maxt = max(tblock)*econ_inputs['Trace']['Time_to_Trace_Contact']
        tracing_blocks.append((i0, len(tblock), int(np.ceil(maxt))))

    max_supervisors = 0
    max_tracers = 0

    tracing_costs = []
    for i0, n, tracers in tracing_blocks:
        supervisors = int(np.ceil(tracers/econ_inputs['Trace']['Tracers_Per_Supervisor']))
        new_supervisors = max(supervisors-max_supervisors, 0)
        max_supervisors += new_supervisors

        new_tracers = max(tracers-max_tracers, 0)
        max_tracers += new_tracers

        # Hiring costs
        costs = (new_tracers+new_supervisors)*econ_inputs['Trace']['Tracer_Initial_Cost']

        # Daily costs
        costs += (max_supervisors*econ_inputs['Trace']['Supervisor_Daily_Cost'] +
                  tracers*econ_inputs['Trace']['Tracer_Daily_Cost'] +
                  econ_inputs['Trace']['Total_Team_Lead_Daily_Cost'] +
                  econ_inputs['Trace']['Tracing_Daily_Public_Communications_Costs'])*n

        tracing_costs.append(costs)

    # Add the startup cost for team leads
    tracing_costs[0] += econ_inputs['Trace']['Number_of_Tracing_Team_Leads']*econ_inputs['Trace']['Tracer_Initial_Cost']
    # And tracing app
    tracing_costs[0] += econ_inputs['Trace']['Tracing_App_Development_Deployment']

    # All of this only applies if we have tracing at all...
    if max(traced) == 0:
        tracing_costs = [0 for tc in tracing_costs]
        print("No Tracing! -- No Tracing! -- No Tracing! -- No Tracing! -- No Tracing! -- No Tracing! -- No Tracing!")

    output['Tracing'] = {}
    output['Tracing']['Tracing_Block_Lengths'] = [tb[1] for tb in tracing_blocks]
    output['Tracing']['Tracers'] = [tb[2] for tb in tracing_blocks]
    output['Tracing']['Max_Tracers'] = max_tracers
    output['Tracing']['Max_Supervisors'] = max_supervisors
    output['Tracing']['Tracing_Costs'] = tracing_costs
    output['Tracing']['Tracing_Total_Costs'] = sum(tracing_costs)

    # Testing
    bw = int(econ_inputs['Test']['Tester_Contract_Length'])
    # Split by blocks
    testing_blocks = []
    for i0 in range(0, days, bw):
        tblock = tested[i0:i0+bw]
        # Laboratories needed?
        labs = max(tblock)*econ_inputs['Test']['Lab_Peaktest_Ratio']
        testing_blocks.append((i0, len(tblock), int(np.ceil(labs))))

    max_labs = 0

    testing_costs = []
    for i0, n, labs in testing_blocks:
        new_labs = max(labs-max_labs, 0)
        max_labs += new_labs

        # Startup costs
        costs = new_labs*econ_inputs['Test']['Lab_Startup_Cost']
        # Daily costs
        costs += (max_labs*econ_inputs['Test']['Lab_NonTechs_Daily_Cost'] +
                  labs*econ_inputs['Test']['Lab_Techs_Daily_Cost'])*n
        # Sum up the tests in this block
        costs += sum(tested[i0:i0+n] * econ_inputs['Test']['Cost_Per_PCR_Test'])

        testing_costs.append(costs)

    if max(tested) == 0:
        testing_costs = [0 for tc in testing_costs]

    output['Testing'] = {}
    output['Testing']['Testing_Block_Lengths'] = [tb[1] for tb in testing_blocks]
    output['Testing']['Laboratories'] = [tb[2] for tb in testing_blocks]
    output['Testing']['Max_Laboratories'] = max_labs
    output['Testing']['Testing_Costs'] = testing_costs
    output['Testing']['Testing_Total_Costs'] = sum(testing_costs)

    # Deaths and other outcomes
    deaths = recovered[-1]*econ_inputs['Medical']['IFR']
    icu = recovered[-1]*econ_inputs['Medical']['ICU_Fraction']
    hospital = recovered[-1]*econ_inputs['Medical']['Hospitalised_Fraction'] - recovered[-1]*econ_inputs['Medical']['ICU_Fraction']  # Hospital non-ICU
    cases = recovered[-1] - deaths - hospital - icu
    daily_nhs_costs = recovered*econ_inputs['Medical']['Total_NHS_Cost_Per_Recovered']
    nhs_costs = sum(daily_nhs_costs)
    #prod_costs = recovered[-1]*econ_inputs['Medical']['Total_Productivity_Loss_Per_Recovered']

    output['Medical'] = {}
    output['Medical']['Deaths'] = deaths
    output['Medical']['ICU'] = icu
    output['Medical']['Hospital'] = hospital  # Hospital non-ICU
    output['Medical']['Cases'] = cases

    # Economy Scales with contacts
    # Economy minimum is: econ_inputs['Shutdown']['UK_Shutdown_GDP_Penalty'], with econ_inputs['Shutdown']['UK_Shutdown_Contacts']
    # Full strength is 0 penalty at econ_inputs['Shutdown']['UK_Open_Contacts']
    Daily_GDP = []
    Daily_GDP_Base = econ_inputs['Shutdown']['UK_GDP_Monthly'] / 30
    Isolated_Fraction = isolated / population # Each person in isolation is a fraction of the economy fully closed.
    # print(Isolated_Fraction)

    Shutdown_Fraction = 1 - (contacts-econ_inputs['Shutdown']['UK_Shutdown_Contacts'])/(
        econ_inputs['Shutdown']['UK_Open_Contacts'] - econ_inputs['Shutdown']['UK_Shutdown_Contacts'])

    Daily_GDP = (1 - Shutdown_Fraction *
                 econ_inputs['Shutdown']['UK_Shutdown_GDP_Penalty'])*(1-Isolated_Fraction)*Daily_GDP_Base
    No_Pandemic_GDP = days * Daily_GDP_Base

    total_GDP = sum(Daily_GDP)


    output['Economic'] = {}
    output['Economic']['Total_NHS_Costs'] = nhs_costs
    output['Economic']['Contacts'] = contacts
    output['Economic']['Isolated'] = isolated
    output['Economic']['Total_Productivity_Loss'] = (No_Pandemic_GDP-total_GDP)

    # Compute daily costs
    output['Daily'] = {}

    output['Daily']['Tracing'] = []
    for block in range(len(output['Tracing']['Tracing_Block_Lengths'])):
        block_length = output['Tracing']['Tracing_Block_Lengths'][block]
        block_cost =  output['Tracing']['Tracing_Costs'][block]
        daily_cost = block_cost/block_length
        output['Daily']['Tracing'].extend([daily_cost]*block_length)

    output['Daily']['Testing'] = []
    for block in range(len(output['Testing']['Testing_Block_Lengths'])):
        block_length = output['Testing']['Testing_Block_Lengths'][block]
        block_cost =  output['Testing']['Testing_Costs'][block]
        daily_cost = block_cost/block_length
        output['Daily']['Testing'].extend([daily_cost]*block_length)

    output['Daily']['Tracing'] = np.array(output['Daily']['Tracing'])
    output['Daily']['Testing'] = np.array(output['Daily']['Testing'])
    output['Daily']['NHS'] = daily_nhs_costs
    output['Daily']['Productivity_Loss'] = Daily_GDP_Base - Daily_GDP

    return output


def calcEconOutputsOld(time, trajectory, parameters, scenario):

    locals().update(econ_inputs['Shutdown'])
    locals().update(econ_inputs['Test'])
    locals().update(econ_inputs['Trace'])

    Output = dict()
    Output['policy'] = scenario
    Output['timesteps'] = time
    Days = time[-1]-time[0]  # Total number of days modeled
    Output['compartments'] = trajectory

    Costs = 0

    Output['Economic'] = dict()
    Output['parameters'] = dict()
    Output['variables'] = dict(parameters)

    Output['I'] = [float(a + b) for a, b in zip(Output['compartments']
                                                [:, 4], Output['compartments'][:, 5])]

    # Compute tracing
    theta = np.array(Output['variables']['theta'])
    c = np.array(Output['variables']['c'])
    gamma = np.array(Output['variables']['gamma'])
    chi = np.array(Output['variables']['chi'])
    eta = np.array(Output['variables']['eta'])
    IU = np.array(Output['compartments'][:, 4])

    To_Trace = Output['compartments'][:, -2]  # note - brittle

    # Now we need to find the number of tracers needed in each window.
    Tracers_Needed_Per_Hiring_Window = []
    Period_Lengths = []
    Period_Starts = []
    Period_Ends = []
    Period_Start = 0

    # Two ways to do periods for hiring; per policy period, or per window. We can do both.
    period_history = np.array(parameters['period'])
    periods = sorted(list(set(period_history)))

    # Tracing hiring windows
    tracer_hiring_windows = np.floor(
        time/econ_inputs['Trace']['Tracer_Contract_Length']).astype(int)
    THW_Starts = []
    THW_Ends = []
    THW_Lengths = []

    Tracing_Costs_TimeSeries = np.zeros(len(time))

    for thw in range(max(tracer_hiring_windows)+1):
        THW_Indices = np.where(tracer_hiring_windows == thw)[0]
        THW_Start, THW_End = THW_Indices[[0, -1]]

        THW_Starts.append(THW_Start)
        THW_Ends.append(THW_End)

        if THW_End < len(time)-1:
            THW_End += 1
        THW_Lengths.append(float(time[THW_End]-time[THW_Start]))

        Tracers_This_Period = max(
            To_Trace[THW_Start:THW_End+1])*econ_inputs['Trace']['Time_to_Trace_Contact']
        Tracers_Needed_Per_Hiring_Window.append(Tracers_This_Period)

    for p in periods:
        Period_Start, Period_End = np.where(period_history == p)[0][[0, -1]]

        Period_Starts.append(Period_Start)
        Period_Ends.append(Period_End)
        Period_Lengths.append(float(time[Period_End] - time[Period_Start]))

    # We assume that each day, all people whose contacts can be traced have all contacts traced by a team.
    # This means to keep tracing on a one-day lag, i.e. by end of the next day,  we need enough people to trace
    # the maximum expected number in any one day during that period.
    Max_Tracers = max(Tracers_Needed_Per_Hiring_Window)

    # We assume we need supervisors full time, regardless of number of tracers at the time.
    Number_of_Tracing_Supervisors = Max_Tracers / \
        econ_inputs['Trace']['Tracers_Per_Supervisor']
    # The above now does a bunch of checking to get the numbers for tracers needed. Now we take the sum.
    Total_Max_Tracing_Workers = Number_of_Tracing_Supervisors + \
        econ_inputs['Trace']['Number_of_Tracing_Team_Leads'] + Max_Tracers
    Recruitment_Costs = econ_inputs['Trace']['Hiring_Cost'] * \
        Total_Max_Tracing_Workers

    Tracers_fixed_cost = (Number_of_Tracing_Supervisors * (econ_inputs['Trace']['Tracing_Supervisor_Salary'] + econ_inputs['Trace']['Phone_Credit_Costs']) * Days) + \
                         (econ_inputs['Trace']['Number_of_Tracing_Team_Leads'] * (econ_inputs['Trace']['Team_Lead_Salary'] + econ_inputs['Trace']['Phone_Credit_Costs']) * Days) + \
        Recruitment_Costs + econ_inputs['Trace']['Tracer_Training_Course_Cost'] + \
        econ_inputs['Trace']['Cost_Per_Extra_Phones_for_Tracers'] * \
        Total_Max_Tracing_Workers

    # These are paid up front
    Tracing_Costs_TimeSeries[0] += Tracers_fixed_cost

    Supervisor_Travel_Costs_Daily = econ_inputs['Trace']['Daily_Travel_Cost']*(
        Number_of_Tracing_Supervisors + econ_inputs['Trace']['Number_of_Tracing_Team_Leads'])
    econ_inputs['Trace']['Tracing_Worker_Travel_Costs'] = econ_inputs['Trace']['Daily_Travel_Cost'] * \
        econ_inputs['Trace']['Rural_Pct']  # Rural Tracers Travel Costs
    # Cost Per Tracer includes PHone credits.
    Tracer_Costs_Daily = econ_inputs['Trace']['Tracer_Salary'] + \
        econ_inputs['Trace']['Phone_Credit_Costs'] + \
        econ_inputs['Trace']['Tracing_Worker_Travel_Costs']

    # Constant all across the windows
    Tracing_Costs_TimeSeries += Supervisor_Travel_Costs_Daily

    Tracers_Cost = Supervisor_Travel_Costs_Daily*Days

    for ts, te, tn, tl in zip(THW_Starts, THW_Ends, Tracers_Needed_Per_Hiring_Window, THW_Lengths):
        # Travel costs
        Tracing_Costs_TimeSeries[ts:te+1] += Tracer_Costs_Daily*tn*tl/(te-ts+1)
        Tracers_Cost += Tracer_Costs_Daily*tn*tl

    # If zero, means there's no tracing at all!
    Uses_Tracing = bool(Max_Tracers > 0)

    Costs += Tracers_fixed_cost*Uses_Tracing
    Costs += Tracers_Cost*Uses_Tracing

    # Public communication
    Tracing_Costs_TimeSeries += econ_inputs['Trace']['Tracing_Daily_Public_Communications_Costs']
    Costs += econ_inputs['Trace']['Tracing_Daily_Public_Communications_Costs'] * \
        Days*Uses_Tracing

    # Now do the sum over periods
    Tracing_Costs_Per_Period = []
    for p in periods:
        Tracing_Costs_Per_Period.append(
            float(sum(np.where(period_history == p, Tracing_Costs_TimeSeries, 0))) *
            Uses_Tracing)

    # That is all costs from the original cost spreadsheet for Tracing.

    Trace_Outputs = dict()
    Trace_Outputs['Tracers_Needed_Per_Hiring_Window'] = list(
        map(float, Tracers_Needed_Per_Hiring_Window))
    Trace_Outputs['Hiring_Window_Lengths'] = THW_Lengths
    Trace_Outputs['Tracers_fixed_cost'] = Tracers_fixed_cost*Uses_Tracing
    Trace_Outputs['Tracers_cost'] = Tracers_Cost*Uses_Tracing
    Trace_Outputs['Tracer_Costs_Per_Period'] = Tracing_Costs_Per_Period

    # Testing Level is now set by Theta, as such:.
    # theta: 100000 / N
    Test_Outputs = dict()

    Testing_Costs = 0  # We will add to this.
    Testing_Costs_TimeSeries = np.zeros(len(time))

    Output['Economic']['tests'] = Output['policy']['initial']['N'] * theta

    Daily_tests = Output['Economic']['tests']  # Test needs over time.

    # This determines how many lab techs we need per period.
    Max_Tests_In_Hiring_Window = []
    Labs_Per_Window = []
    Maximum_tests = max(Daily_tests)

    # Testing hiring windows
    tester_hiring_windows = np.floor(
        time/econ_inputs['Test']['Tester_Contract_Length']).astype(int)
    TSHW_Starts = []
    TSHW_Ends = []
    TSHW_Lengths = []

    Testing_Labs_Per_Window = []
    Testing_Workers_Per_Window = []

    for tshw in range(max(tester_hiring_windows)+1):
        TSHW_Indices = np.where(tester_hiring_windows == tshw)[0]
        TSHW_Start, TSHW_End = TSHW_Indices[[0, -1]]

        TSHW_Starts.append(TSHW_Start)
        TSHW_Ends.append(TSHW_End)

        Window_Tests_max = max(Daily_tests[TSHW_Start:TSHW_End+1])
        Max_Tests_In_Hiring_Window.append(Window_Tests_max)
        Machines_Needed_In_Window = Window_Tests_max /  \
            econ_inputs['Test']['Tests_per_Machine_per_Day']
        Labs_Per_Window.append(Machines_Needed_In_Window /
                               econ_inputs['Test']['PCR_Machines_Per_Lab'])

        if TSHW_End < len(time)-1:
            TSHW_End += 1
        TSHW_Lengths.append(float(time[TSHW_End]-time[TSHW_Start]))

        Machines_In_Window = Window_Tests_max / \
            econ_inputs['Test']['Tests_per_Machine_per_Day']
        Labs_In_Window = Machines_In_Window / \
            econ_inputs['Test']['PCR_Machines_Per_Lab']
        Curr_Period_Days = TSHW_Lengths[-1]

        Testing_Costs += econ_inputs['Test']['Lab_Overhead_Cost_Daily'] * Labs_In_Window * \
            Curr_Period_Days
        Testing_Costs_TimeSeries[TSHW_Indices] += econ_inputs['Test']['Lab_Overhead_Cost_Daily'] * \
            Labs_In_Window * Curr_Period_Days/len(TSHW_Indices)

        # Labs in use are all fully staffed.
        # Staff Costs
        Supervisors = Labs_In_Window  # 1 Supervisor per lab.
        Testing_Costs += Supervisors * \
            econ_inputs['Test']['Lab_Supervisor_Salary'] * Curr_Period_Days

        Testing_Costs_TimeSeries[TSHW_Indices] += Supervisors * \
            econ_inputs['Test']['Lab_Supervisor_Salary'] * \
            Curr_Period_Days/len(TSHW_Indices)

        Daily_Lab_Workers = Labs_In_Window * econ_inputs['Test']['PCR_Machines_Per_Lab'] * econ_inputs['Test']['Shifts_per_Day'] * \
            econ_inputs['Test']['Lab_Techs_Per_Machine_Per_Shift']

        Testing_Costs += Daily_Lab_Workers * \
            econ_inputs['Test']['Lab_Tech_Salary']*Curr_Period_Days
        Testing_Costs_TimeSeries[TSHW_Indices] += Daily_Lab_Workers * \
            econ_inputs['Test']['Lab_Tech_Salary'] * \
            Curr_Period_Days/len(TSHW_Indices)

        Testing_Costs += Machines_In_Window * Curr_Period_Days * \
            econ_inputs['Test']['PCR_Machine_Daily_Maintenance']
        Testing_Costs_TimeSeries[TSHW_Indices] += Machines_In_Window * \
            econ_inputs['Test']['PCR_Machine_Daily_Maintenance'] * \
            Curr_Period_Days/len(TSHW_Indices)

        Testing_Labs_Per_Window.append(float(Labs_In_Window))
        Testing_Workers_Per_Window.append(float(Daily_Lab_Workers))

    # Fixed Testing Costs:
    Total_Required_PCR_Machines = max(
        Max_Tests_In_Hiring_Window) / (econ_inputs['Test']['Tests_per_Machine_per_Day'])
    # 1 Supervisor per lab.
    Max_Lab_Staff = Total_Required_PCR_Machines / \
        econ_inputs['Test']['PCR_Machines_Per_Lab']
    Max_Lab_Staff += Total_Required_PCR_Machines / \
        (econ_inputs['Test']['Shifts_per_Day'] *
         econ_inputs['Test']['Lab_Techs_Per_Machine_Per_Shift'])

    Testing_fixed_Costs = Total_Required_PCR_Machines * \
        econ_inputs['Test']['PCR_Machines_Cost']  # Buy Machines
    # Hire and Train Staff. One Time Cost.
    Testing_fixed_Costs += Max_Lab_Staff * \
        (econ_inputs['Trace']['Hiring_Cost'] +
         econ_inputs['Test']['Staff_Training_Cost'])

    Testing_Costs_TimeSeries[0] += Testing_fixed_Costs
    Testing_Costs += Testing_fixed_Costs

    Total_Required_Tests = np.trapz(Daily_tests, time)

    Testing_Costs_TimeSeries += Total_Required_Tests * \
        econ_inputs['Test']['Cost_Per_PCR_Test']/len(time)
    Testing_Costs += Total_Required_Tests * \
        econ_inputs['Test']['Cost_Per_PCR_Test']

    # Now do the sum over periods
    Testing_Costs_Per_Period = []
    for p in periods:
        Testing_Costs_Per_Period.append(
            float(sum(np.where(period_history == p, Testing_Costs_TimeSeries, 0))))

    Test_Outputs = dict()
    Test_Outputs['Max_Labs'] = Total_Required_PCR_Machines / \
        econ_inputs['Test']['PCR_Machines_Per_Lab']
    Test_Outputs['Hiring_Window_Lengths'] = TSHW_Lengths
    Test_Outputs['Max_Total_Staff'] = Max_Lab_Staff
    Test_Outputs['Testing_Labs_Per_Window'] = Testing_Labs_Per_Window
    Test_Outputs['Testing_Workers_Per_Window'] = Testing_Workers_Per_Window
    Test_Outputs['Total_Tests'] = Total_Required_Tests
    Test_Outputs['Total_Testing_Costs'] = Testing_Costs
    Test_Outputs['Testing_Costs_Per_Period'] = Testing_Costs_Per_Period

    Costs += Testing_Costs

    # Medical Outcomes
    # Because the R compartment is cumulative, we can take the final value as the total number of cases.
    Total_Resolved_Cases = Output['compartments'][-1,
                                                  6] + Output['compartments'][-1, 7]  # RU + RD
    locals().update(econ_inputs['Medical'])  # Retreive local variables
    Medical_Outcomes = dict()
    Medical_Outcomes['Cases'] = Total_Resolved_Cases
    Medical_Outcomes['Deaths'] = Total_Resolved_Cases * \
        econ_inputs['Medical']['IFR']

    In_Hospital_Deaths = econ_inputs['Medical']['Hospitalized_Pct_Deaths'] * \
        Medical_Outcomes['Deaths']

    # We work out number of hospitalizations backwards from data.
    # econ_inputs['Medical']['ICU_Pct'] of patients go to the ICU, and the fatality rate for those cases is econ_inputs['Medical']['ICU_Fatality'].
    # econ_inputs['Medical']['ICU_Pct'] * Hospital_Cases * econ_inputs['Medical']['ICU_Fatality'] + (1-econ_inputs['Medical']['ICU_Pct']) * Hospital_Cases * Non_econ_inputs['Medical']['ICU_Fatality'] = In_Hospital_Deaths.
    # Hospital_Cases = In_Hospital_Deaths / econ_inputs['Medical']['ICU_Pct'] * econ_inputs['Medical']['ICU_Fatality'] + (1-econ_inputs['Medical']['ICU_Pct']) * Non_econ_inputs['Medical']['ICU_Fatality']

    Medical_Outcomes['Hospital_Cases'] = In_Hospital_Deaths / (econ_inputs['Medical']['ICU_Pct']*econ_inputs['Medical']['ICU_Fatality'] +
                                                               (1-econ_inputs['Medical']['ICU_Pct']) * econ_inputs['Medical']['Non_ICU_Fatality'])
    Medical_Outcomes['ICU_Cases'] = Medical_Outcomes['Hospital_Cases'] * \
        econ_inputs['Medical']['ICU_Pct']

    Medical_Outcomes['NHS_Costs'] = Medical_Outcomes['Deaths'] * econ_inputs['Medical']['NHS_Death_Cost'] + \
        Medical_Outcomes['ICU_Cases'] * econ_inputs['Medical']['NHS_ICU_Cost'] + \
        Medical_Outcomes['Hospital_Cases'] * \
        econ_inputs['Medical']['NHS_Hospital_Cost']

    Medical_Outcomes['Productivity_Loss'] = Medical_Outcomes['Deaths'] * econ_inputs['Medical']['Productivity_Death_Cost'] + \
        Medical_Outcomes['ICU_Cases'] * econ_inputs['Medical']['Productivity_ICU_Cost'] + \
        Medical_Outcomes['Hospital_Cases'] * econ_inputs['Medical']['Productivity_Hospital_Cost'] + \
        Medical_Outcomes['Cases'] * econ_inputs['Medical']['Productivity_Symptomatic_Cost'] * \
        econ_inputs['Medical']['Pct_Symptomatic']

    Output['Medical'] = Medical_Outcomes

    # Now, calculate fraction of economy open.

    # Economy Scales with Output['variables']['c'].
    # Economy minimum is: econ_inputs['Shutdown']['UK_Shutdown_GDP_Penalty'], with econ_inputs['Shutdown']['UK_Shutdown_Contacts']
    # Full strength is 0 penalty at econ_inputs['Shutdown']['UK_Open_Contacts']
    Daily_GDP = []
    Economy_Fraction_Daily = []
    Daily_GDP_Base = econ_inputs['Shutdown']['UK_GDP_Monthly'] / 30
    Shutdown_Fraction = (c-econ_inputs['Shutdown']['UK_Shutdown_Contacts'])/(
        econ_inputs['Shutdown']['UK_Open_Contacts'] - econ_inputs['Shutdown']['UK_Shutdown_Contacts'])
    Economy_Fraction_Daily = 1-Shutdown_Fraction
    Daily_GDP = (1-Shutdown_Fraction *
                 econ_inputs['Shutdown']['UK_Shutdown_GDP_Penalty'])*Daily_GDP_Base

    Overall_Period_GDP = np.trapz(Daily_GDP, time)
    Full_Shutdown_GDP = Days * Daily_GDP_Base * \
        (1-econ_inputs['Shutdown']['UK_Shutdown_GDP_Penalty'])
    No_Pandemic_GDP = Days * Daily_GDP_Base

    Output['Economic']['GDP'] = dict()
    Output['Economic']['GDP']['Projected'] = Overall_Period_GDP
    Output['Economic']['GDP']['Reduction_from_Baseline'] = 1 - \
        (Overall_Period_GDP/No_Pandemic_GDP)
    Output['Economic']['GDP']['Benefit_over_Shutdown'] = Overall_Period_GDP - \
        Full_Shutdown_GDP
    Output['Economic']['Total_Costs'] = float(Costs)
    Output['Trace_Outputs'] = Trace_Outputs
    Output['Test_Outputs'] = Test_Outputs

    return Output  # What else is useful to graph / etc?
