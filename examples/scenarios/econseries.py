import numpy as np
import yaml
import sys
from datetime import datetime, timedelta
from ptti.config import config_load

slug = sys.argv[1]

with open(slug + "-out-0-econ.yaml") as fp:
    econ = yaml.safe_load(fp)

cfg = config_load(slug + ".yaml")
t0 = datetime.strptime(cfg["meta"]["start"], '%Y/%m/%d')

tracers = np.array(econ["Tracing"]["Tracers"])
trcosts  = np.array(econ["Tracing"]["Tracing_Costs"])
tblocks = np.array(econ["Tracing"]["Tracing_Block_Lengths"])
trtimes  = [t0 + timedelta(days=t) for t in np.cumsum(tblocks) - tblocks/2]
trdat = np.vstack([trtimes, tracers, trcosts]).T

tecosts  = np.array(econ["Testing"]["Testing_Costs"])
tblocks = np.array(econ["Testing"]["Testing_Block_Lengths"])
tetimes  = [t0 + timedelta(days=t) for t in np.cumsum(tblocks) - tblocks/2]
tedat = np.vstack([tetimes, tecosts]).T

for (times, dat, fn) in [(trtimes, trdat, slug+"-out-0-trcosts.tsv"), (tetimes, tedat, slug+"-out-0-tecosts.tsv")]:
    with open(fn, "w+") as fp:
        for i in range(len(times)):
            row = "\t".join(map(str, [times[i]] + list(dat[i])))
            fp.write(row)
            fp.write("\n")

def flatten_json(d):
    rows = []
    for k in sorted(d.keys()):
        rows.append([k])
        sub = d[k]
        for j in sorted(sub.keys()):
            if isinstance(sub[j], list):
                rows.append(["", j] + sub[j])
            else:
                rows.append(["", j, sub[j]])
    return rows

rows = flatten_json(econ)
maxlen = max(map(len, rows))
with open(slug + "-out-0-econ.tsv", "w+") as fp:
    for row in rows:
        padded = row + [""]*(maxlen-len(row))
        fp.write("\t".join(map(str, padded)))
        fp.write("\n")
