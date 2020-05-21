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
[implemented] in the [PTTI software]. This is fundamentally a SEIR a
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
considering the ensemble as one large outbreak.

### The population is homogeneous

The population is homogeneous and each individual behaves in the same way and is
affected in the same way by the virus. This is manifestly untrue of the real
world. It introduces the limitation that the model will not tell us how specific
segments of society are affected and whether different strategies would be
appropriate for different groups.

*Justification:* This is another simplifying assumption. The subject of this
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

*Justification:* It is not realistic to expect that testing individuals after
they have recovered from the disease or died would be useful for contact
tracing.

### Contact tracing is proportional to having at least one contact

Our [contact tracing approximation] is formulated such that contacts are traced
at a rate proportional to their chance of having had at least one contact with
an infectious individual. An alternative formulation could trace proportional
to the number of infectious contacts: if one has had two infectious contacts,
then perhaps one is twice is likely to be traced.

*Justification:* This is a conservative assumption. It may underestimate the
effectiveness of contact tracing for outbreaks suppression. For policy purposes,
it is better to under-promise and over-deliver than the reverse.

## Assumptions about the data

This software package includes a tool, `ptti-fit`. 

[Sridhar and Majumder]: https://www.bmj.com/content/369/bmj.m1567
[SEIR-TTI ODE model]: https://github.com/ptti/ptti/raw/master/docs/tti.pdf
[contact tracing approximation]: https://github.com/ptti/ptti/raw/master/docs/tti.pdf
[PTTI software]: http://github.com/ptti/ptti
[implemented]: https://github.com/ptti/ptti/blob/master/ptti/seirct_ode.py#L35
