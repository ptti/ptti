#!/usr/bin/env python

from setuptools import setup, find_packages

long_description = """
Models for Population-wide Testing, Tracing and Isolation.

This package contains tools for exploratory modelling of interventions
to control the propagation of epidemics and the economic consequences
thereof. The models employ multiple paradigms including numerical
integration and stochastic simulation of compartmental systems,
agent-based models and network models. Tools for analysis and visualisation
of model output are also provided.
"""

setup(name='ptti',
    version='0.1',
    description='Population-wide Testing, Tracing and Isolation Models',
    long_description=long_description,
    url='https://github.com/ptti/ptti',
    author=['Tim Colbourn', 'David Manheim', 'Jasmina Panovska-Griffiths',
            'Simone Sturniolo', 'William Waites'],
    author_email='ww@groovy.net',
    keywords=['differential equations', 'agent-based models',
              'compartment models', 'economics', 'ecology', 'epidemiology',
              'ecology', 'reactions', 'gillespie'],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Intended audience
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',

        # Topics
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Life',
        'Topic :: Scientific/Engineering :: Chemistry',

        # License
        'License :: OSI Approved :: MIT License',
        # Specify the Python versions you support here. In particular,
        # ensure that you indicate whether you support Python 2, Python 3
        # or both.
        'Programming Language :: Python :: 3',
    ],
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'compyrtment',
        'kappy',
        'matplotlib',
        'numpy',
    ],
    python_requires='>=3.1.*'
)
