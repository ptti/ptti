#!/usr/bin/env python3

import argparse
import numpy as np
import csv
from string import digits
from scipy.interpolate import interp1d

def load_kappa(fname, delimiter=","):
    rows = []
    with open(fname) as fp:
        for row in csv.reader(fp):
            if row[0][0] not in digits: continue
            rows.append(list(map(float, row)))
    return np.array(rows)

def head_kappa(fname, delimiter=","):
    with open(fname) as fp:
        for row in csv.reader(fp):
            if row[0].startswith("#"): continue
            return row

if __name__ == '__main__':
    parser = argparse.ArgumentParser("moments", "compute moments from a set of trajectories")
    parser.add_argument("-d", "--delimiter", default="\t", help="Input delimiter (output is always tab)")
    parser.add_argument("-k", "--kappa", default=False, action="store_true", help="Kappa-style CSV")
    parser.add_argument("-o", "--output", required=True, help="Output filename")
    parser.add_argument("-i", "--input", nargs="*", default=[], help="Input files")
    parser.add_argument("-p", "--points", default=None, type=int, help="Number of points for output")

    args = parser.parse_args()

    if args.kappa:
        load = load_kappa
        headrow = head_kappa(args.input[0], delimiter=args.delimiter)
        head = "\t".join(["t"] + headrow[1:])
    else:
        load = np.loadtxt
        head = None

    samples = [load(fn, delimiter=args.delimiter) for fn in args.input]

    times = [sample[:,0]  for sample in samples]
    trajs = [sample[:,1:] for sample in samples]

    mintime = min(np.min(t) for t in times)
    maxtime = max(np.max(t) for t in times)
    points = args.points if args.points is not None else max(len(t) for t in times)

    t = np.linspace(mintime, maxtime, points)

    interp_trajs = [interp1d(times[i], traj.T, kind="previous", fill_value="extrapolate")(t).T for (i,traj) in enumerate(trajs)]

    avg = np.average(interp_trajs, axis=0).T
    std = np.std(interp_trajs, axis=0).T

    np.savetxt(args.output + "-avg.tsv", np.vstack([t, avg]).T, delimiter="\t", encoding="utf-8", comments="", header=head)
    np.savetxt(args.output + "-std.tsv", np.vstack([t, std]).T, delimiter="\t", encoding="utf-8", comments="", header=head)

