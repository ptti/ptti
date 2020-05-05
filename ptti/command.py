import argparse
import pkg_resources
from ptti.config import config_load
from ptti.model import runModel
import logging as log
import sys
import numpy as np

def command():
    models = {}
    for ep in pkg_resources.iter_entry_points(group='models'):
        models.update({ep.name: ep.load()})

    parser = argparse.ArgumentParser("Population-wide Testing, Tracing and Isolation Models")
    parser.add_argument("-m", "--model", default="SEIRCTODEMem",
                        help="Select model: {}".format(", ".join(models.keys())))
    parser.add_argument("-N", type=int, default=1000,
                        help="Population size")
    parser.add_argument("-I", type=int, default=None,
                        help="Initial infected population")
    parser.add_argument("--tmax", type=float, default=100.0,
                        help="Simulation end time")
    parser.add_argument("--steps", type=int, default=1000,
                        help="Simulation reporting time-steps")
    parser.add_argument("--samples", type=int, default=1,
                        help="Number of samples")
    parser.add_argument("-y", "--yaml", default=None,
                        help="YAML file describing parameters and interventions")
    parser.add_argument("-o", "--output", type=str,
                        default="simdata", help="Output filename")
    parser.add_argument("-R", "--rseries", action="store_true",
                        default=False, help="Compute R along the time-series")
    parser.add_argument("--loglevel", default="INFO",
                        help="Set logging level")
    parser.add_argument("--dump-state", action="store_true",
                        default=False, help="Dump model state and exit")

    args = parser.parse_args()

    log.basicConfig(stream=sys.stdout, level=getattr(log, args.loglevel),
                    format='%(asctime)s - %(levelname)s - %(message)s')

    cfg = config_load(args.yaml)

    if args.I is not None:
        cfg["initial"]["IU"] = args.I

    if args.model not in models:
        log.error("Unknown model: {}".format(args.model))
        sys.exit(255)

    model = models[args.model]

    if args.dump_state:
        m = model()
        m.set_parameters(**cfg["parameters"])
        state = m.initial_conditions(**cfg["initial"])
        print(state)
        sys.exit(0)

    for i in range(args.samples):
        t, traj = runModel(model, 0, args.tmax, args.steps, rseries=args.rseries, **cfg)

        tseries = np.vstack([t, traj.T]).T

        np.savetxt("{}-{}.tsv".format(args.output, i), tseries, delimiter="\t")

if __name__ == '__main__':
    command()
