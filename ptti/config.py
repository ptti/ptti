__all__ = ["config_load", "config_save"]

from ptti.plotting import plot_defaults
from ptti.version import platform, python, software, revision

import pkg_resources
import collections
import logging
import numpy as np
import yaml

log = logging.getLogger(__name__)


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=collections.OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def numpy_funcs():
    funcs = ['beta', 'binomial', 'chisquare', 'choice', 'dirichlet', 'exponential', 'gamma',
             'geometric', 'gumbel', 'hypergeometric', 'laplace', 'logistic', 'lognormal',
             'logseries', 'multinomial', 'multivariate_normal', 'negative_binomial',
             'noncentral_chisquare', 'noncentral_f', 'normal', 'pareto', 'poisson', 'power',
             'rand', 'randint', 'randn', 'random_integers', 'random_sample', 'rayleigh',
             'standard_cauchy', 'standard_exponential', 'standard_gamma', 'standard_normal',
             'standard_t', 'triangular', 'uniform', 'vonmises', 'wald', 'weibull', 'zipf']
    return {f: getattr(np.random, f) for f in funcs}


def config_load(filename=None, interventions=None, sample=0, defaults={}):
    """
    Load a YAML configuration file, supporting evaluation of some expressions and
    sensible defaults. The defaults are:

    {'initial': {'IU': 10, 'N': 1000},
     'interventions': {},
     'meta': {'model': 'SEIRCTODEMem',
              'output': 'simdata',
              'samples': 1,
              'steps': 3600,
              't0': 0,
              'tmax': 360},
     'parameters': {}}
    """

    if filename is not None:
        with open(filename) as fp:
            cfg = ordered_load(fp.read(), yaml.FullLoader)
    else:
        cfg = {}
    if 'interventions' not in cfg.keys():
        cfg['interventions'] = []

    if interventions is not None:
        for item in interventions:
            if type(item) == type([]): #Lists have filename, offset
                filename = item[0]
                offset = item[1]
            elif type(item) != type(""):
                raise(NotImplementedError)
            else:
                filename = item
                offset = 0
            with open(filename) as fp:
                interventionset = ordered_load(fp.read(), yaml.FullLoader)
                if offset != 0:
                    for item in interventionset['interventions']:
                        item['time'] = item['time'] + offset
            cfg['interventions'].extend(interventionset['interventions'])

    cfg['interventions'].sort(key=lambda k: ("time" not in k, k.get("time", 100000)))

    gvars = defaults.copy()
    gvars["sample"] = sample
    gvars.update(numpy_funcs())

    for k, v in cfg.items():
        # collect global variables from initialisation
        if k == "initial":
            for i, iv in v.items():
                gvars[i] = iv

        # compute global parameters
        if k == "parameters":
            v.update(_eval_params(v, gvars))

        if k == "interventions":
            for intv in v:
                for ik, iv in intv.items():
                    if ik == "parameters":
                        iv.update(_eval_params(iv, gvars))

    # set some defaults
    cfg.setdefault("meta", {})
    cfg["meta"].setdefault("model", "SEIRCTODEMem")
    cfg["meta"].setdefault("t0", 0)
    cfg["meta"].setdefault("tmax", 365)
    cfg["meta"].setdefault("steps", 365)
    cfg["meta"].setdefault("samples", 1)
    cfg["meta"].setdefault("seed", 0)
    cfg["meta"].setdefault("output", "simdata")
    cfg["meta"].setdefault("rseries", True)
    cfg["meta"].setdefault("plots", plot_defaults)
    cfg["meta"].setdefault("title", "PTTI Simulation")
    cfg["meta"].setdefault("start", "2020/01/01")
    cfg["meta"].setdefault("date", False)

    if cfg["meta"].setdefault("platform", platform) != platform:
        log.warning("Config platform ({}) differs from {}".format(
            cfg["meta"]["platform"], platform))
    if cfg["meta"].setdefault("software", software) != software:
        log.warning("Config software version ({}) differs from {}".format(
            cfg["meta"]["software"], software))
    if cfg["meta"].setdefault("revision", revision) != revision:
        log.warning("Config software revision ({}) differs from {}".format(
            cfg["meta"]["revision"], revision))
    if cfg["meta"].setdefault("python", python) != python:
        log.warning("Config Python version ({}) differs from {}".format(
            cfg["meta"]["python"], python))

    cfg.setdefault("initial", {})
    cfg["initial"].setdefault("N", 1000)
    cfg["initial"].setdefault("IU", 10)

    cfg.setdefault("parameters", {})
    cfg.setdefault("interventions", {})

    return cfg


def _eval_params(d, gvars):
    """
    Warning, mutates the gvars dictionary by adding parameters into it
    """
    params = {}
    for k, v in d.items():
        if isinstance(v, str):
            params[k] = eval(v, gvars)
        else:
            params[k] = v
        gvars[k] = params[k]
        #print("setting {} to {} = {}".format(k, v, params[k]))
    return params


def config_save(cfg, filename, listcast=False):

    # Deep cast to normal python types
    def cast_tolist(cfg):
        if type(cfg) != dict:
            return cfg
        for k, v in cfg.items():
            if hasattr(v, 'tolist'):
                cfg[k] = v.tolist()
            else:
                cfg[k] = cast_tolist(v)

        return cfg

    if listcast:
        cfg = cast_tolist(cfg)

    with open(filename, "w") as fp:
        fp.write(yaml.dump(cfg))


def save_human(data, outfile):
    # but intended to produce readable YAML
    def _clean(d):
        if isinstance(d, list):
            return [_clean(x) for x in d]
        elif isinstance(d, dict) or isinstance(d, collections.OrderedDict):
            return { k: _clean(v) for k,v in d.items() }
        elif isinstance(d, np.float64):
            return float(d)
        else:
            return d

    with open(outfile, "w") as fp:
        fp.write(yaml.dump(_clean(data)))
