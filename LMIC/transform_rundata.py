import os
import xlsxwriter
from statistics import mean

directory = '20200620'
vals=[]
with open (os.path.join(directory, "lmic-cases.tsv")) as f:
    cols = f.readline().split(sep='\t')
    for line in f:
        vals.append(line.split(sep='\t'))

Pop_Size = 100000
IFR = 0.01
Casenames={}

for line in vals:
    Casenames[str(int(line[0])+1)] = ('High' if line[1]=='1000.0' else ('Moderate' if line[1]=='100.0' else 'Low')) + ' COVID-19 Prevalence,' #INIT_I
    Casenames[str(int(line[0])+1)] += ((' Slow' if line[2]=='12' else ' Rapid') + ' Test with') # k_result
    Casenames[str(int(line[0])+1)] += ((' Unlimited' if line[3] == '500' else ' Limited') + ' Availability.') # m
    Casenames[str(int(line[0])+1)] += ((' No' if line[4] == '0.0' else '') + ' Clinical Testing, ')
    Casenames[str(int(line[0])+1)] += ((' No' if line[5] == '0.0' else '') + ' Release Testing, and with')
    Casenames[str(int(line[0])+1)] += (('out' if line[6] == '0.0\n' else '') + ' Kit Testing')

# ingest case files and output summaries.

Case_Outcomes = {}
Case_Outcomes['0'] = ['Case Name', 'Fatalities', 'Fatalities STDev', 'GDP Pct Loss', 'GDP Pct Loss STDev',
                      'Total Cases', 'Total Cases STDev', 'Tests Used', 'Tests Used STDev']
for case in Casenames.keys():
    avgvals = []
    stdvals = []
    with open(os.path.join(directory, "lmic-case-" + case +"-avg.tsv")) as avg_f:
        avg_cols = avg_f.readline().split(sep='\t')
        Resolved_Case_Cols = [avg_cols.index('Rn'), avg_cols.index('Ry')]
        GDP_Cols = [avg_cols.index('Rn'), avg_cols.index('Ry'), avg_cols.index('Sy'), avg_cols.index('Ey'),
                    avg_cols.index('Iy')] #Used later
        Cases_Cols = [avg_cols.index('Ry'), avg_cols.index('Rn'), avg_cols.index('Iy'), avg_cols.index('In')]
        for line in avg_f:
            avgvals.append(line.split(sep='\t'))
    with open(os.path.join(directory, "lmic-case-" + case + "-std.tsv")) as std_f:
        stdev_cols = std_f.readline().split(sep='\t')
        for line in std_f:
            stdvals.append(line.split(sep='\t'))
    # Now I need to actually do the math
    Case_Outcomes[case] = []
    Case_Outcomes[case].append(Casenames[case]) #name
    # Fatalities is R_final times 0.01.
    #avg_cols.index('Sn')
    #avg_cols.index('Sy')
    Case_Outcomes[case].append(
        sum([float(avgvals[-1][i]) for i in Resolved_Case_Cols])*IFR) #Fatalities
    Case_Outcomes[case].append(
        sum([float(stdvals[-1][i]) for i in Resolved_Case_Cols])*IFR)  # Fatalities Stdev
    # GDP loss fraction is average of (Rn+Ry + Sy+Ey+Iy) / total population over the model time.
    Case_Outcomes[case].append(
        mean([sum([float(avgvals[time][i]) for i in GDP_Cols]) / Pop_Size for time in range(len(avgvals))]))
    Case_Outcomes[case].append(
        mean([sum([float(stdvals[time][i]) for i in GDP_Cols]) / Pop_Size for time in range(len(stdvals))]))
    # Total Cases is R_final + I_final
    Case_Outcomes[case].append(sum([float(avgvals[-1][i]) for i in Cases_Cols]))
    Case_Outcomes[case].append(sum([float(stdvals[-1][i]) for i in Cases_Cols]))
    # Number of tests used is T_final
    Case_Outcomes[case].append(float(avgvals[-1][avg_cols.index('T')]))
    Case_Outcomes[case].append(float(stdvals[-1][avg_cols.index('T')]))


workbook = xlsxwriter.Workbook('Summary_Data.xlsx')
worksheet = workbook.add_worksheet('Summaries')

# Start from the first cell. Rows and columns are zero indexed.
# Iterate over the data and write it out row by row.
for case in Case_Outcomes.keys():
    for entry in range(len(Case_Outcomes[case])):
        worksheet.write(int(case), entry, Case_Outcomes[case][entry])

workbook.close()