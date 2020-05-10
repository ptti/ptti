import matplotlib.pyplot as plt
import numpy as np

from ptti.seirct_ode import SEIRCTODEMem
from ptti.model import runModel
from ptti.data import uk_mortality

t0, tmax, steps = 0, 150, 150

ifr = 0.01
offset = 0 ## date offset for uk case data

initial = {
    "N": 67000000,
    "IU": 1,
}

params = {
    "beta":  0.038,
    "c":     13,
    "alpha": 0.2,
    "gamma": 0.1429,
    "theta": 0.0,
}

t, traj = runModel(SEIRCTODEMem, t0, tmax, steps, params, initial)
IU = traj[:, 4]
ID = traj[:, 5]
t += offset
cases = IU + ID
deaths = ifr * cases

ukm = uk_mortality()
ukt = ukm[:,0]
ukcases = ukm[:,1]
ukdeaths = ukm[:,2]

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
ax2.plot(ukt, ukdeaths, label="UK deaths")
ax2.legend()

fig.show()

input()
