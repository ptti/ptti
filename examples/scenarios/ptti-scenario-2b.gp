set terminal pdfcairo color enhanced dashed font "cmr10,14" size 8,9
seed="ptti-scenario-2b"
set output sprintf("%s.pdf", seed)
set multiplot layout 3,2
odefile=sprintf("%s-out-0.tsv", seed)
ttfile=sprintf("%s-out-0-testtrace.tsv", seed)
trfile=sprintf("%s-out-0-trcosts.tsv", seed)
tefile=sprintf("%s-out-0-tecosts.tsv", seed)
etimesfile=sprintf("%s-events.gp", seed)

set tics nomirror
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

# These are from the economic model inputs
Hospitalized_Pct_Deaths=0.44
ICU_Fatality=0.59
ICU_Pct=0.17
IFR=0.008
Non_ICU_Fatality=0.36

HF = IFR*Hospitalized_Pct_Deaths/(ICU_Pct*ICU_Fatality+(1-ICU_Pct)*Non_ICU_Fatality)
ICUF = HF*ICU_Pct

set key bottom right
set xdata time
set timefmt "%Y-%m-%d %H:%M:%S"
set format x "%d/%m/%y"

load etimesfile

set xtics rotate by -45 3600*24*30*6

set yrange [1:1e6]
set log y

set arrow from graph 0, first 8000 to graph 1, first 8000 nohead lc 0 dt '--'
plot odefile u 1:(($9+$10)*IFR) w l lw 1.5 lc 0 ti "Deaths", "" u 1:(($7+$8)*HF) w l lw 1.5 lc rgb color_EU ti "Hospitalized", "" u 1:(($7+$8)*ICUF) w l lw 1.5 lc rgb color_IU ti "ICU"

unset log y
unset arrow

set autoscale y
set yrange [0:]
set key top right

# set y2tics 0.5
# set y2range [0:4]

plot odefile u 1:7 w l lw 1.5 lc rgb color_IU ti "I_U", odefile u 1:8 w l lw 1.5 lc rgb color_ID ti "I_D", \
     odefile u 1:4 w l lw 1.5 lc rgb color_SD ti "S_D", odefile u 1:6 w l lw 1.5 lc rgb color_ED ti "E_D", \
     odefile u 1:10 w l lw 1.5 lc rgb color_RD ti "R_D"#, odefile u 1:13 w l axis x1y2 lc 0 ti "R"


plot ttfile u 1:3 w l lw 1.5 lc rgb color_IU ti "Tests", ttfile u 1:4 w l lw 1.5 lc rgb color_ID ti "Traced"

unset log y
unset yrange
set autoscale y
set style fill empty

set ylabel "Staff"
plot trfile u 1:5 w boxes ti "Tracers"

set ylabel "Cost (Millions GBP)"
plot tefile u 1:($5/1000000) w boxes ti "Testing"
plot trfile u 1:($6/1000000) w boxes ti "Tracing"

unset multiplot
set output
