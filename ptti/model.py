__all__ = ['Model', 'Unimplemented']

import yaml
import logging
from math import floor
import numpy as np
from ptti.rseries import rseries

log = logging.getLogger(__name__)

## default parameters
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

class Unimplemented(Exception):
    """
    Exception raised when a subclass of model fails to implement
    a required method.
    """

class Model(object):
    """
    This class defines the interface for a model.

    The calling sequence is:

    >>> m = Model()
    >>> m.set_parameters(alpha=1, beta=2, ...)
    >>> state = m.initial_conditions(N=1000, I=10, ...)
    >>> t, obs, state = m.run(t0, tmax, tsteps, state)
    """
    ## name of this model
    name = "ChangeMe: set model.name"

    ## dictionary of parameter names to descriptions and default
    ## values, e.g.
    ##
    ## parameters = { 'a': { 'descr': 'a parameter', 'default': 1 } }
    parameters = yaml.load(yaml_params, yaml.FullLoader)

    ## list of observable metadata (dictionary of names, and descriptions
    ## etc in the order that they appear in model output
    ##
    ##
    ## observables = [{ 'name': 'I', 'descr': 'infectious }]
    observables = []

    def __init__(self):
        self.set_parameters(**dict((k, self.parameters[k]["default"])
                                   for k in self.parameters.keys()))

    def set_parameters(self, **params):
        """
        Set the model parameters. Subclasses should populate
        the `parameters` class variable with those parameters
        that are relevant. If any parameters that are not
        relevant are provided, a warning is issued. Parameters
        are then available as instance variables.
        """
        for k, v in params.items():
            if k in self.parameters:
                setattr(self, k, v)
            else:
                log.warning("[{}] unknown parameter provided {} = {}".format(self.name, k, v))

    def initial_conditions(self, **init):
        """
        Return a model state object, given initial conditions.
        The model state is opaque, and encodes the initial
        conditions of the model. The convention is that the
        initial conditions include,

          - `N` the total population
          - one entry for each non-zero observable, e.g. I=10
          - any other initial state required by the model
        """
        raise Unimplemented("[{}] initial_conditions".format(self.name))

    def colindex(self, c):
        """
        Return the index in the columns of the trajectory for
        the named observable.
        """
        for i, o in enumerate(self.observables):
            if o["name"] == c:
                return i
        raise ValueError("no such column: {}".format(c))

    def run(self, t0, tmax, tsteps, state):
        """
        Run the model from time t0 to time tmax reporting in
        tsteps number of steps, provided initial model state. This
        returns a triple of `(t, obs, state)` where:

          - `t` is a sequence of times
          - `obs` is a numpy array of observables representing
            the model trajectory at each `t`
          - `state` is an opaque state object representing
            the final state of the model
        """
        raise Unimplemented("[{}] run".format(self.name))

    @property
    def sucols(self):
        """
        Method supporting computation of R(t): return column indexes
        for susceptibles subject to infection (e.g. not quarantined)
        """
        return (self.colindex("SU"),)
    @property
    def iucols(self):
        """
        Method supporting computation of R(t): return column indexes
        for active infectious individuals (e.g. not quarantined)
        """
        return (self.colindex("IU"),)
    @property
    def icols(self):
        """
        Method supporting computation of R(t): return column indexes
        for all infectious individuals
        """
        return (self.colindex("IU"), self.colindex("ID"))

    def R(self, t, traj, beta=None, c=None):
        """
        Return a time-series of R(t) to augment the given trajectory.

        Support passing in beta and c which may be arrays to support
        calculating R(t) under interventions. If they are not given,
        the corresponding model parameter is used.

        This is done in a slightly model-specific way because we need
        to know the susceptible population and the fraction of the
        infectious population that may infect them.
        """
        SU = np.sum(traj[:,i] for i in self.sucols)
        IU = np.sum(traj[:,i] for i in self.iucols)
        I  = np.sum(traj[:,i] for i in self.icols)
        X = np.zeros(len(I))
        np.true_divide(SU*IU, I, out=X, where=I != 0)

        if beta is None:
            beta = self.beta
        if c is None:
            c = self.c
        return rseries(t, X, beta, c, self.gamma, sum(traj[0]))


def runModel(model, t0, tmax, tsteps, parameters={}, initial={}, interventions=[], rseries=False):
    """
    Run the provided model with the given parameters, initial conditions and
    interventions. The latter are a list 2-tuples of the form (time, parameters).
    The model is run up to the given time, the parameters are updated, and it
    then continues, for each intervention up until tmax.
    """
    m = model()
    m.set_parameters(**parameters)
    state = m.initial_conditions(**initial)

    log.info("Running model: {}".format(m.name))
    log.info("Parameters: {}".format(parameters))
    log.info("Initial conditions: {}".format(initial))
    log.info("Interventions: {}".format(len(interventions)))

    ## piece-wise simulation segments
    times = []
    trajs = []

    ## also record a time-series of betas and cs for
    ## piece-wise computation of R(t)
    if rseries:
        betas = []
        cs    = []

    ts = t0
    for iv in interventions:
        ti, pi = iv["time"], iv["parameters"]

        ## end time for this segment
        te = min(tmax, ti)

        ## how many time-steps in this segment?
        steps = floor((te - ts) * tsteps / (tmax - t0))

        ## end time in integral number of steps
        te = ts + (steps * (tmax - t0) / tsteps)

        ## run the simulation
        log.info("Running from {} to {} in {} steps".format(ts, te, steps))
        t, traj, state = m.run(ts, te, steps, state)

        ## save the trajectory
        times.append(t)
        trajs.append(traj)

        ## save the beta and c being used
        if rseries:
            betas.append(m.beta * np.ones(len(t)))
            cs.append(m.c * np.ones(len(t)))

        ## update the parameters
        log.info("Intervention: {}".format(pi))
        m.set_parameters(**pi)

        ts = ti

        ## stop running if we are past the 
        if te >= tmax:
            break

    ## if we have more time to run, run for the required
    ## number of steps
    if ts < tmax:
        steps = int((tmax - ts) * tsteps / (tmax - t0))
        log.info("Running from {} to {} in {} steps".format(ts, tmax, steps))
        t, traj, state = m.run(ts, tmax, steps, state)

        ## save the trajectory
        times.append(t)
        trajs.append(traj)

        ## save the beta and c being used
        if rseries:
            betas.append(m.beta * np.ones(len(t)))
            cs.append(m.c * np.ones(len(t)))

    t    = np.hstack(times)
    traj = np.vstack(trajs)

    if rseries:
        betas = np.hstack(betas)
        cs    = np.hstack(cs)
        rs    = m.R(t, traj, betas, cs)
        traj  = np.vstack((traj.T, rs)).T

    return t, traj
