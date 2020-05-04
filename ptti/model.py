__all__ = ['Model', 'Unimplemented']

import logging

log = logging.getLogger(__name__)

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
    >>> t, obs, state = m.run(state)
    """
    ## name of this model
    name = "ChangeMe: set model.name"

    ## list of parameters known to this model
    parameters = []

    ## list of observable names in the order that they appear
    ## in model output
    observables = []

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
        conditions of the model.
        """
        raise Unimplemented("[{}] initial_conditions".format(self.name))

    def run(self, state):
        """
        Run the model, provided initial model state. This
        returns a triple of `(t, obs, state)` where:

          - `t` is a sequence of times
          - `obs` is a numpy array of observables representing
            the model trajectory at each `t`
          - `state` is an opaque state object representing
            the final state of the model
        """
        raise Unimplemented("[{}] run".format(self.name))

