import argparse
import pkg_resources
from ptti.config import config_load, config_save, save_human
from ptti.model import runModel
from ptti.plotting import plot
from ptti.economic import calcEconOutputs, calcArgumentsODE
from multiprocessing import Pool
from datetime import datetime, timedelta
import logging as log
import os
import sys
import numpy as np
import yaml

# MPI is an optional dependency for running on HPC systems
try:
    from mpi4py import MPI
except ImportError:
    MPI = None


def _save_datetime(fname, timeaxis, columns, delimiter='\t'):
    with open(fname, 'w') as f:
        for j, t in enumerate(timeaxis):
            f.write('{0}\t{1}\n'.format(t, delimiter.join(map(str, columns[j]))))

def inmpi():
    return "PMIX_RANK" in os.environ


def mpirank():
    return int(os.environ.get("PMIX_RANK", "0"))


log.basicConfig(stream=sys.stdout, level=log.INFO,
                format='%(asctime)s - %(name)s:%(levelname)s - %(message)s')


def command():
    # if we are running in MPI, and we are a worker process, skip all this
    if inmpi() and mpirank() > 0:
        mpiwork()
        sys.exit(0)

    # locate models by name from pkg_resources
    models = {}
    for ep in pkg_resources.iter_entry_points(group='models'):
        models.update({ep.name: ep.load()})

    parser = argparse.ArgumentParser("ptti",
                                     description="Population-wide Testing, Tracing and Isolation Models")
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
    parser.add_argument("--plot", action="store_true",
                        default=False, help="Plot trajectories")
    parser.add_argument("--loglevel", default="INFO",
                        help="Set logging level")
    parser.add_argument("-st", "--statistics", action="store_true",
                        default=False, help="Save average and standard deviation files")
    parser.add_argument("--dump-state", action="store_true",
                        default=False, help="Dump model state and exit")
    parser.add_argument("--parallel", action="store_true",
                        default=False, help="Execute samples in parallel")
    parser.add_argument("-v", "--var", nargs="*", default=[],
                        help="Set variables / parameters")
    parser.add_argument("-e", "--econ", action="store_true", default=False,
                        help="Perform economic analysis")
    parser.add_argument("-d", "--date", action="store_true", default=False,
                        help="Store time axis as dates")
    parser.add_argument("-sp", "--save-param", type=str, nargs="+", default=[],
                        help="Parameters to save a time series of")

    args = parser.parse_args()

    log.basicConfig(stream=sys.stdout, level=getattr(log, args.loglevel),
                    format='%(asctime)s - %(name)s:%(levelname)s - %(message)s')

    def mkcfg(sample):
        cfg = config_load(args.yaml, sample=sample)

        for meta in ("model", "tmax", "steps", "samples", "output", "date"):
            arg = getattr(args, meta)
            if arg is not None:
                cfg["meta"][meta] = arg
        for init in ("N", "IU"):
            arg = getattr(args, init)
            if arg is not None:
                cfg["initial"][init] = arg

        for v in args.var:
            k, v = v.split("=", 1)
            v = float(v)
            cfg["parameters"][k] = v

        if isinstance(cfg["meta"]["model"], str):
            model = models.get(cfg["meta"]["model"])
            if model is None:
                log.error("Unknown model: {}".format(cfg["meta"]["model"]))
                sys.exit(255)
            cfg["meta"]["model"] = model

        log.debug("Config: {}".format(cfg))
        return cfg

    if args.dump_state:
        cfg = mkcfg(0)
        m = cfg["meta"]["model"]()
        m.set_parameters(**cfg["parameters"])
        state = m.initial_conditions(**cfg["initial"])
        print(state)
        sys.exit(0)

    if args.parallel:
        if inmpi():
            pmap = mpimap
        else:
            pmap = Pool().map
    else:
        def pmap(f, v): return list(map(f, v))

    cfg = mkcfg(0)
    samples = [(i, mkcfg(i)) for i in range(cfg["meta"]["samples"])]
    results = pmap(runSample, samples)

    for s, (traj, events, paramtraj) in zip(samples, results):

        i, cfg = s
        outfile = "{}-{}.tsv".format(cfg["meta"]["output"], i)

        t0 = datetime.strptime(cfg["meta"]["start"], '%Y/%m/%d')
        timeaxis = [t0 + timedelta(days=t) for t in traj[:, 0]]

        if not cfg["meta"]["date"]:
            np.savetxt(outfile, traj, delimiter="\t")
        else:
            # We need to store these as dates
            _save_datetime(outfile, timeaxis, traj[:, 1:])

        # Save the parameters
        for sp in args.save_param:
            if sp not in paramtraj:
                print(
                    'Parameter {0} does not exist for chosen model'.format(sp))
                continue

            outfile = "{}-{}-{}.tsv".format(cfg["meta"]["output"], i, sp)

            if not cfg["meta"]["date"]:
                np.savetxt(outfile, np.concatenate([traj[:, 0:1],
                                                    paramtraj[sp][:, None]],
                                                   axis=1),
                           delimiter="\t")
            else:
                # We need to store these as dates
                _save_datetime(outfile, timeaxis, paramtraj[sp][:, None])

            # # Period history
            # period_history = np.zeros(len(timeaxis)).astype(int)
            # if "periods" in cfg:
            #     periodtimes = [datetime.strptime(p, '%Y/%M/%d')
            #                    for p in cfg["periods"]]
            #     for j, t in enumerate(timeaxis):
            #         p_i = 0
            #         while p_i < len(periodtimes):
            #             if t < periodtimes[p_i]:
            #                 break
            #             p_i += 1
            #         period_history[j] = p_i

        cfgout = "{}-{}.yaml".format(cfg["meta"]["output"], i)
        config_save(cfg, cfgout)

        allevents = events + [i for i in cfg["interventions"] if "time" in i]
        allevents = sorted(allevents, key=lambda i: i["time"])
        eout = "{}-{}-events.yaml".format(cfg["meta"]["output"], i)
        save_human(allevents, eout)

        if args.econ:
            # Economic analysis
            t, vals = traj[:, 0], traj[:, 1:]

            econ_args = calcArgumentsODE(traj, paramtraj, cfg)

            econ = calcEconOutputs(**econ_args)
            econout = "{}-{}-econ.yaml".format(cfg["meta"]["output"], i)
            save_human(econ, econout)

            # Also, time series stuff
            ttout = "{}-{}-testtrace.tsv".format(cfg["meta"]["output"], i)

            ttdata = np.concatenate([econ_args['time'][:,None], 
                                     econ_args['tested'][:, None],
                                     econ_args['traced'][:, None]], axis=1)
            if not cfg["meta"]["date"]:
                np.savetxt(ttout, ttdata, delimiter="\t")
            else:
                # We need to store these as dates
                ttaxis = [t0 + timedelta(days=t) for t in ttdata[:, 0]]
                _save_datetime(ttout, ttaxis, ttdata[:,1:])

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

    parser = argparse.ArgumentParser("ptti-compare",
                                     description="Comparison between different runs of the same model")
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
    parser.add_argument("--skip",
                        type=int, default=0,
                        help="Skip the first several datapoints")

    args = parser.parse_args()

    idata = np.loadtxt(args.input)[args.skip:]
    rdata = np.loadtxt(args.reference)[args.skip:]

    if args.reference_std is not None:
        stddata = np.loadtxt(args.reference_std)[args.skip:]
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

    outbase = args.input.rsplit(".", 1)[0]
    errfile = "{}-abserr.tsv".format(outbase)
    np.savetxt(errfile, abserr, delimiter="\t")

    # Integrated absolute errors
    intabserr = np.trapz(np.abs(abserr[:, 1:]), x=abserr[:, 0], axis=0)
    intabserr /= (abserr[-1, 0]-abserr[0, 0])
    report["abserr"] = intabserr.tolist()

    # Relative errors
    relerr = abserr.copy()
    relerr[:, 1:cn+1] /= np.where(rdata[:, 1:cn+1]
                                  != 0, rdata[:, 1:cn+1], np.inf)

    errfile = "{}-relerr.tsv".format(outbase)
    np.savetxt(errfile, relerr, delimiter="\t")

    # Integrated relative errors
    intrelerr = np.trapz(np.abs(relerr[:, 1:]), x=relerr[:, 0], axis=0)
    intrelerr /= (relerr[-1, 0]-relerr[0, 0])
    report["relerr"] = intrelerr.tolist()

    # Normalised errors
    if stddata is not None:
        stderr = abserr.copy()
        stderr[:, 1:cn+1] /= np.where(stddata[:, 1:cn+1]
                                      != 0, stddata[:, 1:cn+1], np.inf)

        errfile = "{}-stderr.tsv".format(outbase)
        np.savetxt(errfile, stderr, delimiter="\t")

        # Integrated normalised errors
        intstderr = np.trapz(np.abs(stderr[:, 1:]), x=stderr[:, 0], axis=0)
        intstderr /= (stderr[-1, 0]-stderr[0, 0])
        report["stderr"] = intstderr.tolist()

    repfile = "{}-err.yaml".format(outbase)
    config_save(report, repfile)


def runSample(arg):
    i, cfg = arg

    # set random seed for the benefit of stochastic simulations
    cfg["meta"]["seed"] = i

    # for indexed samples, select the right parameter:
    for k, v in cfg["parameters"].copy().items():
        if isinstance(v, list):
            cfg["parameters"][k] = v[i]
    for iv in cfg["interventions"]:
        for k, v in iv.copy().items():
            if isinstance(v, list):
                iv[k] = v[i]

    t, traj, events, paramtraj = runModel(**cfg["meta"], **cfg)

    tseries = np.concatenate([t[:, None], traj], axis=1)

    return tseries, events, paramtraj


def mpimap(f, v):
    if MPI is None:
        log.error("Using MPI requires installation of mpi4py")
        sys.exit(255)

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    import logging
    log = logging.getLogger("MPI [{}/{}]".format(rank, size))
    log.info("Running under MPI")

    chunksize = int(len(v)/size)
    if len(v) % size > 0:
        chunksize += 1
    chunks = [v[i*chunksize:(i+1)*chunksize] for i in range(size)]

    chunk = comm.scatter(chunks, root=0)
    log.info("processing chunk of size {}".format(len(chunk)))
    result = list(map(runSample, chunk))
    data = comm.gather(result, root=0)

    return sum(data, [])


def mpiwork():
    if MPI is None:
        log.error("Using MPI requires installation of mpi4py")
        sys.exit(255)

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    import logging
    log = logging.getLogger("MPI [{}/{}]".format(rank, size))
    log.info("MPI worker running".format(rank, size))

    chunk = comm.scatter(None, root=0)
    log.info("processing chunk of size {}".format(len(chunk)))
    result = list(map(runSample, chunk))
    comm.gather(result, root=0)
    log.info("done")


if __name__ == '__main__':
    command()
