"""
This file is a work-around for Windows. Some of the models use libraries
that don't work properly on Windows. The ABM uses the numba just-in-time
compiler. The rule-based model uses kappy that has problems compiling.

The command-line program `ptti` imports all of the models to allow choosing
one by name. These imports fail in the above circumstance. This file is
a shim providing a layer of indirection to catch these failures and allow
execution to proceed, with fewer models.
"""

try:
    from ptti.seirct_ode import SEIRODE
except:
    SEIRODE = None

try:
    from ptti.seirct_ode import SEIRCTODEMem
except:
    SEIRCTODEMem = None

try:
    from ptti.seirct_abm import SEIRCTABM
except:
    SEIRCTABM = None

try:
    from ptti.seirct_abm import SEIRCTABMDet
except:
    SEIRCTABMDet = None

try:
    from ptti.seirct_kappa import SEIRCTKappa
except:
    SEIRCTKappa = None

try:
    from ptti.seirct_eon import SEIRCTNet
except:
    SEIRCTNet = None
