SAMPLES = 10
BENCHMARKS = bmark-notest bmark-noct-lowtest bmark-noct-hightest bmark-lowct-lowtest bmark-highct-lowtest \
bmark-lowct-hightest bmark-highct-hightest bmark-highct-verylowtest bmark-small

${BENCHMARKS:=-out-abm-avg.tsv}: %-out-abm-avg.tsv : %.yaml
	TARG=$@; \
	SEED=$${TARG%-out-abm-avg.tsv}; \
	ptti -y $$SEED.yaml -m SEIRCTABM --samples $(SAMPLES) -st -o $${TARG%-avg.tsv}; \
	find . -name $$SEED'-out-abm-*.tsv' ! -name $$SEED'-out-abm-avg.tsv' ! -name $$SEED'-out-abm-std.tsv' -delete; \
	find . -name $$SEED'-out-abm-*.yaml' -delete

run-abm: ${BENCHMARKS:=-out-abm-avg.tsv}
	@echo 'Running all ABM models'

${BENCHMARKS:=-out-0.tsv}: %-out-0.tsv : %.yaml
	TARG=$@; \
	SEED=$${TARG%-out-0.tsv}; \
	ptti -y $$SEED.yaml -m SEIRCTODEMem -o $${TARG%-0.tsv}; \
	find . -name $$SEED'-out-0.yaml' -delete

run-ode: ${BENCHMARKS:=-out-0.tsv}
	@echo 'Running all ODE models'

${BENCHMARKS:=-out-0-err.yaml}: %-out-0-err.yaml : %-out-0.tsv %-out-abm-avg.tsv
	TARG=$@; \
	SEED=$${TARG%-out-0-err.yaml}; \
	ptti-compare $$SEED-out-0.tsv $$SEED-out-abm-avg.tsv --reference-std $$SEED-out-abm-std.tsv -cols 8

compare: ${BENCHMARKS:=-out-0-err.yaml}
	@echo 'Running all comparisons'

benchmark: run-abm run-ode compare
	@echo 'Running benchmark'

clean:
	# Remove all files except ABM results
	find . -name '*-out-*.*' ! -name '*-out-abm-*.*' -delete

clean-all:
	# Remove all files
	find . -name '*-out-*.*' -delete