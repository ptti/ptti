# Assumptions underlying the PTTI computational model

As [Sridhar and Majumder] argue, it is crucially important to understand the
limitations of computational models and the data used to calibrate them. The
model given here is intended for exploration of the relative consequences of
different actions and policy interventions under different conditions.

There are two fundamentally different kinds of assumptions at play. Structural
assumptions that are a consequence of the formulation of the model itself. These
are eternally true in the sense that if the model is calibrated with parameters
for different disease outbreaks, the structural assumptions are still there and
need to be understood. Assumptions about data, meanwhile, are particular to
calibration of the model to a specific outbreak. Data about a novel pathogen
causing a pandemic of proportions not seen for a century are simply too scarce
and inconsistent, particularly in the early days, to accurately calibrate any
model without assumptions about the meaning and reliability of the data. Neither
class of assumption presents insurmountable problems but they are important to
recognise in order to understand what can, and cannot, be learned from a model.

## Structural assumptions

We refer specifically to the [SEIR-TTI ODE model] with economic extensions as
[implemented] in the [PTTI software]. This is fundamentally a SEIR
compartmental model simulated with ordinary differential equations (ODE)s.
The extensions to include testing, tracing and isolation (TTI) are based on
a careful probabilistic argument that we discuss in detail in that paper.
This formulation means that there are automatically several underlying
assumptions, for which we provide justification here.

### The outbreak is sufficiently large

The outbreak, and each susceptible, exposed, infectious and removed cohort is of
sufficient size that it is coherent to simulate it with ODEs. This is not the
case in the very early days with dozens or small numbers of hundreds of cases
where stochastic methods would be more appropriate. This is also not the case if
the outbreak is nearly completely suppressed.

*Justification:* we are studying management strategies for large outbreaks.
That is the circumstance where ODEs are applicable.

### The outbreak or epidemic is homogeneous in space and time.

In reality, the UK is undergoing several COVID-19 outbreaks. The outbreak in
Edinburgh is perhaps 10 days behind that in London. The outbreak in the North of
England began declining well after London. Distancing interventions such as
lock-down happened simultaneously throughout the UK but are being released at
different times.

In general, a model of a single large outbreak cannot be used to reproduce
the dynamics of smaller outbreaks separated in time. This is easily seen
with the simplest of models (e.g. SIR) if outbreaks are widely spaced in
time. Simulating the large outbreak with such a model will produce a curve for,
say, infections, with one peak. Simulating two small outbreaks individually will
each produce a peak at a different time. Adding the results of simulating the
small outbreaks produces a curve with two peaks, different from the result of
simulating the large outbreak.

This model does not represent those different, coupled outbreaks, it represents
a single outbreak.

*Justification:* this is a simplifying assumption. In the case of COVID-19, the
major outbreaks in the most populous cities are separated in time by only a
couple of generations. We argue that this is close enough that, to a first
approximation, the differences can be disregarded and valid insights gained by
considering the ensemble as one large outbreak. Furthermore, it is possible to
use the same model to study individual outbreaks.

### The population is homogeneous

The population is homogeneous and each individual behaves in the same way and is
affected in the same way by the virus. This is manifestly untrue of the real
world. It introduces the limitation that the model will not tell us how specific
segments of society are affected and whether different strategies would be
appropriate for different groups.

*Justification:* this is another simplifying assumption. The subject of this
study is testing, tracing and isolation. We wish to know the effect of this
on the population level and how it interacts with other interventions for a
large outbreak. This is not a well-studied topic and for this reason we
examine it for a simple population before introducing more complex structure.
It is possible to build an analogous stratified model to account for more
population structure and we leave this as future work.

### Testing happens sufficiently frequently

The nature of our [contact tracing approximation], triggered by testing, is such
that it requires that testing happen on the same time-scale as disease
progression, or faster.

*Justification:* it is not realistic to expect that testing individuals after
they have recovered from the disease or died would be useful for contact
tracing.

### Contact tracing is proportional to having at least one contact

Our [contact tracing approximation] is formulated such that contacts are traced
at a rate proportional to their chance of having had at least one contact with
an infectious individual. An alternative formulation could trace proportional
to the number of infectious contacts: if one has had two infectious contacts,
then perhaps one is twice is likely to be traced.

*Justification:* this is a conservative assumption. It may underestimate the
effectiveness of contact tracing for outbreak suppression. For policy purposes,
it is better to under-promise and over-deliver than the reverse.

## Assumptions about the data

The available data for the UK COVID-19 epidemic presents several challenges. The
central government releases data about deaths in the whole of the UK as well as
Scotland, Wales and Northern Ireland on the [data.gov.uk coronavirus web site]
as well as the number of cases reported in England and Wales.

The availability of tests both in hospital settings and among different groups
of workers and individuals has changed over time and varies by location, and the
supply and provision of tests continues to be constrained. Because the reported cases
depend on testing, these data are difficult to interpret reliably. Due to the
lack of seroprevalence testing we also do not know the true number of cases in
the population. Attempting to fit a model that produces a definite number of
instantaneous or cumulative cases to such data is a fool's errand. We therefore
disregard this data.

Mortality data is better but also suffers problems. Reporting of
coronavirus-related deaths in hospitals is thought to be relatively consistent
across the UK. The criterion for reporting of deaths outside of hospitals as
coronavirus-related has changed in time and has differed by region. We
nevertheless attempt to calibrate our model to this mortality data, estimating
that it is not as severely defective as the case data.

Calibration of our model to mortality data involves some facts and some
assumptions.

### Fact: lock-down throughout the UK began on the 23rd of March

Although we suspect a slowing of activity and reduction in contact for at least 
a week before lockdown was ordered, we are only certain that it was ordered
effective the 23rd of March. The effect of this is a reduction of the average
contact rate as of that date.

### Fact: lock-down was eased in England on the 13th of May

Although we cannot say by how much contact increased on the 13th of May, some
economic activity resumed in England on that day. Data that reflects this is, at
the time of writing sparse and very recent.

### Assumption: british people have, on average, 13 contacts per day

This value, represented in our model as *c*, comes from the literature
[citation] and reflects normal life. The main effect of distancing measures is
to change this value.

### Assumption: the latent and infectious periods are 5 and 7 days, respectively

We know from clinical studies [citation] that the incubation/latent period when
infected individuals are not yet infectious is about 5 days. We likewise know
that the infectious phase of the disease lasts approximately a week, after which
the individuals either recover or become severely ill.

### Assumption: severely ill individuals are removed through hospitalisation

We assume that all severely ill individuals are hospitalised, and that
conditions within hospitals are such as prevent onward transmission. This has
consequences because the reciprocal of the parameter *γ* appears in the model as
the duration of infectiousness and is fixed at one week.

*Justification:*

### Assumption: the overall infection fatality rate (IFR) is 0.008

The model does not explicitly produce a time-series for the number of dead.
Rather, it produces the number of individuals removed through recovery or death.
To calibrate against mortality data it is necessary to count the dead. To do
this, we need to know what fraction of infections result in death. Estimates
vary and reflection in the model as the probability of infection (and
consequently the overall force of the epidemic) depends strongly on this value.

*Justification:* scientific consensus appears to be converging on an IFR of
around 0.8% for the UK, justified by the IFR in China being estimated as [0.66%] 
and the UK population being older, as well as by a recent large scale seroprevalence 
survey of 70,000 people in Spain showing 5.0% infected to date (2.35m people) meaning
an IFR there of 1.15% given the 27,100 Covid-19 deaths there. However we conduct 
sensitivity analysis on the resulting infectiousness parameter to understand how 
this affects the behaviour of the model.

## Fitting the data

Our strategy is not to find which model parameters are *determined by* the data,
but to find those that are *consistent with* the data and also with the broader
scientific consensus. The [PTTI software] includes a tool, `ptti-fit`, for
calibrating the model to mortality data. The fitting is conducted using the
[fitting scenario] that includes three interventions:

  * on the 18th of February
  * on the 23rd of March
  * on the 13th of May

The first intervention represents a notional start to the epidemic implied by
the UK government figures under our model. However, we do not believe this to be
the true date as discussed below.

The number of contacts per unit time, *c*, was fixed at 1, and the
infectiousness, *β*, was allowed to vary. No testing or contact tracing was
included in the model for fitting purposes. Without contact tracing, the
effects of *β* and *c* are indistinguishable so no information is lost by
simply fixing *c* to 1.

To compute the difference between the model output and the mortality data we
used the *L2 norm* or Euclidean distance, as is standard practice for nonlinear
optimisation. We minimised this distance using the [Nelder-Mead simplex algorithm],
allowing infectiousness to vary independently in each time-period.

The result of this fitting exercise is shown below,

<image src="https://github.com/ptti/ptti/raw/master/examples/scenarios/fitting-ukbest.png" width="400" />

The vertical lines indicate the interventions and the case data begins on the
6th of March. The values for *β* that were discovered by the optimisation
process are,

  * 0.1529 (equivalent to R = 1) from the first of January to the 12th of February
  * 1.59   (equivalent to R = 11) from the 12th of February until lock-down
  * 0.1529 (equivalent to R = 1) during lock-down

Of these, only the third is meaningful. The first may be disregarded as it is
before the notional start of the epidemic implied by the UK government mortality
data. Seeding the simulation on the first of January with one infectious
individual, a value implying that R = 1 will maintain this until the notional
start of the epidemic. That this was found automatically through fitting is
a sanity check for identifying the 12th of February as the key date.

The second figure of 1.59 (R = 11) during the initial phase of the epidemic is
conspicuously high and this bears explanation. Firstly, there is a large degree
of uncertainty here: a fit of comparable quality equivalent to R = 8 is also
possible. Nevertheless, the early UK government data implies a much larger value
than we believe to be correct. This can be clearly seen from the figure
presented on a logarithmic scale. This value can be revised downwards easily by
moving the notional start of the epidemic earlier and a value close to the
scientific consensus value is obtained towards the end of December or the
beginning of January, the specific date not being very influential for obtaining
this value. The resulting curve, however, no longer matches the initial data.

The final figure of 0.1529 (R = 1) during lock-down appears to be robust against
all efforts to vary the starting date and intervention timing, varying from
slightly below to slightly above. Whilst the initial UK government data is
suspect, the later data appears more reliable.

On this basis, then, we can infer that *if* it is correct that lock-down reduces
contact by 70% [citation] *then* the initial value for the infectiousness should
be 0.51, implying R0 of 3.5, at the high end of the range of scientific
consensus. By adjusting the notional start of the epidemic to be in late
December or early January, we obtain such an initial value without perturbing
the fit or value of infectiousness during the lock-down period.

## Adjustment to dates

Recall that this model assumes individuals are removed through hospitalisation
or death. From what we have observed of disease progression, the second phase of
the illness leading to death typically lasts 2-3 weeks. If the mean is 18 days,
this means that, when fitting to mortality data with this model, an adjustment
of 18 days is required. Therefore, measured as the first active case, the date
implied by the UK government data is not the 12th of February but the 25th of
January, and by the above argument, we believe the true beginning of the
epidemic in the UK to be in mid-December.

## Conclusions from fitting

We therefore conclude that the following are *consistent with* the data:

  1. The UK government data implies an unreasonably high infectiousness and the
     epidemic beginning on the 25th of January.
  2. The COVID-19 epidemic in the UK was probably seeded at in the middle to end
     of December 2019.
  3. The reproduction number for a completely susceptible population in the
     absence of any interventions is about 3.3, implying an appropriate value
     for *β* in our full model (*c* equal to 13 without interventions) of 0.036.

Acknowledging the uncertainty in the data, and inherent in our reasoning above,
we also conduct a sensitivity analysis, exploring scenarios where infectiousness
is slightly below, and slightly above this value to ascertain the effectiveness
of the measures that we propose here.

Fitting can be verified by downloading the mortality data from the
[data.gov.uk coronavirus web site] and running the command,
```sh
ptti-fit -y fitting.yaml --dgu coronavirus-deaths_latest.csv --mask c theta --ifr 0.008
```
where `fitting.yaml` is the [fitting scenario] in the `examples/` subdirectory
of the [PTTI software] distribution.

[Sridhar and Majumder]: https://www.bmj.com/content/369/bmj.m1567
[SEIR-TTI ODE model]: https://github.com/ptti/ptti/raw/master/docs/tti.pdf
[contact tracing approximation]: https://github.com/ptti/ptti/raw/master/docs/tti.pdf
[0.66%]: https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(20)30243-7/fulltext
[PTTI software]: http://github.com/ptti/ptti
[implemented]: https://github.com/ptti/ptti/blob/master/ptti/seirct_ode.py#L35
[data.gov.uk coronavirus web site]: https://coronavirus.data.gov.uk/
[fitting scenario]: https://github.com/ptti/ptti/blob/master/examples/fitting.yaml
[Broyden-Fletcher-Goldfarb-Shanno]: https://www.encyclopediaofmath.org/index.php/Broyden-Fletcher-Goldfarb-Shanno_method
[Nelder-Mead simplex algorithm]: http://www.scholarpedia.org/article/Nelder-Mead_algorithm
