__all__ = ['SEIRCTODEMem']

import numpy as np
import yaml
from ptti.model import Model
from scipy.interpolate import interp1d
from cpyment import CModel
import logging

log = logging.getLogger(__name__)

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
- name:  CIS
  descr: traceable and susceptible
- name:  CIE
  descr: traceable and exposed
- name:  CII
  descr: traceable and infectious
- name:  CIR
  descr: traceable and exposed
"""

class SEIRCTODEMem(Model):
    parameters = yaml.load(yaml_params, yaml.FullLoader)
    observables = yaml.load(yaml_obs, yaml.FullLoader)

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


    def run(self, t0, tmax, tsteps, state):
        """
        Run the model from t0 to tmax in tsteps steps, given the
        starting model state.
        """
        y0, N = state
        beta  = self.beta
        c     = self.c
        chi   = self.chi
        eta   = self.eta
        alpha = self.alpha
        gamma = self.gamma
        theta = self.theta
        kappa = self.kappa

        states = list(o["name"] for o in self.observables)
        cm = CModel(states)

        cm.set_coupling_rate('SU*IU:SU=>EU', beta*c/N)
        cm.set_coupling_rate('SD:SD=>SU', kappa)

        cm.set_coupling_rate('EU:EU=>IU', alpha)
        cm.set_coupling_rate('ED:ED=>ID', alpha)

        cm.set_coupling_rate('IU:IU=>RU', gamma)
        cm.set_coupling_rate('ID:ID=>RD', gamma)

        cm.set_coupling_rate('RD:RD=>RU', kappa)

        cm.set_coupling_rate('EU:EU=>ED', eta*chi*theta)
        cm.set_coupling_rate('IU:IU=>ID', theta*(1+eta*chi))

        # Now the stuff that depends on memory
        cm.set_coupling_rate('IU*SU:=>CIS', c*(1-beta)/N)
        cm.set_coupling_rate('IU*CIS:CIS=>CIE', c*beta/N)
        cm.set_coupling_rate('CIS:CIS=>', gamma+theta*eta*chi)
        cm.set_coupling_rate('CIS*CIS:CIS=>', chi*(1-(1-eta)**2)*theta/N)

        cm.set_coupling_rate('IU*SU:=>CIE', c*beta/N)
        cm.set_coupling_rate('CIE:CIE=>CII', alpha)
        cm.set_coupling_rate('CIE:CIE=>', gamma+theta*eta*chi)

        cm.set_coupling_rate('IU*IU:=>CII', c/N)
        cm.set_coupling_rate('CII:CII=>CIR', gamma)
        cm.set_coupling_rate('CII:CII=>', gamma+theta*(1+eta*chi))

        cm.set_coupling_rate('IU*RU:=>CIR', c/N)
        cm.set_coupling_rate('CIR:CIR=>', gamma+theta*eta*chi)
        cm.set_coupling_rate('CIR*CIR:CIR=>', chi*(1-(1-eta)**2)*theta/N)

        cm.set_coupling_rate('CIS:SU=>SD', chi*eta*theta)
        cm.set_coupling_rate('CIS*CIS:SU=>SD', chi*(1-(1-eta)**2)*theta/N)
        cm.set_coupling_rate('CIR:RU=>RD', chi*eta*theta)
        cm.set_coupling_rate('CIR*CIR:RU=>RD', chi*(1-(1-eta)**2)*theta/N)

        t = np.linspace(t0, tmax, tsteps)

        traj = cm.integrate(t, y0)

        return (t, traj["y"], (traj["y"][-1, :], N))
