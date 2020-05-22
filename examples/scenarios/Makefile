SCENARIOS?= ptti-scenario-1 ptti-scenario-1-Trig \
ptti-scenario-2a ptti-scenario-2b \
ptti-scenario-3a ptti-scenario-3a-Trig ptti-scenario-3b ptti-scenario-3b-Trig \
ptti-scenario-4a ptti-scenario-4b ptti-scenario-4c ptti-scenario-4d \
ptti-scenario-4a-Trig ptti-scenario-4b-Trig ptti-scenario-4c-Trig ptti-scenario-4d-Trig \
fitting-ukbest

all: plot

${SCENARIOS:=-out-0.tsv}: %-out-0.tsv : %.yaml
	TARG=$@; \
	SEED=$${TARG%-out-0.tsv}; \
	ptti -y $$SEED.yaml -m SEIRCTODEMem -o $${TARG%-0.tsv} -e -d; \
	find . -name $$SEED'-out-0.yaml' -delete

run-ode: ${SCENARIOS:=-out-0.tsv}
	@echo 'Running all ODE models'

${SCENARIOS:=.pdf}: %.pdf : %-out-0.tsv fourpanels.gp get_trigger_times.py
	TARG=$@; \
	SEED=$${TARG%.pdf}; \
	python get_trigger_times.py $$SEED; \
	sed 's/@/'$$SEED'/g' fourpanels.gp | gnuplot
	
## specific rule for fitting plot
fitting-ukbest-out-0.tsv: fitting-ukbest.yaml
	PTTI -y $< -m SEIRCTODEMem -o fitting-ukbest-out; \
	rm -f fitting-ukbest-out-0.yaml

fitting-inferred-cases.tsv: dgu-deaths-20200520.csv
	python dgu_transform.py $< $@

fitting-ukbest.pdf: fitting-ukbest-out-0.tsv fitting-inferred-cases.tsv dgu_transform.py
	python get_trigger_times.py fitting-ukbest;\
	gnuplot fitting.gp

plot: ${SCENARIOS:=.pdf}
	@echo 'Plotting all scenario calculations' 

clean:
	# Remove all files
	find . -name '*-econ.yaml' -delete	
	find . -name '*-events.yaml' -delete	
	find . -name '*-out-*.*' -delete
	find . -name '*.pdf' -delete
