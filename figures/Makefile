all:
	python methods.py
	pdflatex -shell-escape plots.tex

eps: Fig2.eps Fig3.eps Fig4.eps Fig5.eps Fig6.eps Fig7.eps Fig8.eps Fig9.eps

%.pdf: %.tex
	pdflatex $<

%.eps: %.pdf
	pdftops -eps $< $@

clean:
	rm -f *.tsv *.t *.traj
	rm -f plots-figure*
	rm -f *.aux *.auxlock *.log
	rm -f *.synctex.gz
	rm -f *.eps
	rm -f *.pdf
	rm -f *.dep
	rm -f *.dpth
	rm -f *.md5
