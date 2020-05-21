#set terminal pdfcairo color enhanced dashed font "cmr10,14" size 8,6
set terminal png
seed="fitting-ukbest"
set output sprintf("%s.png", seed)
odefile=sprintf("%s-out-0.tsv", seed)
ukfile="fitting-inferred-cases.tsv"
etimesfile=sprintf("%s-events.gp", seed)

set tics nomirror
set xlabel 'Days since 2020/01/01'
set ylabel 'Cumulative infections'

set yrange [0:]

set style fill transparent solid 0.25 noborder

# Colors
color_S = '#00aa55'
color_D = '#eba134'

color_RU = '#0055aa'
color_RD = '#002277'

load etimesfile

set key top left
set logscale y
set arrow from 49, graph 0 to 49, graph 1 nohead lt 3
set arrow from 82, graph 0 to 82, graph 1 nohead lt 3
set arrow from 136, graph 0 to 136, graph 1 nohead lt 3

plot odefile u 1:($8+$9) w l lw 2 lc rgb color_S ti "Simulated", ukfile u 1:2 w l lw 2 lc rgb color_D ti "Data"
