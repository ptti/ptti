__all__ = ['SEIRCTODEMem']

import numpy as np
import yaml
from ptti.model import Model
from scipy.interpolate import interp1d
from cpyment import CModel
import logging

log = logging.getLogger(__name__)

yaml_seirct_obs = """
- name:  SU
  descr: susceptible and unconfined
- name:  SD
  descr: susceptible and distanced
- name:  EU
  descr: exposed and unconfined
- name:  ED
  descr: exposed and distanced
- name:  IU
  descr: infectious and unconfined
- name:  ID
  descr: infectious and distanced
- name:  RU
  descr: removed and unconfined
- name:  RD
  descr: removed and distanced
- name:  CIS
  descr: traceable and susceptible
- name:  CIR
  descr: traceable and exposed
- name:  M
  descr: dead
"""

class SEIRCTODEMem(Model):
    name = "SEIR-CT ODE"
    observables = yaml.load(yaml_seirct_obs, yaml.FullLoader)

    def initial_conditions(self, N, **o):
        """
        Populate the initial condition vector from the given data.
        SU will be populated with N less the sum of the data. For
        example,

        >>> m = SEIRCTODEMem()
        >>> m.initial_conditions(N=10000, IU=100)
        (array([9900.,    0.,    0.,    0.,  100.,    0.,    0.,    0.,    0.,
                0.,    0.,    0.]), 10000)
        """
        y0 = np.zeros(len(self.observables))
        columns = list(o["name"] for o in self.observables)
        for k, v in o.items():
            y0[columns.index(k)] = v
        y0[columns.index("SU")] = N - sum(o.values())
        return (y0, N)


    def couplings(self, N):
        beta  = self.beta
        c     = self.c
        chi   = self.chi
        eta   = self.eta
        alpha = self.alpha
        gamma = self.gamma
        theta = self.theta
        kappa = self.kappa
        ifr   = self.ifr

        return (
            ('SU*IU:SU=>EU', beta*c/N),
            ('SD:SD=>SU', kappa),

            ('EU:EU=>IU', alpha),
            ('ED:ED=>ID', alpha),

            ('IU:IU=>RU', gamma*(1-ifr)),
            ('ID:ID=>RD', gamma*(1-ifr)),
            ('IU:IU=>M', gamma*ifr),
            ('ID:ID=>M', gamma*ifr),

            ('RD:RD=>RU', kappa),

            ## trace
            ('EU:EU=>ED', eta*chi*theta),
            ('IU:IU=>ID', theta*(1+eta*chi)),

            # Now the stuff that depends on memory
            ('IU*SU:=>CIS', c*(1-beta)/N),
            ('IU*CIS:CIS=>', c*beta/N),
            ('CIS:CIS=>', gamma+theta*eta*chi),

            ('IU*RU:=>CIR', c/N),
            ('IU:=>CIR', gamma),
            ('CIR:CIR=>', gamma+theta*eta*chi),

            ## trace
            ('CIS:SU=>SD', chi*eta*theta),
            ('CIR:RU=>RD', chi*eta*theta)
        )

    def reset_parameters(self, **params):
        self.set_parameters(**params)
        for name, rate in self.couplings(self.N):
            self.cm.edit_coupling_rate(name, rate)

    def run(self, t0, tmax, tsteps, state):
        """
        Run the model from t0 to tmax in tsteps steps, given the
        starting model state.
        """
        y0, N = state

        self.N = N
        states = list(o["name"] for o in self.observables)
        self.cm = CModel(states)
        for name, rate in self.couplings(N):
            self.cm.set_coupling_rate(name, rate, name=name)

        t = np.linspace(t0, tmax, tsteps+1)

        traj = self.cm.integrate(t, y0, events=self.conditions, ivpargs={"max_step": 1.0})

        return (t, traj["y"], (traj["y"][-1, :], N))


yaml_seir_obs = """
- name:  SU
  descr: susceptible and unconfined
- name:  EU
  descr: exposed and unconfined
- name:  IU
  descr: infectious and unconfined
- name:  RU
  descr: removed and unconfined
"""

class SEIRODE(Model):
    name = "SEIR ODE"
    observables = yaml.load(yaml_seir_obs, yaml.FullLoader)

    @property
    def pcols(self):
        """
        Method supporting computation of R(t): return column indexes
        representing individuals. These should sum to N.
        """
        return tuple(self.colindex(c) for c in ("SU", "EU", "IU", "RU"))

    @property
    def icols(self):
        """
        Method supporting computation of R(t): return column indexes
        for all infectious individuals
        """
        return (self.colindex("IU"),)

    def initial_conditions(self, N, **o):
        """
        Populate the initial condition vector from the given data.
        SU will be populated with N less the sum of the data. For
        example,

        >>> m = SEIRODE()
        >>> m.initial_conditions(N=10000, IU=100)
        (array([9900.,    0.,    100.,    0.]), 10000)

        This model is mainly used for fitting basic parameters like
        beta.
        """
        y0 = np.zeros(len(self.observables))
        columns = list(o["name"] for o in self.observables)
        for k, v in o.items():
            y0[columns.index(k)] = v
        y0[columns.index("SU")] = N - sum(o.values())
        return (y0, N)

    def _cmodel(self, N):
        beta  = self.beta
        c     = self.c
        alpha = self.alpha
        gamma = self.gamma

        states = list(o["name"] for o in self.observables)
        cm = CModel(states)

        cm.set_coupling_rate('SU*IU:SU=>EU', beta*c/N)
        cm.set_coupling_rate('EU:EU=>IU', alpha)
        cm.set_coupling_rate('IU:IU=>RU', gamma)

        return cm

    def run(self, t0, tmax, tsteps, state):
        """
        Run the model from t0 to tmax in tsteps steps, given the
        starting model state.
        """
        y0, N = state
        cm = self._cmodel(N)
        t = np.linspace(t0, tmax, tsteps+1)

        traj = cm.integrate(t, y0, events=self.conditions)

        return (t, traj["y"], (traj["y"][-1, :], N))


    def fit_beta(self, N, init, data):
        """
        Estimate beta based on mortality data
        """
        cm = self._cmodel(N)
        constraints = dict(v for k,v in cm.couplings.items() if k not in ("SU*IU:SU=>EU",))
        constraints.update(init)
        print(constraints)

        fit = cm.fit(data, constraints=constraints)

        beta = fit.C["SU*IU:SU=>EU"] * N / self.c

        return (beta, fit)

    def tt_rates(self, t, traj):
        # Return testing and tracing rates, computed from a trajectory
        pass        
        
