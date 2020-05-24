__all__ = ['Model', 'Unimplemented']

import yaml
import logging
from math import floor
import numpy as np

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

    conditions = None

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
            setattr(self, k, v)

    def reset_parameters(self, **params):
        """
        Reset the model parameters. By default, this just calls
        `set_parameters()`. It is intended for implementations
        that carry internal state that also needs to be reset
        when parameters change due to interventions.
        """
        return self.set_parameters(**params)

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

    def add_condition(self, callable):
        if self.conditions is None:
            self.conditions = []
        self.conditions.append(callable)

    @classmethod
    def colindex(cls, c):
        """
        Return the index in the columns of the trajectory for
        the named observable.
        """
        ## this enables uniform use of colindex mainly for the
        ## benefit of plotting, so that computed columns like
        ## R can be specified numerically
        if isinstance(c, int):
            return c
        for i, o in enumerate(cls.observables):
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
    def pcols(self):
        """
        Method supporting computation of R(t): return column indexes
        representing individuals. These should sum to N.
        """
        return tuple(self.colindex(c) for c in ("SU", "SD", "EU", "ED", "IU", "ID", "RU", "RD"))
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
        Compute the function R(t) for the reproduction number according to the
        provided time-series for the susceptible population. Taken from S9.3 of
        https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6002118/

        Support passing in beta and c which may be arrays to support
        calculating R(t) under interventions. If they are not given,
        the corresponding model parameter is used.

        This is done in a slightly model-specific way because we need
        to know the susceptible population and the fraction of the
        infectious population that may infect them.
        """
        if beta is None:
            beta = self.beta
        if c is None:
            c = self.c

        n = len(t)

        ## could alternatively require that subclasses just populate self.N
        N  = np.sum(traj[0,i] for i in self.pcols)
        ## but these are model-specific anyways
        SU = np.sum(traj[:,i] for i in self.sucols)
        IU = np.sum(traj[:,i] for i in self.iucols)
        I  = np.sum(traj[:,i] for i in self.icols)

        X = np.zeros(len(I))
        np.true_divide(SU*IU, I, out=X, where=I != 0)

        ker = np.exp(-self.gamma*t)
        bcs = beta*c*X

        Rs = []
        for i, tau in enumerate(t):
            s = np.pad(bcs, (n-i-1, 0), mode="edge")
            Rs.append(np.trapz(s[:n]*ker[::-1]/N, t))
        return np.array(Rs)

def runModel(model, t0, tmax, steps, parameters={}, initial={}, interventions=[], rseries=True, seed=0, **unused):
    """
    Run the provided model with the given parameters, initial conditions and
    interventions. The model is run up to the given time, the parameters are
    updated, and it then continues, for each intervention up until tmax.

    Arguments:

      - `model` is a model class (not an instance). It will be initialised by
         this function.
      - `t0` the start time of the simulation. This will usually be 0.
      - `tmax` the end time of the simulation.
      - `steps` the number of time-steps to report, evenly spaced from `t0`
         to `tmax`.
      - `parameters` model parameters. This is a dictionary of the form,

           { "beta": 0.033, "c": 13, "theta": 0.1 }

      - `initial` initial conditions. For example,

           { "N": 10000, "IU": 10, "EU": 5 }

        it is required to provide N, and it doesn't make much sense to not
        provide any I.
      - `interventions` are a list of interventions that may change any parameter.
        For example, the following would set c to a small value representing
        lockdown at 60 days, and then raise it to normal at 120 days,

           [
             { "time": 60, parameters: { "c": 5 }},
             { "time": 120, parameters: { "c": 13}}
           ]

      - `rseries` compute R(t) and concatenate it to the trajectory. It will
         be the last column.
      - `seed` the random seed to set at the beginning of the simulation.

    Returns a tuple `(t, traj)` where `t` is the sequence of times, and `traj`
    is the sequence of observables produced by the model.
    """
    np.random.seed(seed)

    m = model()
    m.set_parameters(**parameters)
    state = m.initial_conditions(**initial)

    log.info("Running model: {}".format(m.name))
    log.info("Random seed: {}".format(seed))
    log.info("Parameters: {}".format(parameters))
    log.info("Initial conditions: {}".format(initial))
    log.info("Interventions: {}".format(len(interventions)))

    ## piece-wise simulation segments
    times = []
    trajs = []

    events = []
    for iv in [i for i in interventions if "condition" in i]:
        _add_condition(m, iv, events)

    t00 = t0 ## save actual start time because interventions are relative to it
    ts = t0
    for iv in [i for i in interventions if "time" in i]:
        ti, pi = iv["time"], iv["parameters"]
        ti = ti - t00 ## interventions relative to start time

        ## end time for this segment
        te = min(tmax, ti)

        ## how many time-tsteps in this segment?
        tsteps = floor((te - ts) * steps / (tmax - t0))

        ## end time in integral number of tsteps
        te = ts + (tsteps * (tmax - t0) / steps)

        ## run the simulation
        log.info("Running from {} to {} in {} tsteps".format(ts, te, tsteps))
        if tsteps == 0: continue
        t, traj, state = m.run(ts, te, tsteps, state)

        ## save the trajectory
        times.append(t)
        trajs.append(traj)

        ## update the parameters
        log.info("Intervention: {}".format(pi))
        m.set_parameters(**pi)

        ts = ti

        ## stop running if we are past the 
        if te >= tmax:
            break

    ## if we have more time to run, run for the required
    ## number of tsteps
    if ts < tmax:
        tsteps = int((tmax - ts) * steps / (tmax - t0))
        log.info("Running from {} to {} in {} tsteps".format(ts, tmax, tsteps))
        if tsteps > 0: ## can be 0 if the step is smaller than the step size
            t, traj, state = m.run(ts, tmax, tsteps, state)

            ## save the trajectory
            times.append(t)
            trajs.append(traj)

    t    = np.hstack(times)
    traj = np.vstack(trajs)

    if "beta" not in parameters:
        parameters["beta"] = getattr(m, "beta")
    if "c" not in parameters:
        parameters["c"] = getattr(m, "c")
    if rseries:
        ## compute the simulation segments where beta and c change because we need
        ## them to calculate R.
        ivs = sorted(events + [i for i in interventions if "time" in i], key=lambda x: x["time"])

        betapieces = [(i["time"], i["parameters"]["beta"]) for i in ivs if "beta" in i["parameters"]]
        betapieces.insert(0, (0, parameters["beta"]))

        cpieces = [(i["time"], i["parameters"]["c"]) for i in ivs if "c" in i["parameters"]]
        cpieces.insert(0, (0, parameters["c"]))

        ## project the values onto the right segment
        def _project(pieces):
            segments = []
            for i in range(len(pieces)):
                start, v = pieces[i]
                if i < len(pieces)-1:
                    end, _ = pieces[i+1]
                    seg = v * (t >= start)*(t < end)
                else:
                    seg = v * (t >= start)
                segments.append(seg)
            return np.sum(segments, axis=0)

        betas = _project(betapieces)
        cs    = _project(cpieces)

        rs    = m.R(t, traj, betas, cs)
        traj  = np.vstack((traj.T, rs)).T

    return t, traj, events


def _add_condition(m, iv, events):
    g = { col: m.colindex(col) for col in [o["name"] for o in m.observables] }
    cond = iv["condition"]
    def e(t, x):
        g.update(m.__dict__)
        root = eval(cond, g, {"t": t, "x": x})
        if 0 <= root*e.direction < 1:
            log.info("Condition '{}' met at t = {}".format(cond, t))
            record = iv.copy()
            record["time"] = t
            events.append(record)
            m.reset_parameters(**iv["parameters"])
        return root
    e.direction = iv.get("direction", 1.0)
    m.add_condition(e)
