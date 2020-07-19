
N = 100000
support = {
  "m": [0.1*N, 0.005*N],
  "INIT_I": [0.01*N, 0.001*N, 0.0001*N],
  "k_result": [1.0/2, 12],
  "thetaT": [0.0, 1.0],
  "thetaD": [0.0, 1.0],
  "thetaI": [0.0, 1.0/7]
}

cols = sorted(support.keys())
def enum(cols):
    if cols == []:
        yield []
        return
    c = cols[0]
    for v in support[c]:
        for rest in enum(cols[1:]):
            yield [v] + rest

print("case\t" + "\t".join(cols))
for i, row in enumerate(enum(cols)):
    print(str(i) + "\t" + "\t".join(map(str, row)))
