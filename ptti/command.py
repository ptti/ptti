import argparse
import pkg_resources
import yaml
from ptti.model import runModel
import logging as log
import sys
import numpy as np

log.basicConfig(stream=sys.stdout, level=log.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s')

def command():
    models = {}
    for ep in pkg_resources.iter_entry_points(group='models'):
        models.update({ep.name: ep.load()})

    parser = argparse.ArgumentParser("Population-wide Testing, Tracing and Isolation Models")
    parser.add_argument("-N", type=int, default=1000,
                        help="Population size")
    parser.add_argument("-I", type=int, default=10,
                        help="Initial infected population")
    parser.add_argument("--tmax", type=float, default=100.0,
                        help="Simulation end time")
    parser.add_argument("--steps", type=int, default=1000,
                        help="Simulation reporting time-steps")
    parser.add_argument("--samples", type=int, default=1,
                        help="Number of samples")
    parser.add_argument("-m", "--model", default="SEIRCTODEMem",
                        help="Select model: {}".format(", ".join(models.keys())))
    parser.add_argument("-y", "--yaml", default=None,
                        help="YAML file describing parameters and interventions")
    parser.add_argument("-o", "--output", type=str,
                        default="simdata", help="Output filename")

    args = parser.parse_args()

    cfg = {
        "initial": {
            "N":  9900,
            "IU":  100,
        },
        "parameters": {},
        "interventions": [],
    }

    if args.yaml is not None:
        with open(args.yaml) as fp:
            ycfg = yaml.load(fp.read(), loader=yaml.FullLoader)
            for section in ["initial", "parameters"]:
                cfg.update(ycfg.get(section, {}))
            cfg["interventions"] = ycfg.get("interventions", [])

    if args.model not in models:
        log.error("Unknown model: {}".format(args.model))
        sys.exit(255)

    model = models[args.model]

    for i in range(args.samples):
        t, traj = runModel(model, 0, args.tmax, args.steps, **cfg)

        tseries = np.vstack([t, traj.T]).T
        
        np.savetxt("{}-{}.tsv".format(args.output, i), tseries, delimiter="\t")

if __name__ == '__main__':
    command()
