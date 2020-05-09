# PTTI: Population-wide Testing, Tracing and Isolation

This repository contains software for simulating epidemiological models
of various kinds: compartmental models, agent-based models, and rule-based
models. It is intended for studying the effects of testing and contact
tracing for containing disease outbreaks. We call this TTI - Testing, 
tracing and Isolation. It contains the following models:

  * SEIRCTABM an agent-based model
  * SEIRCTODEMem an ODE implementation of a compartmental model with
    extra memory states
  * SEIRODE a plain SEIR model for comparison
  * SEIRKappa a rule-based model

The software has a variety of useful features:

  * Formalism-agnostic: we believe in checking models against each other,
    as it's the best way to understand which models work best in what 
    circumstances. So we have ordinary differential equation models,
    agent-based models, and rule-based models.
  * Simple configuration: simulations are described in a user-friendly
    YAML file (though there is nothing to prevent running them directly
    in [Python] if you wish).
  * Interventions: the simulation is stopped at set times (in future,
    on conditions as well), parameters are changed, and the simulation
    continues.
  * Parallel execution: simulations can be conducted in parallel using
    as many CPUs as are available, and also supports [MPI] for use in
    High-Performance Computing environments.
  * Easy extension to other models: we provide an interface definition
    that any model implementation with any number of compartments or 
    states or agents can use to be incorporated into the simulation
    machinery. It does have to be written in [Python]. We're sorry, it
    would have taken too long to make this software in [Haskell].
  
## Installation

This software is written for [Python]3 and relies on a number of 
libraries including [NumPy], [SciPy] and the [Numba] just-in-time
compiler. The most straightforward way to use this software is to
first create a virtual environment using, for example, [Conda],
and then clone this repository and install it in-place:

    conda create -n ptti python=3
    conda activate ptti
    git clone https://github.com/ptti/ptti
    cd ptti
    python setup.py develop

For rule-based simulations, the [KaSim] kappa-language simulator
should also be installed. It is a separate program that is used
through python bindings.

## Basic usage

A simulation is described by a YAML file. This description specifies
some metadata about which model to use, what time period to run for,
what time step to use for reporting and where to put output, and also
what initial values and parameters to set. In addition, it is possible
to specify interventions that change parameters discontinuously at 
given times (a planned feature is to also be able to do this when a
certain condition is met).

An example description that simply sets some initial conditions and 
uses the default values to run a simulation:

    meta:
      title:  Example simulation
      model:  SEIRCTODEMem
      output: example
    initial:
      N:  67000000
      IU: 100000

This example is run with the `ptti` command as follows:

    ptti -y example.yaml

Doing so will produce a tab-separated output file of the resulting
time-series called `example-0.tsv`. The reason for the `0` in the 
name is because, with agent- and rule-based models, it is necessary
to run many instances of the same simulation to get many system 
trajectories. For deterministic models, we only need the one.

Another version of this command,

    ptti -y example.yaml --plot

will cause some simple plots to be created to visualise the output.
They are not very sophisticated but are useful for quickly inspecting
model output. This uses the [Matplotlib] python library, but you could
just as well use [gnuplot]. Some example plots:

## Programmatic interface

To run the models from a python program, for example in a [Jupyter]
notebook, see the `runModel` function in the [ptti/models.py] file.
Its signature is:

    def runModel(model, t0, tmax, steps, parameters={}, initial={},
                 interventions=[], rseries=False, seed=0, **unused):

The first argument is a model class, for example,
`ptti.seirct_ode.SEIRCTODEMem`. The next three arguments give the time
to start the simulation, the end time, and the number of time-steps.
This is followed by parameters and initial conditions. The parameters
all have defaults so you only need to specify those that are different.
Similarly for the initial conditions. To run the model for 300 days 
with a population of 5000000, with 1000 infectious individuals initially
and a conspicuously high testing rate, one would do:

    from ptti.seirct_ode import SEIRCTODEMem
    from ptti.model import runModel
    
    params  = { "theta": 1.0 }
    initial = { "N": 5000000, "IU": 1000 }
    t, traj = runModel(SEIRCTODEMem, 0, 300, 300, params, initial)

and `t` will be an array of times, and `traj` will be an array of 
each observable (compartment) for each time.

Of the other arguments, `interventions` specifies interventions and
`rseries` causes an extra column to be added to the trajectory for the
computed value of the reproduction number at each time. The `seed` 
argument is for the random seed to use and is intended to make 
stochastic simulations repeatable.

[Matplotlib]: https://matplotlib.org
[gnuplot]: http://www.gnuplot.info
[Python]: https://python.org/
[NumPy]: https://numpy.org/
[SciPy]: https://scipy.org/
[Numba]: https://numba.pydata.org/
[Conda]: https://docs.conda.io/en/latest/miniconda.html
[KaSim]: https://kappalanguage.org/
[MPI]: https://www.mpi-forum.org/
[Haskell]: https://www.haskell.org/
[Jupyter]: https://jupyter.org/
[ptti/models.py]: https://github.com/ptti/ptti/blob/master/ptti/model.py
