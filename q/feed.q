/ Synthetic feed handler: publishes quotes and trades to the tickerplant on a timer.
/ q q/feed.q [-tp host:port] [-batch n] [-t ms]

\l q/synth.q

.feed.args:.Q.opt .z.x
.feed.opt:{[k;default] $[k in key .feed.args;first .feed.args k;default]}
.feed.h:hopen `$":",.feed.opt[`tp;"localhost:5010"]
.feed.batch:"J"$.feed.opt[`batch;"20"]
.feed.px:.synth.px0

.feed.step:{[]
  q:.synth.quotes[.feed.px;.feed.batch;0D;0D00:00:00.001];
  .feed.px,:.synth.lastMid q;
  tr:.synth.trades[q;.feed.batch div 4];
  / the tickerplant stamps time, so send every column except time
  (neg .feed.h)(".u.upd";`quote;1_value flip q);
  (neg .feed.h)(".u.upd";`trade;1_value flip tr);}

.z.ts:{.feed.step[]}
.z.pc:{if[x=.feed.h; -2"tickerplant closed the connection"; exit 1]}
if[not system"t"; system"t 200"]
