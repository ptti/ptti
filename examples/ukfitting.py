import matplotlib.pyplot as plt
import numpy as np

from ptti.seirct_ode import SEIRCTODEMem
from ptti.model import runModel
from ptti.data import uk_mortality_2
# uk_mortality_2 data starts on 15th Feb 2020,
#   first cases 23rd Feb (t=53), first deaths 5th March (t=64)

t0, tmax, steps = -14, 127, 141  # Day 0 is 1st Jan 2020, -14 is 18th Dec 2019
    # simulation runs from 1st Jan to 7th May (t=127)
ifr = 0.008
offset = 0 ## date offset for uk case data

initial = {
    "N": 67886011,
    "IU": 2,
}

params = {
    "beta":  0.0375,
    "c":     13,
    "alpha": 0.2,
    "gamma": 0.1429,
    "theta": 0.0,
}

interventions = [
    { "time": 75, "parameters": { "c": 10 } },  # 16th March 2020 voluntary distancing
    { "time": 82, "parameters": { "c": 4 } }    # 23rd March 2020 lockdown
]

model = SEIRCTODEMem
t, traj = runModel(model, t0, tmax, steps, params, initial, interventions)
RU = traj[:, model.colindex("RU")]
RD = traj[:, model.colindex("RD")]
t += offset
cases = RU + RD
deaths = ifr * cases

ukm = uk_mortality()
ukt = ukm[:,0]
ukcases = ukm[:,1]
ukdeaths = ukm[:,2]*1.6

fig, (ax1, ax2) = plt.subplots(2, 1)

ax1.set_xlabel("Days since outbreak start")
ax1.set_ylabel("Cases")
ax1.set_xlim(t0, tmax)
ax1.set_yscale("log")
ax1.plot(t, cases, label="Simulated")
ax1.plot(ukt, ukcases, label="UK data")
ax1.legend()

ax2.set_xlabel("Days since outbreak start")
ax2.set_ylabel("Deaths")
ax2.set_xlim(t0, tmax)
ax2.set_yscale("log")
ax2.plot(t, deaths, label="Simulated")
ax2.plot(ukt, ukdeaths, label="UK data")
ax2.legend()

fig.show()

input()
