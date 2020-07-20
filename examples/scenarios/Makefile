#SCENARIOS?= ptti-scenario-1 ptti-scenario-1-Trig \
ptti-scenario-2a ptti-scenario-2a-Trig ptti-scenario-2b ptti-scenario-2b-Trig \
ptti-scenario-3a ptti-scenario-3a-Trig ptti-scenario-3b ptti-scenario-3b-Trig \
ptti-scenario-4a ptti-scenario-4b ptti-scenario-4c ptti-scenario-4d \
ptti-scenario-4a-Trig ptti-scenario-4b-Trig ptti-scenario-4c-Trig ptti-scenario-4d-Trig \
ptti-scenario-4d-Trig10 ptti-scenario-4d-Trig20 ptti-scenario-4d-Trig30 \
ptti-scenario-4d-Trig40 ptti-scenario-4d-Trig50 ptti-scenario-4d-Trig60 ptti-scenario-4d-Trig70 \
ptti-scenario-3b-Trig10 ptti-scenario-3b-Trig20 ptti-scenario-3b-Trig30 \
ptti-scenario-3b-Trig30-3mo ptti-scenario-3b-Trig00-3mo ptti-scenario-3b-Trig00

#SCENARIOS?= ptti-scenario-No_TTI ptti-scenario-No_TTI_Lockdown_Triggers \
ptti-scenario-Targeted_PTTI ptti-scenario-Targeted_PTTI_Face_Coverings \
ptti-scenario-Targeted_PTTI_Face_Coverings_Lockdown_Triggers \
ptti-scenario-Targeted_PTTI_Lockdown_Triggers \
ptti-scenario-Targeted_PTTI_TracingSuccess30_Face_Coverings_Lockdown_Triggers \
ptti-scenario-Targeted_PTTI_TracingSuccess40_Face_Coverings_Lockdown_Triggers \
ptti-scenario-Targeted_PTTI_TracingSuccess50_Face_Coverings_Lockdown_Triggers \
ptti-scenario-Untargeted_PTTI \
ptti-scenario-Untargeted_PTTI_Face_Coverings \
ptti-scenario-Untargeted_PTTI_Face_Coverings_Lockdown_Triggers \
ptti-scenario-Untargeted_PTTI_Lockdown_Triggers \
ptti-scenario-Untargeted_PTTI_TracingSuccess0_Face_Coverings_Lockdown_Triggers \
ptti-scenario-Untargeted_PTTI_TracingSuccess30_Face_Coverings_Lockdown_Triggers \
ptti-scenario-Untargeted_to_Targeted_PTTI_Face_Coverings_Lockdown_Triggers

SCENARIOS?= ptti-1_No_TTI_Lockdown_Triggers \
ptti-2_Universal_PTTI ptti-3_Universal_PTTI_Face_Coverings ptti-4_Universal_PTTI_Face_Coverings_Lockdown_Triggers \
ptti-5_Targeted_TTI ptti-6_Targeted_TTI_Face_Coverings ptti-7_Targeted_TTI_Face_Coverings_Lockdown_Triggers

PYTHON=python3

all: plot fitting-ukbest.pdf

${SCENARIOS:=-out-0.tsv}: %-out-0.tsv : %.yaml
	TARG=$@; \
	SEED=$${TARG%-out-0.tsv}; \
	ptti -y $$SEED.yaml -m SEIRCTODEMem -o $${TARG%-0.tsv} -e -d; \
	find . -name $$SEED'-out-0.yaml' -delete

run-ode: ${SCENARIOS:=-out-0.tsv}
	@echo 'Running all ODE models'

${SCENARIOS:=.pdf}: %.pdf : %.gp
	gnuplot $<

${SCENARIOS:=.gp}: %.gp : %-out-0.tsv fourpanels.gp get_trigger_times.py
	TARG=$@; \
	SEED=$${TARG%.gp}; \
	${PYTHON} get_trigger_times.py $$SEED; \
	${PYTHON} econseries.py $$SEED; \
	sed 's/@/'$$SEED'/g' fourpanels.gp > $@
	
## specific rule for fitting plot
fitting-ukbest-out-0.tsv: fitting-ukbest.yaml
	ptti -y $< -m SEIRCTODEMem -o fitting-ukbest-out -e; \
	rm -f fitting-ukbest-out-0.yaml

fitting-inferred-cases.tsv: dgu-deaths-20200520.csv
	${PYTHON} dgu_transform.py $< $@

fitting-ukbest.pdf: fitting-ukbest-out-0.tsv fitting-inferred-cases.tsv dgu_transform.py
	${PYTHON} get_trigger_times.py fitting-ukbest;\
	gnuplot fitting.gp

plot: ${SCENARIOS:=.pdf}
	@echo 'Plotting all scenario calculations' 

clean:
	# Remove all files
	find . -name '*-econ.yaml' -delete	
	find . -name '*-events.yaml' -delete	
	find . -name '*-out-*.*' -delete
	find . -name '*.pdf' -delete
