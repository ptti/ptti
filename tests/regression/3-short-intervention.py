#!/usr/bin/env python3

from ptti.model import runModel
from ptti.seirct_ode import SEIRCTODEMem
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(name)s:%(levelname)s - %(message)s')

initial = {
  "N": 1e6,
  "IU": 100,
}
interventions = [
  { "time": 10, "parameters": { "c": 5 } },
  { "time": 11, "parameters": { "c": 10 } }
]

result = runModel(SEIRCTODEMem, t0=0, tmax=20, steps=20, initial=initial, interventions=interventions)
