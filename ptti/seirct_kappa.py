__all__ = ['SEIRCTKappa']

import numpy as np
import kappy
import logging
import yaml
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
  kappa: "|P(s{s}, d{u})|"
- name:  SD
  descr: susceptible and distanced
  kappa: "|P(s{s}, d{d})|"
- name:  EU
  descr: exposed and unconfined
  kappa: "|P(s{e}, d{u})|"
- name:  ED
  descr: infectious and distanced
  kappa: "|P(s{e}, d{d})|"
- name:  IU
  descr: infectious and unconfined
  kappa: "|P(s{i}, d{u})|"
- name:  ID
  descr: infectious and distanced
  kappa: "|P(s{i}, d{d})|"
- name:  RU
  descr: removed and unconfined
  kappa: "|P(s{r}, d{u})|"
- name:  RD
  descr: removed and distanced
  kappa: "|P(s{r}, d{d})|"
- name:  C
  descr: traceable
  kappa: "|C()|"
"""

class SEIRCTKappa(Model):
    parameters = yaml.load(yaml_params, yaml.FullLoader)
    observables = yaml.load(yaml_obs, yaml.FullLoader)

    def _vars(self):
        params = ["%var: {}\t{}\t// {}".format(k, getattr(self, k), self.parameters[k]["descr"])
                  for k in self.parameters.keys()]
        return "\n".join(params)
    def _rules(self):
        return ""
        with open("seir-ct.ka") as fp:
            kappa_text += "\n" + fp.read()

    def _init(self):
        return ""
    def _obs(self):
        obs = ["obs: {}\t{}\t// {}".format(o["name"], o["kappa"], o["descr"])
               for o in self.observables]
        return "\n".join(obs)

    def initial_conditions(self, **inits):
        return "\n\n".join((self._vars(), self._rules(), self._init(), self._obs()))

    def run(self, t0, tmax, steps, kappa_text):
        """
        For the Kappa model, the state is simply the Kappa text
        """
        stepsize = (tmax - t0) / steps

        client = kappy.KappaStd()
        client.add_model_string(kappa_text)
        client.project_parse()

        client.simulation_start(kappy.SimulationParameter(stepsize, "[T] > {0}".format(tmax)))
        client.wait_for_simulation_stop()

        plot = client.simulation_plot()
        series = np.array(plot["series"])

        t = series[:-1:-1, 0]
        traj = series[:-1:-1, 1:].T

        if traj.shape[1] > self.t.shape[0]:
            traj = traj[:,:self.t.shape[0]]
        else:
            ## pad because Kappa will stop if no more transitions
            traj = np.pad(traj, ((0,0), (0, self.t.shape[0] - traj.shape[1])), "edge")

        return t, traj, None
