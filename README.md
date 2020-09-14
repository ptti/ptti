# PTTI: Population-wide Testing, Tracing and Isolation

This repository contains software for simulating epidemiological models
of various kinds: compartmental models, agent-based models, network models
and rule-based models. It is intended for studying the effects of testing
and contact tracing for containing disease outbreaks. We call this TTI - Testing, 
tracing and Isolation. The underlying principles are described in our
[SEIR-TTI paper] and used in our [PTTI paper] examining the human and 
economic cost of various interventions. This software contains the following models:

  * SEIRCTABM an agent-based model
  * SEIRCTODEMem an ODE implementation of a compartmental model with
    extra memory states
  * SEIRODE a plain SEIR model for comparison
  * SEIRCTKappa a rule-based model in the [Kappa Language]
  * SEIRCTNet a network model using [Epidemics on Networks]

The software has a variety of useful features:

  * Formalism-agnostic: we believe in checking models against each other,
    as it's the best way to understand which models work best in what 
    circumstances. So we have ordinary differential equation models,
    agent-based models, network, and rule-based models.
  * Simple configuration: simulations are described in a user-friendly
    YAML file (though there is nothing to prevent running them directly
    in [Python] if you wish).
  * Interventions: the simulation is stopped at set times or on certain
    conditions, parameters are changed, and the simulation continues.
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

```sh
conda create -n ptti python=3
conda activate ptti
git clone https://github.com/ptti/ptti
cd ptti
python setup.py develop
```

For rule-based simulations, the [KaSim] kappa-language simulator
should also be installed. It is a separate program that is used
through python bindings. The python bindings are also not installed
by default because some Windows users have trouble installing them.
They should be installed separately with,

```sh
pip install kappy
```

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

 ```yaml
 meta:
  title:  Example simulation
  model:  SEIRCTODEMem
  output: example
initial:
  N:  67000000
  IU: 100000
```

This example is run with the `ptti` command as follows:

```sh
ptti -y example.yaml
```

Doing so will produce a tab-separated output file of the resulting
time-series called `example-0.tsv`. The reason for the `0` in the 
name is because, with agent- and rule-based models, it is necessary
to run many instances of the same simulation to get many system 
trajectories. For deterministic models, we only need the one.

Another version of this command,

```sh
ptti -y example.yaml --plot
```

will cause some simple plots to be created to visualise the output.
They are not very sophisticated but are useful for quickly inspecting
model output. This uses the [Matplotlib] python library, but you could
just as well use [gnuplot]. Some example plots:

<image src="https://github.com/ptti/ptti/raw/master/examples/example-susceptibles.png" width="300" /><image src="https://github.com/ptti/ptti/raw/master/examples/example-exposed.png" width="300" />

<image src="https://github.com/ptti/ptti/raw/master/examples/example-infections.png" width="300" /><image src="https://github.com/ptti/ptti/raw/master/examples/example-removed.png" width="300" />


## Webapp

Installation and usage instructions for the webapp version can be found [in the app folder](app/README.md).


## Advanced usage

The `ptti` program accepts several command-line arguments that modify
its behaviour. In particular, values specified in the `.yaml`
configuration file can be overridden:

```
usage: ptti [-h] [-m MODEL] [-N N] [-IU IU] [--tmax TMAX] [--steps STEPS] [--samples SAMPLES]
            [-y YAML] [-o OUTPUT] [-R] [--plot] [--loglevel LOGLEVEL] [-st] [--dump-state]
            [--parallel] [-v [VAR [VAR ...]]]

Population-wide Testing, Tracing and Isolation Models

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL, --model MODEL
                        Select model: SEIRCTABM, SEIRCTKappa, SEIRCTODEMem, SEIRODE
  -N N                  Population size
  -IU IU                Initial infected population
  --tmax TMAX           Simulation end time
  --steps STEPS         Simulation reporting time-steps
  --samples SAMPLES     Number of samples
  -y YAML, --yaml YAML  YAML file describing parameters and interventions
  -o OUTPUT, --output OUTPUT
                        Output filename
  --plot                Plot trajectories
  --loglevel LOGLEVEL   Set logging level
  -st, --statistics     Save average and standard deviation files
  --dump-state          Dump model state and exit
  --parallel            Execute samples in parallel
  -v [VAR [VAR ...]], --var [VAR [VAR ...]]
                        Set variables / parameters
```

For example, we may wish to run `100` iterations of an agent-based model, and 
output statistics about the average trajectory and its standard deviation, while
making sure to use all available processors,
```sh
ptti -y example.yaml -m SEIRCTABM --samples 100 --statistics --parallel
```

Or we may wish to sweep through a variety of testing rates,
```sh
for t in 0.0 0.1 0.2 0.3 0.4 0.5; do
    ptti -y example.yaml -o example-theta${t} -v theta=${t}
done
```
or even a nested loop to try different combinations of infection rate and 
contact rate:
```sh
for b in 0.028 0.030 0.032 0.034; do
    for c in 8 10 12 14 16; do
        ptti -y example.yaml -o example-beta${b}-c${c} -v beta=${b} c=${c}
    done
done
```

For these kinds of exercises, the excellent [GNU Parallel] can be very
helpful.

## Benchmarks and Reproducing our SEIR-TTI paper data

The software comes with a set of benchmarks exploring various cases
for parameter choices. These are in the `benchmarks/` subdirectory
and are driven by a `Makefile`. Be sure to have [GNU Make] installed,
and simply run,
```sh
cd benchmarks
make benchmark compare plot
```

It is possible to pass some parameters to the `make`, such as the
specific benchmark to use (by default it will do all of them) and the
number of samples to take from the ABM. For example, to reproduce
the data for Figure 7 in our [SEIR-TTI paper], it would be:
```sh
make BENCHMARKS=bmark-sweet SAMPLES=100 benchmark compare plot
```
Figures 7 and 8 are produced from `bmark-sweet.yaml` and
`bmark-highct-verylowtest.yaml` respectively.

The data underlying Figures 2-6 are produced in a different way. They
are generated by the python script `examples/tti-paper.py`.
This script can simply be run from the command line,
```sh
python examples/tti-paper.py
```
This script is also a good example of using the programmatic interface
to the PTTI software, described below.

## Programmatic interface

To run the models from a python program, for example in a [Jupyter]
notebook, see the `runModel` function in the [ptti/models.py] file.
Its signature is:

```python
def runModel(model, t0, tmax, steps, parameters={}, initial={},
             interventions=[], rseries=True, seed=0, **unused)
```

The first argument is a model class, for example,
`ptti.seirct_ode.SEIRCTODEMem`. The next three arguments give the time
to start the simulation, the end time, and the number of time-steps.
This is followed by parameters and initial conditions. The parameters
all have defaults so you only need to specify those that are different.
Similarly for the initial conditions. To run the model for 300 days 
with a population of 5000000, with 1000 infectious individuals initially
and a conspicuously high testing rate, one would do:

```python
from ptti.seirct_ode import SEIRCTODEMem
from ptti.model import runModel

params  = { "theta": 1.0 }
initial = { "N": 5000000, "IU": 1000 }
t, traj, events = runModel(SEIRCTODEMem, 1, 300, 300, params, initial)
```

and `t` will be an array of times, and `traj` will be an array of 
each observable (compartment) for each time. `events` will be a list of
events caused by conditional interventions. A full example of this
programmatic use is available in [examples/ukfitting.py].

Of the other arguments, `interventions` specifies interventions.
The `seed` argument is for the random seed to use and is intended to
make stochastic simulations repeatable.

The parameters that are understood by a model, and the observables
that it provides can be retrieved from the corresponding model 
properties:

```python
>>> pprint(model.parameters)
{'alpha': {'default': 0.2, 'descr': 'incubation rate'},
 'beta': {'default': 0.033, 'descr': 'transmission probability'},
 'c': {'default': 13.0, 'descr': 'contact rate'},
 'chi': {'default': 0.25, 'descr': 'tracing rate'},
 'eta': {'default': 0.5, 'descr': 'tracing success probability'},
 'gamma': {'default': 0.1429, 'descr': 'recovery rate'},
 'kappa': {'default': 0.0714, 'descr': 'isolation exit rate'},
 'theta': {'default': 0.0714, 'descr': 'testing rate'}}
>>> pprint(model.observables)
[{'descr': 'susceptible and unconfined', 'name': 'SU'},
 {'descr': 'susceptible and distanced', 'name': 'SD'},
 {'descr': 'exposed and unconfined', 'name': 'EU'},
 {'descr': 'infectious and distanced', 'name': 'ED'},
 {'descr': 'infectious and unconfined', 'name': 'IU'},
 {'descr': 'infectious and distanced', 'name': 'ID'},
 {'descr': 'removed and unconfined', 'name': 'RU'},
 {'descr': 'removed and distanced', 'name': 'RD'},
 {'descr': 'traceable and susceptible', 'name': 'CIS'},
 {'descr': 'traceable and exposed', 'name': 'CIE'},
 {'descr': 'traceable and infectious', 'name': 'CII'},
 {'descr': 'traceable and exposed', 'name': 'CIR'}]
```

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
[GNU Parallel]: https://www.gnu.org/software/parallel/
[examples/ukfitting.py]: https://github.com/ptti/ptti/blob/master/examples/ukfitting.py
[SEIR-TTI paper]: https://github.com/ptti/ptti/raw/master/docs/tti.pdf
[PTTI paper]: https://github.com/ptti/ptti/raw/master/docs/PTTI-Covid-19-UK.pdf
[GNU Make]: https://www.gnu.org/software/make/
[Kappa Language]: http://kappalanguage.org/
[Epidemics on Networks]: https://epidemicsonnetworks.readthedocs.io/
