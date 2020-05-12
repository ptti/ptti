set terminal pdfcairo color enhanced dashed font "cmr10,14" size 8,6
seed="@"
set output sprintf("%s.pdf", seed)
set multiplot layout 2,1
odefile=sprintf("%s-out-0.tsv", seed)
avgfile=sprintf("%s-out-abm-avg.tsv", seed)
stdfile=sprintf("%s-out-abm-std.tsv", seed)
joinfile=sprintf("< join %s %s", avgfile, stdfile)

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

plot joinfile u 1:($2-3*$11):($2+3*$11) w filledcu lc rgb color_SU notitle, joinfile u 1:($2-2*$11):($2+2*$11) w filledcu lc rgb color_SU notitle, joinfile u 1:($2-$11):($2+$11) w filledcu lc rgb color_SU notitle, \
joinfile u 1:($3-3*$12):($3+3*$12) w filledcu lc rgb color_SD notitle, joinfile u 1:($3-2*$12):($3+2*$12) w filledcu lc rgb color_SD notitle, joinfile u 1:($3-$12):($3+$12) w filledcu lc rgb color_SD notitle, \
joinfile u 1:($8-3*$17):($8+3*$17) w filledcu lc rgb color_RU notitle, joinfile u 1:($8-2*$17):($8+2*$17) w filledcu lc rgb color_RU notitle, joinfile u 1:($8-$17):($8+$17) w filledcu lc rgb color_RU notitle, \
joinfile u 1:($9-3*$18):($9+3*$18) w filledcu lc rgb color_RD notitle, joinfile u 1:($9-2*$18):($9+2*$18) w filledcu lc rgb color_RD notitle, joinfile u 1:($9-$18):($9+$18) w filledcu lc rgb color_RD notitle, \
joinfile u 1:2 w l lc rgb color_SU dt '--' notitle, joinfile u 1:3 w l lc rgb color_SD dt '--' notitle, \
joinfile u 1:8 w l lc rgb color_RU dt '--' notitle, joinfile u 1:9 w l lc rgb color_RD dt '--' notitle, \
odefile u 1:2 w l lw 1.5 lc rgb color_SU ti "S_U", odefile u 1:3 w l lw 1.5 lc rgb color_SD ti "S_D", \
odefile u 1:8 w l lw 1.5 lc rgb color_RU ti "R_U", odefile u 1:9 w l lw 1.5 lc rgb color_RD ti "R_D"
plot joinfile u 1:($4-3*$13):($4+3*$13) w filledcu lc rgb color_EU notitle, joinfile u 1:($4-2*$13):($4+2*$13) w filledcu lc rgb color_EU notitle, joinfile u 1:($4-$13):($4+$13) w filledcu lc rgb color_EU notitle, \
joinfile u 1:($5-3*$14):($5+3*$14) w filledcu lc rgb color_ED notitle, joinfile u 1:($5-2*$14):($5+2*$14) w filledcu lc rgb color_ED notitle, joinfile u 1:($5-$14):($5+$14) w filledcu lc rgb color_ED notitle, \
joinfile u 1:($6-3*$15):($6+3*$15) w filledcu lc rgb color_IU notitle, joinfile u 1:($6-2*$15):($6+2*$15) w filledcu lc rgb color_IU notitle, joinfile u 1:($6-$15):($6+$15) w filledcu lc rgb color_IU notitle, \
joinfile u 1:($7-3*$16):($7+3*$16) w filledcu lc rgb color_ID notitle, joinfile u 1:($7-2*$16):($7+2*$16) w filledcu lc rgb color_ID notitle, joinfile u 1:($7-$16):($7+$16) w filledcu lc rgb color_ID notitle, \
joinfile u 1:4 w l lc rgb color_EU dt '--' notitle, joinfile u 1:5 w l lc rgb color_ED dt '--' notitle, \
joinfile u 1:6 w l lc rgb color_IU dt '--' notitle, joinfile u 1:7 w l lc rgb color_ID dt '--' notitle, \
odefile u 1:4 w l lw 1.5 lc rgb color_EU ti "E_U", odefile u 1:5 w l lw 1.5 lc rgb color_ED ti "E_D", \
odefile u 1:6 w l lw 1.5 lc rgb color_IU ti "I_U", odefile u 1:7 w l lw 1.5 lc rgb color_ID ti "I_D"
unset multiplot
set output