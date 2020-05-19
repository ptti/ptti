set terminal pdfcairo color enhanced dashed font "cmr10,14" size 8,6
seed="@"
set output sprintf("%s.pdf", seed)
set multiplot layout 2,2
odefile=sprintf("%s-out-0.tsv", seed)
etimesfile=sprintf("%s-events.gp", seed)

set tics nomirror
set xlabel 't (Days)'
set ylabel 'Population'

set yrange [0:]

set style fill transparent solid 0.25 noborder

# Colors
color_SU = '#00aa55'
color_SD = '#007722'

color_EU = '#eba134'
color_ED = '#945e0f'

color_IU = '#9c210e'
color_ID = '#5e160b'

color_RU = '#0055aa'
color_RD = '#002277'

load etimesfile

plot odefile u 1:2 w l lw 1.5 lc rgb color_SU ti "S_U", odefile u 1:3 w l lw 1.5 lc rgb color_SD ti "S_D"
plot odefile u 1:4 w l lw 1.5 lc rgb color_EU ti "E_U", odefile u 1:5 w l lw 1.5 lc rgb color_ED ti "E_D"
plot odefile u 1:6 w l lw 1.5 lc rgb color_IU ti "I_U", odefile u 1:7 w l lw 1.5 lc rgb color_ID ti "I_D"
set key bottom right
plot odefile u 1:8 w l lw 1.5 lc rgb color_RU ti "R_U", odefile u 1:9 w l lw 1.5 lc rgb color_RD ti "R_D"

unset multiplot
set output