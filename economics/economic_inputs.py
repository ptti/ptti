
econ_inputs = dict()

# Parameters
# econ_inputs['Population'] = 67886011 # From scenario

econ_inputs['Shutdown'] = dict()
econ_inputs['Shutdown']['UK_Shutdown_GDP_Penalty'] = 0.08  # How much economic damage is happening? 8% reduction for c=4, shutdown.
econ_inputs['Shutdown']['UK_Open_Contacts'] = 13  # Base level
econ_inputs['Shutdown']['UK_Shutdown_Contacts'] = 3.9  # Shutdown level
econ_inputs['Shutdown']['UK_GDP_Monthly'] = 186000000000


# We will (potentially) model several possible interventions, with different costs.
# Tracing alone, universal testing + tracing, or partial / scaled testing + tracing.
# In each case, we need to compute costs from

econ_inputs['Trace'] = dict()
econ_inputs['Trace']['Time_to_Trace_Contact'] = 2.8 / 8.0  # 2.8 hours to trace each contact
#Pct_Symptomatic = 0.5

# Hire_Interval = 90 # Now Unused



# Variable Tracing Costs
econ_inputs['Trace']['Phone_Credit_Costs'] = 5 # Daily, per person.

# Max_Number_of_Tracers = UK_Population/1000
econ_inputs['Trace']['Cost_per_Tracer'] = 0
econ_inputs['Trace']['Tracer_Salary'] = 80  # Daily
econ_inputs['Trace']['Cost_per_Tracer'] += econ_inputs['Trace']['Tracer_Salary']
# We need to add the *daily* cost for other factors
econ_inputs['Trace']['Cost_per_Tracer'] += econ_inputs['Trace']['Phone_Credit_Costs'] # Add phone costs


# Number_of_Tracing_Supervisors = Max_Number_of_Tracers/50
econ_inputs['Trace']['Tracing_Supervisor_Salary'] = 160  # Daily
econ_inputs['Trace']['Tracers_Per_Supervisor'] = 50  # Daily
econ_inputs['Trace']['Number_of_Tracing_Team_Leads'] = 343
econ_inputs['Trace']['Team_Lead_Salary'] = 300  # Daily

econ_inputs['Trace']['Hiring_Cost'] = 200  # £200 per recruitment for advertisements, phone interviews, salary of recruiters

econ_inputs['Trace']['Tracer_Training_Course_Cost'] = 72000  # Three training courses (including refreshers) one for each staff cadre


# Tracers_Day_N = Max_Number_of_Tracers # This can vary. Set to max for now. (This is overridden in the econ model now.)
# We assume supervisors and team leads are employed the entire time we do this, regardless of varying number of tracers.

econ_inputs['Trace']['Tracing_App_Development_Deployment'] = 10000000  # ball park estimate of developing, maintenance & running app for 1 year

econ_inputs['Trace']['Cost_Per_Extra_Phones_for_Tracers'] = 200  # For any tracers without phones / replacements.
econ_inputs['Trace']['Tracer_Percentage_Needing_Phones'] = 0.1  # Fairly small percentage.
econ_inputs['Trace']['Tracers_Per_Infected_Person'] = 58.0/8 # See report - 58 hours, tracers work 8 hour days.

econ_inputs['Trace']['Rural_Pct'] = 0.17
econ_inputs['Trace']['Daily_Travel_Cost'] = 10
# Travelers = (Max_Number_of_Tracers * Rural_Pct) + Number_of_Tracing_Supervisors + Number_of_Tracing_Team_Leads

econ_inputs['Trace']['Tracing_Daily_Public_Communications_Costs'] = 100000 #Messaging, etc.



# Testing Costs

# PCR Machine Capabilities

econ_inputs['Test'] = dict()

econ_inputs['Test']['PCR_Machines_Per_Lab'] = 10
econ_inputs['Test']['Shifts_per_Day'] = 2
econ_inputs['Test']['Hours_per_Shift'] = 9
econ_inputs['Test']['Time_per_Batch'] = 0.5  # Half Hour batches
econ_inputs['Test']['Tests_per_Batch'] = 96
econ_inputs['Test']['Tests_per_Machine_per_Hour'] = econ_inputs['Test']['Tests_per_Batch'] / econ_inputs['Test']['Time_per_Batch']
econ_inputs['Test']['Tests_per_Machine_per_Shift'] = econ_inputs['Test']['Tests_per_Machine_per_Hour'] * econ_inputs['Test']['Hours_per_Shift']
econ_inputs['Test']['Tests_per_Machine_per_Day'] = econ_inputs['Test']['Tests_per_Machine_per_Shift'] * econ_inputs['Test']['Shifts_per_Day']

econ_inputs['Test']['Lab_Techs_Per_Machine_Per_Shift'] = 2 # One to run the test, one to fill the wells.

#Personnel Costs
# Moved to Econ Model
# Lab_supervisors	= Needed_Labs
# Max_Lab_Techs = Needed_PCR_Machines * Lab_Techs_Per_Machine_Per_Shift * Shifts_per_Day
# Lab_staff_trainings = Max_Lab_Techs + Lab_supervisors # Retrainings every 3 months?

econ_inputs['Test']['Lab_Tech_Salary'] = 200  # Per Shift
econ_inputs['Test']['Lab_Supervisor_Salary'] = 300  # Per Day
econ_inputs['Test']['Staff_Training_Cost'] = 200  # Trainings / retrainings every Period, per person.

econ_inputs['Test']['Cost_Per_PCR_Test'] = 4  # 3.50 for testing supplies, 0.50 for swab.


# Setup / Fixed Costs
econ_inputs['Test']['Lab_Overhead_Cost_Daily'] = 500  # Estimated cost of £500 per day per lab for 289 labs with 10 RT LAMP PCR machines each
econ_inputs['Test']['PCR_Machines_Cost'] = 27000 #  Roche COBAS 8800 Machines, as suggested by: https://www.bmj.com/content/368/bmj.m1163
econ_inputs['Test']['PCR_Machine_Daily_Maintenance'] = 10  # assume maintenance costs averaging £10 per day

import yaml
with open(r'economics\economic-inputs.yaml', 'w') as file:
    documents = yaml.dump(econ_inputs, file)
    file.close()