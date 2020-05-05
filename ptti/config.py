__all__ = ["config_load"]

import yaml

def config_load(filename):
    """
    Load a YAML configuration file, supporting evaluation of some expressions
    """
    with open(filename) as fp:
        cfg = yaml.load(fp.read(), yaml.FullLoader)

    gvars = {}
    for k, v in cfg.items():
        ## collect global variables from initialisation
        if k == "initial":
            for i, iv in v.items():
                gvars[i] = iv

        ## compute global parameters
        if k == "parameters":
            params = _eval_params(v, gvars)
            gvars.update(params)
            v.update(params)

        if k == "interventions":
            for intv in v:
                for ik, iv in intv.items():
                    if ik == "parameters":
                        iv.update(_eval_params(iv, gvars))
    return cfg

def _eval_params(d, gvars):
    params = {}
    for k, v in d.items():
        if isinstance(v, str):
            params[k] = eval(v, gvars)
        else:
            params[k] = v
    return params
