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
                        help="Select model: {}".format(", ".join(
                            models.keys())))
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
                        help="YAML file describing parameters and "
                        "interventions")
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


def compare():
    # Compare two different runs of the same model, gauge one vs. the other
    # and produce various metrics

    parser = argparse.ArgumentParser(
        "Comparison between different runs of the same model")
    parser.add_argument("input",
                        help=".tsv file containing the results to compare")
    parser.add_argument("reference",
                        help=".tsv file containing the reference results")
    parser.add_argument("--reference-std", "-rstd",
                        type=str, default=None,
                        help=".tsv file containing the standard deviation"
                        " of the reference results. If not present, only"
                        " compute absolute errors")
    parser.add_argument("--columns", "-cols",
                        type=int, default=None,
                        help="Number of columns of the two models to compare"
                        ". The first x columns will be compared")

    args = parser.parse_args()

    idata = np.loadtxt(args.input)
    rdata = np.loadtxt(args.reference)

    if args.reference_std is not None:
        stddata = np.loadtxt(args.reference_std)
        if stddata.shape != rdata.shape:
            raise RuntimeError("Invalid reference standard deviation data")
    else:
        stddata = None

    cn = args.columns
    if cn is None:
        cn = min(idata.shape[1], rdata.shape[1]) - 1
        print("Comparing first {0} columns".format(cn))
    elif cn > min(idata.shape[1], rdata.shape[1]):
        raise RuntimeError("Not enough columns in one or both models")

    # Sanity check
    if ((idata.shape[0] != rdata.shape[0]) or
            not np.all(idata[:, 0] == rdata[:, 0])):
        raise RuntimeError("The two time axes don't match")

    L = idata.shape[0]
    report = {}

    # Absolute errors
    abserr = np.zeros((L, cn+1))
    abserr[:, 0] = idata[:, 0]
    abserr[:, 1:] = idata[:, 1:cn+1]-rdata[:, 1:cn+1]

    errfile = "{}-abserr.tsv".format(args.input.split('.')[0])
    np.savetxt(errfile, abserr, delimiter="\t")

    # Integrated absolute errors
    intabserr = np.trapz(abserr[:, 1:], x=abserr[:, 0], axis=0)
    intabserr /= (abserr[-1, 0]-abserr[0, 0])
    report["abserr"] = intabserr.tolist()

    # Relative errors
    relerr = abserr.copy()
    relerr[:, 1:cn+1] /= np.where(rdata[:, 1:cn+1]
                                  != 0, rdata[:, 1:cn+1], np.inf)

    errfile = "{}-relerr.tsv".format(args.input.split('.')[0])
    np.savetxt(errfile, relerr, delimiter="\t")

    # Integrated relative errors
    intrelerr = np.trapz(relerr[:, 1:], x=relerr[:, 0], axis=0)
    intrelerr /= (relerr[-1, 0]-relerr[0, 0])
    report["relerr"] = intrelerr.tolist()

    # Normalised errors
    if stddata is not None:
        stderr = abserr.copy()
        stderr[:, 1:cn+1] /= np.where(stddata[:, 1:cn+1]
                                      != 0, stddata[:, 1:cn+1], np.inf)

        errfile = "{}-stderr.tsv".format(args.input.split('.')[0])
        np.savetxt(errfile, stderr, delimiter="\t")

        # Integrated normalised errors
        intstderr = np.trapz(stderr[:, 1:], x=stderr[:, 0], axis=0)
        intstderr /= (stderr[-1, 0]-stderr[0, 0])
        report["stderr"] = intstderr.tolist()

    repfile = "{}-err.yaml".format(args.input.split('.')[0])
    config_save(report, repfile)


def runSamples(arg):
    i, cfg = arg

    t, traj = runModel(**cfg["meta"], **cfg)

    tseries = np.vstack([t, traj.T]).T

    # increment random seed for the benefit of stochastic simulations
    cfg["meta"]["seed"] += 1

    return tseries


if __name__ == '__main__':
    command()
