import pkg_resources
import csv
import time
import numpy as np
from ptti.seirct_ode import SEIRODE

def uk_mortality():
    raise NotImplementedError('UK mortality data unavailable')
    def read_csv():
        fn = pkg_resources.resource_filename("ptti", "data/uk_mortality.csv")
        with open(fn) as fp:
            for date, cases, deaths in csv.reader(fp, delimiter=','):
                if date == "date": ## header
                    continue
                date = time.strptime(date, "%d/%m/%Y")
                cases, deaths = int(cases), int(deaths)
                yield (date.tm_yday, cases, deaths)
    return np.array(list(read_csv()))

def fit_beta():
    m = SEIRODE()

    data = uk_mortality()

    N = 67000000
    I0 = 1.0/N
    points = [ {"t": t, "RU": r*1.5/(0.008*N)} for t,_,r in data ]
    init = {"SU0": 1-I0, "EU0": 0, "IU0": I0, "RU0": 0 }
    print(init)

    return m.fit_beta(N, init, points)
