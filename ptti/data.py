import pkg_resources
import csv
import time
import numpy as np
from ptti.seirct_ode import SEIRODE

def uk_mortality():
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

    N = 67000000
    data = [ {"t": t, "RU": r} for t,_,r in uk_mortality() ]
    data.append({"t": 0, "SU": N-1, "EU": 0, "IU": 1, "RU": 0 })

    return m.fit_beta(N, data)
