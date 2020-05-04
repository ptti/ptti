__all__ = ["rseries"]

import numpy as np

def rseries(t, S, beta, c, gamma, N):
    """
    Compute the function R(t) for the reproduction number according to the provided
    time-series for the susceptible population. Taken from S9.3 of
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6002118/
    """
    n = len(t)
    ker = np.exp(-gamma*t)

    bcs = beta*c*S
    Rs = []
    for i, tau in enumerate(t):
        s = np.pad(bcs, (n-i-1, 0), mode="edge")
        Rs.append(np.trapz(s[:n]*ker[::-1]/N, t))
    return np.array(Rs)
