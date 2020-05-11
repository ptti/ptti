from glob import glob
import yaml
import re
import numpy as np

fre = re.compile(r"^(abm1)-.*-([0-9][0-9])k.*-err*.yaml")

stderrors = []
relerrors = []
for fname in glob("*-err.yaml"):
    print(fname)
    m = fre.match(fname)
    greek, value = m.groups()
    with open(fname) as fp:
        data = yaml.load(fp.read(), yaml.FullLoader)
    stderr = data["stderr"]
    stderr.insert(0, float(value)*1000)
    stderrors.append(stderr)

    relerr = data["relerr"]
    relerr.insert(0, float(value)*1000)
    relerrors.append(relerr)

stderrors = np.array(sorted(stderrors, key=lambda r: r[0]))
relerrors = np.array(sorted(relerrors, key=lambda r: r[0]))

np.savetxt("{}-stderrors.tsv".format(greek), stderrors, delimiter="\t")
np.savetxt("{}-relerrors.tsv".format(greek), relerrors, delimiter="\t")

