#!/bin/bash

module load git
module load openmpi

. "/lustre/home/dc030/oww/miniconda3/etc/profile.d/conda.sh"
conda activate ptti

YAML=abm1.yaml

ptti -N 10000 -IU 100 -m SEIRCTODEMem -y $YAML -o abm1-ode-10k
ptti -N 20000 -IU 100 -m SEIRCTODEMem -y $YAML -o abm1-ode-20k
ptti -N 30000 -IU 100 -m SEIRCTODEMem -y $YAML -o abm1-ode-30k
ptti -N 40000 -IU 100 -m SEIRCTODEMem -y $YAML -o abm1-ode-40k
#ptti -N 50000 -IU 100 -m SEIRCTODEMem -y $YAML -o abm1-ode-50k

ptti-compare --skip 30 --reference-std abm1-10k-std.tsv abm1-ode-10k-0.tsv abm1-10k-avg.tsv
ptti-compare --skip 30 --reference-std abm1-20k-std.tsv abm1-ode-20k-0.tsv abm1-20k-avg.tsv
ptti-compare --skip 30 --reference-std abm1-30k-std.tsv abm1-ode-30k-0.tsv abm1-30k-avg.tsv
ptti-compare --skip 30 --reference-std abm1-40k-std.tsv abm1-ode-40k-0.tsv abm1-40k-avg.tsv
#ptti-compare --skip 30 --reference-std abm1-50k-std.tsv abm1-ode-50k-0.tsv abm1-50k-avg.tsv
