/ Deterministic synthetic market data shared by q/feed.q and q/gen_hdb.q.
/ Prices follow a per-symbol random walk; trades print at the prevailing bid or ask.

\d .synth

syms:`JPM`GS`MS`BAC`C`WFC
venues:`XNYS`XNAS`BATS`IEXG
px0:syms!195 470 115 42 68 62f

round2:{0.01*floor 0.5+100*x}

/ mid price per event: each symbol walks independently from px[sym]
mids:{[px;s;r]
  {[px;s;r;m;k] i:where s=k; @[m;i;:;px[k]*prds 1+r i]}[px;s;r]/[(count s)#0n;distinct s]}

/ n quotes with times uniformly spread over [start;end), sorted by time
quotes:{[px;n;start;end]
  s:n?key px;
  m:mids[px;s;0.0004*-1+2*n?1f];
  h:0.01*1+n?2;
  ([]time:asc start+n?end-start;sym:s;bid:round2 m-h;ask:round2 m+h;bsize:100*1+n?20;asize:100*1+n?20)}

/ n trades sampled from quote table q, printing 1ms after the quote they hit
trades:{[q;n]
  i:asc n?count q;
  side:n?`B`S;
  ([]time:1000000+q[`time] i;sym:q[`sym] i;price:?[side=`B;q[`ask] i;q[`bid] i];size:100*1+n?10;side:side;venue:n?venues)}

/ last mid per symbol, used to carry the walk forward between batches (spread is symmetric, so no drift)
lastMid:{[q] exec last 0.5*bid+ask by sym from q}

\d .
