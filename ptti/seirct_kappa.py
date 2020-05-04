__all__ = ['SEIRCTKappa']

import numpy as np
import kappy
import logging
import yaml
import pkg_resources
from ptti.model import Model

log = logging.getLogger(__name__)

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
    """
    /////////////////////////////////////////////
    /// SEIR with Contact Tracing Kappa Model ///
    /////////////////////////////////////////////
    """
    name = "SEIR-CT Kappa"
    observables = yaml.load(yaml_obs, yaml.FullLoader)

    def _vars(self, N):
        params = ["%var: {}\t{}\t// {}".format(k, getattr(self, k), self.parameters[k]["descr"])
                  for k in self.parameters.keys()]
        params.append("%var: N\t{}\t// Total population".format(N))
        return "\n".join(params)

    def _rules(self):
        return pkg_resources.resource_string(__name__, "seir-ct.ka").decode("utf-8")

    def _init(self, N, **ivs):
        obs = dict((o["name"], o) for o in self.observables)
        inits = ["%init: {}\t{}\t// {}".format(n, obs[k]["kappa"].strip("|"), obs[k]["descr"])
                 for k, n in ivs.items()]
        SU = "%init: {}\t{}\t// {}".format(N - sum(ivs.values()),
                                           obs["SU"]["kappa"].strip("|"), obs["SU"]["descr"])
        inits.append(SU)
        return "\n".join(inits)

    def _obs(self):
        obs = ["%obs: {}\t{}\t// {}".format(o["name"], o["kappa"], o["descr"])
               for o in self.observables]
        return "\n".join(obs)

    def initial_conditions(self, N, **inits):
        kappa_text = "\n\n".join((self.__doc__, self._vars(N), self._rules(), self._obs(), self._init(N, **inits)))
        log.debug(kappa_text)
        return kappa_text

    def run(self, t0, tmax, steps, kappa_text):
        """
        For the Kappa model, the state is simply the Kappa text
        """
        stepsize = (tmax - t0) / steps

        client = kappy.KappaStd()
        client.add_model_string(kappa_text)
        client.project_parse()

        client.simulation_start(kappy.SimulationParameter(stepsize, "[T] > {0}".format(tmax - t0)))
        client.wait_for_simulation_stop()

        plot = client.simulation_plot()
        series = np.array(plot["series"])[::-1, :]

        t = series[:, 0]
        traj = series[:, 1:]

        ## Kappa will stop running when no more events are possible,
        ## so pad to the end
        skipped = steps - traj.shape[0]
        if skipped > 0:
            maxt = max(t)
            stepsize = (tmax - t0) / steps
            t = np.hstack([t, np.linspace(t[-1] + stepsize, tmax-t0, skipped)])
            traj = np.pad(traj, ((0,skipped), (0, 0)), "edge")

        ## correct time-series because Kappa always starts at 0
        t = t + t0

        ## construct a new Kappa program to support exogeneous interventions
        last   = traj[-1]
        onames = [o["name"] for o in self.observables]
        init   = dict((o, self.colindex(o)) for o in onames)
        N      = np.sum(last[i] for i in self.pcols)
        kappa_text = self.initial_conditions(N, **init)

        return t, traj, kappa_text
