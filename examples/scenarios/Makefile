SAMPLES?= 10
SCENARIOS?= ptti-scenario-1 ptti-scenario-1-Trig \
ptti-scenario-2a ptti-scenario-2b \
ptti-scenario-3a ptti-scenario-3a-Trig ptti-scenario-3b ptti-scenario-3b-Trig \
ptti-scenario-4a ptti-scenario-4b ptti-scenario-4c ptti-scenario-4d \
ptti-scenario-4a-Trig ptti-scenario-4b-Trig ptti-scenario-4c-Trig ptti-scenario-4d-Trig \

all: benchmark compare plot

${SCENARIOS:=-out-0.tsv}: %-out-0.tsv : %.yaml
	TARG=$@; \
	SEED=$${TARG%-out-0.tsv}; \
	ptti -y $$SEED.yaml -m SEIRCTODEMem -o $${TARG%-0.tsv} -e; \
	find . -name $$SEED'-out-0.yaml' -delete

run-ode: ${SCENARIOS:=-out-0.tsv}
	@echo 'Running all ODE models'

${SCENARIOS:=.pdf}: %.pdf : %-out-0.tsv plots_template.gp get_trigger_times.py
	TARG=$@; \
	SEED=$${TARG%.pdf}; \
	python get_trigger_times.py $$SEED; \
	sed 's/@/'$$SEED'/g' plots_template.gp | gnuplot
	
plot: ${SCENARIOS:=.pdf}
	@echo 'Plotting all scenario calculations' 

clean:
	# Remove all files
	find . -name '*-econ.yaml' -delete	
	find . -name '*-events.yaml' -delete	
	find . -name '*-out-*.*' -delete
	find . -name '*.pdf' -delete