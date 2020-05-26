__all__ = ["SEIRCTNet"]

import EoN
import networkx as nx
from collections import defaultdict
import numpy as np
from scipy.interpolate import interp1d
import yaml
from ptti.model import Model

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
  descr: infectious and distanced
- name:  IU
  descr: infectious and unconfined
- name:  ID
  descr: infectious and distanced
- name:  RU
  descr: removed and unconfined
- name:  RD
  descr: removed and distanced
"""

class SEIRCTNet(Model):
    name = "SEIR-CT Network"
    observables = yaml.load(yaml_seirct_obs, yaml.FullLoader)

    def initial_conditions(self, N, **o):
        gdef = o.get("graph", "nx.fast_gnp_random_graph(N, 5./(N-1))")
        G = eval(gdef)

        IC = defaultdict(lambda: 'SU')
        columns = list(o["name"] for o in self.observables)

        vertex = 0
        for k, v in o.items():
            for _ in range(v):
                IC[vertex] = k
                vertex += 1

        return (G, IC)

    def transitions(self):
        beta  = self.beta
        c     = self.c
        chi   = self.chi
        eta   = self.eta
        alpha = self.alpha
        gamma = self.gamma
        theta = self.theta
        kappa = self.kappa

        #we must define two graphs, one of which has the internal transitions
        H = nx.DiGraph()
        H.add_edge('EU', 'IU', rate = alpha)
        H.add_edge('ED', 'ID', rate = alpha)
        H.add_edge('IU', 'RU', rate = gamma)
        H.add_edge('ID', 'RD', rate = gamma)
        ## testing is perfect
        H.add_edge('IU', 'ID', rate = theta)
        ## leaving isolation
        H.add_edge('SD', 'SU', rate = kappa)
        H.add_edge('RD', 'RU', rate = kappa)

        #and the other graph has transitions caused by a neighbor.
        J = nx.DiGraph()
        ## infection
        J.add_edge(('IU', 'SU'), ('IU', 'EU'), rate = beta*c)

        ## isolation due to tracing
        J.add_edge(('ID', 'SU'), ('ID', 'ED'), rate = chi*eta)
        J.add_edge(('ID', 'EU'), ('ID', 'ED'), rate = chi*eta)
        J.add_edge(('ID', 'IU'), ('ID', 'ID'), rate = chi*eta)
        J.add_edge(('ID', 'RU'), ('ID', 'RD'), rate = chi*eta)

        return (H, J)

    def run(self, t0, tmax, tsteps, state):
        G, IC = state

        H, J = self.transitions()

        rs = [o["name"] for o in self.observables]
        ig = EoN.Gillespie_simple_contagion(G, H, J, IC, rs, tmax = (tmax-t0), return_full_data=True)

        nettime, cols = ig.summary()
        nettraj = np.vstack(list(cols[o] for o in rs))
        nettime += t0

        t = np.linspace(t0, tmax, tsteps)
        if nettime.shape == (1,):
            ## can't interpolate if no transitions are possible
            traj = np.vstack(list(nettraj.T for _ in range(tsteps))).T
        else:
            traj = interp1d(nettime, nettraj, kind="previous", bounds_error=False,
                            fill_value=(nettraj[:,0], nettraj[:,-1]))(t)

        return (t, traj.T, (ig.G, ig.get_statuses(time=nettime[-1])))

