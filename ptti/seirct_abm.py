__all__ = ['SEIRCTABM', 'SEIRCTABMDet']

import numpy as np
from numba import jit
from math import sqrt
from scipy.interpolate import interp1d
import yaml
import logging as log
from ptti.model import Model

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

# Time rows (for deterministic model)
TIME_I_CONTACT = 0
TIME_I_STATE = 1
TIME_I_ISOL = 2
TIME_I_TEST = 3
TIME_I_TRACE = 4


@jit(nopython=True, cache=True)
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


@jit(nopython=True, cache=True)
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


@jit(nopython=True, cache=True)
def random_agent_i(states, diagnosed, tstate, tdiag=None):
    if tdiag is None:
        return np.random.choice(np.where(states == tstate)[0])
    else:
        return np.random.choice(np.where((states == tstate) *
                                         (diagnosed == tdiag))[0])


@jit(nopython=True, cache=True)
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
        wIc = c*counts[INDEX_IU]
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

        Wtot = wIc + wEI + wIR + wIUID + wSDSU + wRDRU + wCT
        if Wtot <= 0:
            break

        wp = np.array([wIc, wEI, wIR, wIUID, wSDSU, wRDRU, wCT])
        wp = np.cumsum(wp)/Wtot

        dt = -np.log(np.random.random())/Wtot

        rn = np.random.random()

        if rn < wp[0]:
            # Contact between a random individual and a random IU
            rndi = np.random.randint(0, N)
            ii = random_agent_i(states, diagnosed, STATE_I, False)
            contactM[rndi, ii] = True
            is_SU = (states[rndi] == STATE_S)*(not diagnosed[rndi])
            if is_SU and np.random.random() <= beta:
                states[rndi] = STATE_E
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


@jit(nopython=True, cache=True)
def seirxud_abm_det(tmax=100,
                    N=1000,
                    I0=10,
                    c=5,
                    beta=0.05,
                    alpha=0.2,
                    gamma=0.1,
                    theta=0.0,
                    theta0=-1,
                    kappa=0.05,
                    eta=0,
                    chi=0,
                    return_pcis=False):
    
    theta0 = max(theta, theta0) # Can't be smaller than theta

    # Times
    tEI = 1.0/alpha if alpha > 0 else np.inf
    tIR = 1.0/gamma if gamma > 0 else np.inf
    tUD = 1.0/theta0 if theta0 > 0 else np.inf
    tCO = 1.0/c if c > 0 else np.inf
    tDU = 1.0/kappa if kappa > 0 else np.inf
    tCT = 1.0/chi if chi > 0 else np.inf

    # Probability of testing
    ptest = theta/(theta0 if theta0 > 0 else 1)

    # Generate states
    states = np.zeros(N, dtype=np.int8)
    # Generate diagnosed state
    diagnosed = np.zeros(N, dtype=np.bool8)
    # Generate traceable status
    traceable = np.zeros(N, dtype=np.bool8)
    # Contact matrix
    contactM = np.zeros((N, N), dtype=np.bool8)
    # Times matrix
    timeM = np.zeros((N, 5)) + np.inf

    # Infect I0 patients
    istart = np.random.choice(np.arange(N), size=I0, replace=False)
    for i in istart:
        states[i] = STATE_I
        # How long have they had it?
        t0 = min(tIR, tUD)*np.random.random()
        timeM[i, TIME_I_STATE] = tIR-t0
        if np.random.random() < ptest:
            timeM[i, TIME_I_TEST] = tUD-t0
        timeM[i, TIME_I_CONTACT] = tCO-np.fmod(t0, tCO)

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

        dt = np.amin(timeM)
        trans = np.argmin(timeM)

        ti = int(trans/5)
        ttype = trans%5

        if dt == np.inf:
            # Simulation is over!
            break
        elif dt < 0:
            dt = 0

        timeM[ti, ttype] = np.inf
        t += dt
        timeM = timeM-dt

        if ttype == TIME_I_CONTACT:
            # Contact between a random individual and a random IU
            rndi = np.random.randint(0, N)
            if states[ti] == STATE_I and (not diagnosed[ti]):
                contactM[rndi, ti] = True
                is_SU = (states[rndi] == STATE_S)*(not diagnosed[rndi])
                if is_SU and np.random.random() <= beta:
                    states[rndi] = STATE_E
                    timeM[rndi, TIME_I_STATE] = tEI
                timeM[ti, TIME_I_CONTACT] = tCO

        elif ttype == TIME_I_STATE:
            if states[ti] == STATE_E:            
                # E becomes I
                states[ti] = STATE_I
                timeM[ti, TIME_I_STATE] = tIR
                if np.random.random() < ptest:
                    timeM[ti, TIME_I_TEST] = tUD
                timeM[ti, TIME_I_CONTACT] = tCO
            elif states[ti] == STATE_I:
                states[ti] = STATE_R
                contactM[:, ti] = False
                timeM[ti, TIME_I_TEST] = np.inf
                timeM[ti, TIME_I_CONTACT] = np.inf
                if diagnosed[ti]:
                    timeM[ti, TIME_I_ISOL] = tDU

        elif ttype == TIME_I_ISOL:

            if diagnosed[ti] and states[ti] != STATE_I:
                diagnosed[ti] = False

        elif ttype == TIME_I_TEST:

            if states[ti] == STATE_I and (not diagnosed[ti]):
                # Diagnosis
                diagnosed[ti] = True
                traceable[ti] = False
                # Also set all those who have it as an infector as traceable
                ctis = np.where((contactM[:, ti]*(diagnosed == 0)))[0]
                traceable[ctis] = np.logical_or(traceable[ctis],
                                                np.random.random(len(ctis)) < eta)
                timeM[ti, TIME_I_CONTACT] = np.inf # No more contacts!
                for cti in ctis:
                    if traceable[cti]:
                        timeM[cti, TIME_I_TRACE] = tCT

        elif ttype == TIME_I_TRACE:
            # Contact tracing
            diagnosed[ti] = True
            traceable[ti] = False
            timeM[ti, TIME_I_CONTACT] = np.inf
            timeM[ti, TIME_I_TEST] = np.inf
            if states[ti] == STATE_S or states[ti] == STATE_R:
                timeM[ti, TIME_I_ISOL] = tDU

    counts = count_states(states, diagnosed, traceable)
    traj.append(counts)
    times.append(t)
    if return_pcis:
        pcis.append(np.sum(np.sum(contactM, axis=0) > 0)/N)
    else:
        pcis.append(0)

    return times, traj, pcis


class SEIRCTABM(Model):
    name = "SEIR-CT ABM"
    observables = yaml.load(yaml_obs, yaml.FullLoader)

    def initial_conditions(self, N, IU=None):
        if IU is None:
            IU = int(0.01 * N)
        return (N, IU)

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
                            fill_value=(traj[:, 0], traj[:, -1]))(t)

        if return_pcis:
            intppcis = interp1d(tr[0], pcis, kind="previous", bounds_error=False,
                                fill_value=(pcis[0], pcis[-1]))(t)

            return t, (intptraj.T, intppcis), state
        else:
            return t, intptraj.T, state


class SEIRCTABMDet(Model):
    name = "SEIR-CT ABM Deterministic"
    observables = yaml.load(yaml_obs, yaml.FullLoader)

    def initial_conditions(self, N, IU=None):
        if IU is None:
            IU = int(0.01 * N)
        return (N, IU)

    def run(self, t0, tmax, tsteps, state, return_pcis=False):
        N, I0 = state
        t = np.linspace(t0, tmax, tsteps)

        dt = t[1]-t[0]

        times, traj, pcis = seirxud_abm_det(tmax=t[-1],
                                            N=N, I0=I0,
                                            c=self.c, beta=self.beta,
                                            alpha=self.alpha, gamma=self.gamma,
                                            theta=self.theta, theta0=self.theta0,
                                            kappa=self.kappa,
                                            eta=self.eta, chi=self.chi)

        traj = np.array(traj).T

        intptraj = interp1d(times, traj, kind="previous", bounds_error=False,
                            fill_value=(traj[:, 0], traj[:, -1]))(t)

        if return_pcis:
            intppcis = interp1d(tr[0], pcis, kind="previous", bounds_error=False,
                                fill_value=(pcis[0], pcis[-1]))(t)

            return t, (intptraj.T, intppcis), state
        else:
            return t, intptraj.T, state
