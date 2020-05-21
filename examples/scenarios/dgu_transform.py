from ptti.fit import dgu
from sys import argv
import numpy as np

inf = argv[1]
outf = argv[2]

d = dgu(inf)

d = np.vstack([d[:,0], d[:,1]/0.008]).T

np.savetxt(outf, d, delimiter="\t")

