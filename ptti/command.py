import argparse
import pkg_resources
from ptti.config import config_load, config_save
from ptti.model import runModel
from ptti.plotting import plot
from multiprocessing import Pool
import logging as log
import sys
import numpy as np

log.basicConfig(stream=sys.stdout, level=log.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s')


def command():
    models = {}
    for ep in pkg_resources.iter_entry_points(group='models'):
        models.update({ep.name: ep.load()})

    parser = argparse.ArgumentParser(
        "Population-wide Testing, Tracing and Isolation Models")
    parser.add_argument("-m", "--model", default=None,
                        help="Select model: {}".format(", ".join(models.keys())))
    parser.add_argument("-N", type=int, default=None,
                        help="Population size")
    parser.add_argument("-IU", type=int, default=None,
                        help="Initial infected population")
    parser.add_argument("--tmax", type=float, default=None,
                        help="Simulation end time")
    parser.add_argument("--steps", type=int, default=None,
                        help="Simulation reporting time-steps")
    parser.add_argument("--samples", type=int, default=None,
                        help="Number of samples")
    parser.add_argument("-y", "--yaml", default=None,
                        help="YAML file describing parameters and interventions")
    parser.add_argument("-o", "--output", type=str,
                        default=None, help="Output filename")
    parser.add_argument("-R", "--rseries", action="store_true",
                        default=False, help="Compute R along the time-series")
    parser.add_argument("--plot", action="store_true",
                        default=False, help="Plot trajectories")
    parser.add_argument("--loglevel", default="INFO",
                        help="Set logging level")
    parser.add_argument("-st", "--statistics", action="store_true",
                        default=False,
                        help="Save average and standard deviation files")
    parser.add_argument("--dump-state", action="store_true",
                        default=False, help="Dump model state and exit")
    parser.add_argument("--parallel", action="store_true",
                        default=False, help="Execute samples in parallel")

    args = parser.parse_args()

    log.basicConfig(stream=sys.stdout, level=getattr(log, args.loglevel),
                    format='%(asctime)s - %(levelname)s - %(message)s')

    def mkcfg(sample):
        cfg = config_load(args.yaml, sample)
        log.debug("Config: {}".format(cfg))

        for meta in ("model", "tmax", "steps", "samples", "rseries", "output"):
            arg = getattr(args, meta)
            if arg is not None:
                cfg["meta"][meta] = arg
        for init in ("N", "IU"):
            arg = getattr(args, init)
            if arg is not None:
                cfg["initial"][init] = arg

        if isinstance(cfg["meta"]["model"], str):
            model = models.get(cfg["meta"]["model"])
            if model is None:
                log.error("Unknown model: {}".format(cfg["meta"]["model"]))
                sys.exit(255)
            cfg["meta"]["model"] = model

        return cfg

    if args.dump_state:
        m = model()
        m.set_parameters(**cfg["parameters"])
        state = m.initial_conditions(**cfg["initial"])
        print(state)
        sys.exit(0)

    if args.parallel:
        pmap = Pool().map
    else:
        def pmap(f, v): return list(map(f, v))

    cfg = mkcfg(0)
    samples = [(i, mkcfg(i)) for i in range(cfg["meta"]["samples"])]
    trajectories = pmap(runSamples, samples)

    for s, traj in zip(samples, trajectories):

        i, cfg = s
        outfile = "{}-{}.tsv".format(cfg["meta"]["output"], i)
        np.savetxt(outfile, traj, delimiter="\t")

        cfgout = "{}-{}.yaml".format(cfg["meta"]["output"], i)
        config_save(cfg, cfgout)

    if args.statistics:
        # Average trajectory?
        tt = np.array(trajectories)
        tavg = np.average(tt[:, :, 1:], axis=0)
        tstd = np.std(tt[:, :, 1:], axis=0)

        tavg = np.concatenate([tt[0, :, 0:1], tavg], axis=1)
        tstd = np.concatenate([tt[0, :, 0:1], tstd], axis=1)

        avgfile = "{}-avg.tsv".format(cfg["meta"]["output"])
        np.savetxt(avgfile, tavg, delimiter="\t")

        stdfile = "{}-std.tsv".format(cfg["meta"]["output"])
        np.savetxt(stdfile, tstd, delimiter="\t")

    if args.plot:
        plot(**cfg["meta"], **cfg)


def runSamples(arg):
    i, cfg = arg

    t, traj = runModel(**cfg["meta"], **cfg)

    tseries = np.vstack([t, traj.T]).T

    # increment random seed for the benefit of stochastic simulations
    cfg["meta"]["seed"] += 1

    return tseries


if __name__ == '__main__':
    command()
