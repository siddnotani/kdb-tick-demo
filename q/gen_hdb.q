/ Writes several weekdays of synthetic history to a date-partitioned HDB, then exits.
/ q q/gen_hdb.q [-db data/sym] [-days 5] [-quotes 50000]

\l q/synth.q

.gen.args:.Q.opt .z.x
.gen.opt:{[k;default] $[k in key .gen.args;first .gen.args k;default]}
.gen.db:hsym `$.gen.opt[`db;"data/sym"]
.gen.days:"J"$.gen.opt[`days;"5"]
.gen.n:"J"$.gen.opt[`quotes;"50000"]

/ the most recent n weekdays before today (2000.01.01 was a Saturday, so mod 7 > 1 is Mon-Fri)
.gen.dates:{[n] d:.z.D-1+til 7+2*n; asc neg[n]#asc d where 1<(`long$d) mod 7}

system"S 42"
.gen.px:.synth.px0
{[d]
  quote::.synth.quotes[.gen.px;.gen.n;0D09:30;0D16:00];
  trade::.synth.trades[quote;.gen.n div 4];
  .gen.px::.synth.lastMid quote;
  .Q.dpft[.gen.db;d;`sym] each `quote`trade;
  -1"wrote ",string d;
  } each .gen.dates .gen.days;

exit 0
