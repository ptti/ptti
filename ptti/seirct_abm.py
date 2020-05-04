__all__ = ['SEIRCTABM']

import numpy as np
from numba import jit
from math import sqrt
from scipy.interpolate import interp1d
import yaml
import logging as log
from ptti.model import Model

yaml_params = """
c:
  descr:   contact rate
  default: 13.0
beta:
  descr:   transmission probability
  default: 0.033
alpha:
  descr:   incubation rate
  default: 0.2
gamma:
  descr:   recovery rate
  default: 0.1429
theta:
  descr:   testing rate
  default: 0.0714
kappa:
  descr:   isolation exit rate
  default: 0.0714
eta:
  descr:   tracing success probability
  default: 0.5
chi:
  descr:   tracing rate
  default: 0.25
"""

yaml_obs = """
- name:  SU
  descr: susceptible and unconfined
- name:  SD
  descr: susceptible and distanced
- name:  EU
  descr: exposed and unconfined
- name:  ED
  descr: infectious and distanced
- name:  IU
  descr: infectious and unconfined
- name:  ID
  descr: infectious and distanced
- name:  RU
  descr: removed and unconfined
- name:  RD
  descr: removed and distanced
- name:  C
  descr: traceable
"""

# States
STATE_S = 0
STATE_E = 1
STATE_I = 2
STATE_R = 3

INDEX_SU = 0
INDEX_EU = 2
INDEX_IU = 4
INDEX_RU = 6

INDEX_SD = 1
INDEX_ED = 3
INDEX_ID = 5
INDEX_RD = 7

INDEX_CT = 8

@jit(nopython=True)
def count_states(states, diagnosed, traceable):
    SU = np.sum((states == STATE_S)*(diagnosed == 0))
    SD = np.sum((states == STATE_S)*diagnosed)
    EU = np.sum((states == STATE_E)*(diagnosed == 0))
    ED = np.sum((states == STATE_E)*diagnosed)
    IU = np.sum((states == STATE_I)*(diagnosed == 0))
    ID = np.sum((states == STATE_I)*diagnosed)
    RU = np.sum((states == STATE_R)*(diagnosed == 0))
    RD = np.sum((states == STATE_R)*diagnosed)
    CT = np.sum(traceable)
    return SU, SD, EU, ED, IU, ID, RU, RD, CT


@jit(nopython=True)
def count_pcis(states, diagnosed, contactM):
    SUi = np.where((states == STATE_S)*(1-diagnosed))[0]
    SDi = np.where((states == STATE_S)*diagnosed)[0]
    EUi = np.where((states == STATE_E)*(1-diagnosed))[0]
    EDi = np.where((states == STATE_E)*diagnosed)[0]
    IUi = np.where((states == STATE_I)*(1-diagnosed))[0]
    IDi = np.where((states == STATE_I)*diagnosed)[0]
    RUi = np.where((states == STATE_R)*(1-diagnosed))[0]
    RDi = np.where((states == STATE_R)*diagnosed)[0]

    N = states.shape[0]
    SUpci = np.sum(contactM[SUi])/(len(SUi)*N)
    SDpci = np.sum(contactM[SDi])/(len(SDi)*N)
    EUpci = np.sum(contactM[EUi])/(len(EUi)*N)
    EDpci = np.sum(contactM[EDi])/(len(EDi)*N)
    IUpci = np.sum(contactM[IUi])/(len(IUi)*N)
    IDpci = np.sum(contactM[IDi])/(len(IDi)*N)
    RUpci = np.sum(contactM[RUi])/(len(RUi)*N)
    RDpci = np.sum(contactM[RDi])/(len(RDi)*N)

    return SUpci, SDpci, EUpci, EDpci, IUpci, IDpci, RUpci, RDpci


@jit(nopython=True)
def random_agent_i(states, diagnosed, tstate, tdiag=None):
    if tdiag is None:
        return np.random.choice(np.where(states == tstate)[0])
    else:
        return np.random.choice(np.where((states == tstate) *
                                         (diagnosed == tdiag))[0])


@jit(nopython=True)
def seirxud_abm_gill(tmax=10,
                     N=1000,
                     I0=10,
                     c=5,
                     beta=0.05,
                     alpha=0.2,
                     gamma=0.1,
                     theta=0.0,
                     kappa=0.05,
                     eta=0,
                     chi=0,
                     return_pcis=False):


    # Generate states
    states = np.zeros(N, dtype=np.int8)
    # Generate diagnosed state
    diagnosed = np.zeros(N, dtype=np.bool8)
    # Generate traceable status
    traceable = np.zeros(N, dtype=np.bool8)
    # Contact matrix
    contactM = np.zeros((N, N), dtype=np.bool8)

    # Infect I0 patients
    istart = np.random.choice(np.arange(N), size=I0, replace=False)
    for i in istart:
        states[i] = STATE_I

    times = []
    traj = []
    pcis = []

    t = 0
    while t < tmax:

        counts = count_states(states, diagnosed, traceable)
        traj.append(counts)
        times.append(t)
        if return_pcis:
            pcis.append(np.sum(np.sum(contactM, axis=0) > 0)/N)
        else:
            pcis.append(0)

        E = counts[INDEX_EU] + counts[INDEX_ED]
        I = counts[INDEX_IU] + counts[INDEX_ID]

        # Possible contacts
        wSIc = c*counts[INDEX_SU]*counts[INDEX_IU]/N
        # E becomes I
        wEI = alpha*E
        # I becomes R
        wIR = gamma*I
        # I is diagnosed
        wIUID = theta*counts[INDEX_IU]
        # Diagnosed S is released
        wSDSU = kappa*counts[INDEX_SD]
        # Diagnosed R is released
        wRDRU = kappa*counts[INDEX_RD]
        # Someone who's traceable gets quarantined
        wCT = chi*counts[INDEX_CT]

        Wtot = wSIc + wEI + wIR + wIUID + wSDSU + wRDRU + wCT
        if Wtot <= 0:
            break

        wp = np.array([wSIc, wEI, wIR, wIUID, wSDSU, wRDRU, wCT])
        wp = np.cumsum(wp)/Wtot

        dt = -np.log(np.random.random())/Wtot

        rn = np.random.random()

        if rn < wp[0]:
            # Contact between a random SU and a random IU
            si = random_agent_i(states, diagnosed, STATE_S, False)
            ii = random_agent_i(states, diagnosed, STATE_I, False)
            contactM[si, ii] = True
            if np.random.random() <= beta:
                states[si] = STATE_E
        elif rn < wp[1]:
            # E becomes I
            ei = random_agent_i(states, diagnosed, STATE_E)
            states[ei] = STATE_I
        elif rn < wp[2]:
            # I becomes R
            ii = random_agent_i(states, diagnosed, STATE_I)
            contactM[:, ii] = False
            states[ii] = STATE_R
        elif rn < wp[3]:
            # Diagnosis
            ii = random_agent_i(states, diagnosed, STATE_I, False)
            diagnosed[ii] = True
            traceable[ii] = False
            # Also set all those who have it as an infector as traceable
            ctis = np.where((contactM[:, ii]*(diagnosed == 0)))[0]
            traceable[ctis] = np.logical_or(traceable[ctis],
                                            np.random.random(len(ctis)) < eta)
        elif rn < wp[4]:
            si = random_agent_i(states, diagnosed, STATE_S, True)
            diagnosed[si] = False
        elif rn < wp[5]:
            ri = random_agent_i(states, diagnosed, STATE_R, True)
            diagnosed[ri] = False
        else:
            # Contact tracing
            # Random traceable?
            cti = np.random.choice(np.where(traceable)[0])
            diagnosed[cti] = True
            traceable[cti] = False

        t += dt

    counts = count_states(states, diagnosed, traceable)
    traj.append(counts)
    times.append(t)
    if return_pcis:
        pcis.append(np.sum(np.sum(contactM, axis=0) > 0)/N)
    else:
        pcis.append(0)

    return times, traj, pcis


class SEIRCTABM(Model):
    parameters = yaml.load(yaml_params, yaml.FullLoader)
    observables = yaml.load(yaml_obs, yaml.FullLoader)

    def initial_conditions(self, N, I0=None):
        if I0 is None:
            I0 = int(0.01 * N)
        return (N, I0)

    def run(self, t0, tmax, tsteps, state, return_pcis=False):
        N, I0 = state
        t = np.linspace(t0, tmax, tsteps)

        times, traj, pcis = seirxud_abm_gill(tmax=t[-1],
                                             N=N, I0=I0,
                                             c=self.c, beta=self.beta,
                                             alpha=self.alpha, gamma=self.gamma,
                                             theta=self.theta, kappa=self.kappa,
                                             eta=self.eta, chi=self.chi)
        traj = np.array(traj).T


        intptraj = interp1d(times, traj, kind="previous", bounds_error=False,
                            fill_value=(traj[:, 0], traj[:,-1]))(t)

        if return_pcis:
            intppcis = interp1d(tr[0], pcis, kind="previous", bounds_error=False,
                               fill_value=(pcis[0], pcis[-1]))(t)

            return t, (intptraj.T, intppcis), state
        else:
            return t, intptraj.T, state
