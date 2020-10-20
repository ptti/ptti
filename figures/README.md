
The files in this directory are used to make the plots for the paper. The
routines in `methods.py` generate data and munge it into a form where 
`pgfplots` can read it. To make the plots (there are actually more than
appear in the paper) it is necessary to have the `ptti` software installed
in the way described in the installation instructions. It is also necessary
to have a `LaTeX` installation that includes `tikz` and `pgfplots`. It is
also necessary to have `make`. Either GNU Make or BSD Make will do. To
build the plots it should be sufficient to run

    make

and, after a little while, that will produce a `plots.pdf` and individual
PDF files of the figures. It does this by running,

    python methods.py
    pdflatex -shell-escape plots.tex

