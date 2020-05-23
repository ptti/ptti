import yaml
import numpy as np
from math import ceil, exp
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

def calcEconOutputs(time, trajectory, parameters, scenario):

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

    To_Trace = Output['compartments'][:,-2] ## note - brittle

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

    Uses_Tracing = bool(Max_Tracers > 0)  # If zero, means there's no tracing at all!

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
        Machines_Needed_In_Window = Window_Tests_max/  \
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
        Testing_Costs_TimeSeries[TSHW_Indices] += econ_inputs['Test']['Lab_Overhead_Cost_Daily'] * Labs_In_Window * Curr_Period_Days/len(TSHW_Indices)

        # Labs in use are all fully staffed.
        # Staff Costs
        Supervisors = Labs_In_Window  # 1 Supervisor per lab.
        Testing_Costs += Supervisors * \
            econ_inputs['Test']['Lab_Supervisor_Salary'] * Curr_Period_Days

        Testing_Costs_TimeSeries[TSHW_Indices] += Supervisors * \
            econ_inputs['Test']['Lab_Supervisor_Salary']*Curr_Period_Days/len(TSHW_Indices)

        Daily_Lab_Workers = Labs_In_Window * econ_inputs['Test']['PCR_Machines_Per_Lab'] * econ_inputs['Test']['Shifts_per_Day'] * \
            econ_inputs['Test']['Lab_Techs_Per_Machine_Per_Shift']

        Testing_Costs += Daily_Lab_Workers * \
            econ_inputs['Test']['Lab_Tech_Salary']*Curr_Period_Days
        Testing_Costs_TimeSeries[TSHW_Indices] += Daily_Lab_Workers*econ_inputs['Test']['Lab_Tech_Salary']*Curr_Period_Days/len(TSHW_Indices)

        Testing_Costs += econ_inputs['Test']['Staff_Training_Cost'] * \
            (Daily_Lab_Workers + Supervisors)  # Once Per Period
        Testing_Costs_TimeSeries[TSHW_Start] += econ_inputs['Test']['Staff_Training_Cost'] * \
            (Daily_Lab_Workers + Supervisors)

        Testing_Costs += Machines_In_Window * Curr_Period_Days * \
            econ_inputs['Test']['PCR_Machine_Daily_Maintenance']
        Testing_Costs_TimeSeries[TSHW_Indices] += Machines_In_Window  * \
            econ_inputs['Test']['PCR_Machine_Daily_Maintenance']*Curr_Period_Days/len(TSHW_Indices)

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
    # Hire Staff. One Time Cost.
    Testing_fixed_Costs += Max_Lab_Staff * econ_inputs['Trace']['Hiring_Cost']

    Testing_Costs_TimeSeries[0] += Testing_fixed_Costs
    Testing_Costs += Testing_fixed_Costs

    Total_Required_Tests = np.trapz(Daily_tests, time)

    Testing_Costs_TimeSeries += Total_Required_Tests*econ_inputs['Test']['Cost_Per_PCR_Test']/len(time)
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
