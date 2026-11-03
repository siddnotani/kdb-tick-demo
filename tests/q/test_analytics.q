\l q/analytics.q

tr:([]time:0D09:30 0D09:31 0D09:32 0D09:33;sym:`JPM`JPM`JPM`GS;price:100 101 102 400f;size:100 200 100 50;side:`B`S`B`S;venue:4#`XNYS)
qt:([]time:0D09:29 0D09:30:30 0D09:31:30 0D09:32:30;sym:`JPM`JPM`JPM`GS;bid:99.98 100.98 101.98 399.9;ask:100.02 101.02 102.02 400.1;bsize:4#100;asize:4#100)

v:.mkt.vwap tr
.t.eq["vwap JPM";v[`JPM;`vwap];101f]
.t.eq["vwap GS";v[`GS;`vwap];400f]
.t.eq["volume JPM";v[`JPM;`volume];400]
.t.eq["trade count";v[`JPM;`trades];3]

b:.mkt.bars[tr;0D00:02]
.t.eq["bars keys";key b;([]sym:`GS`JPM`JPM;time:0D09:32 0D09:30 0D09:32)]
.t.eq["bar ohlc";b[`sym`time!(`JPM;0D09:30)];`open`high`low`close`volume!(100 101 100 101f),300]

j:.mkt.withQuotes[tr;qt]
.t.eq["aj picks prevailing bid";j`bid;99.98 100.98 101.98 399.9]
.t.eq["aj keeps trade rows";count j;count tr]

s:.mkt.spread qt
.t.ok["spread JPM";1e-9>abs s[`JPM;`avgSpread]-0.04]
.t.ok["spread bps GS";1e-9>abs s[`GS;`avgSpreadBps]-5f]

c:.mkt.tca[tr;qt]
/ JPM buy at 100 vs mid 100: 0bps; sell at 101 vs mid 101: 0bps; buy at 102 vs mid 102: 0bps
.t.ok["tca zero when filled at mid";1e-9>abs c[`JPM;`slippageBps]]
.t.eq["tca notional";c[`GS;`notional];20000f]

c2:.mkt.tca[([]time:enlist 0D09:30;sym:`JPM;price:100.02;size:100;side:`B;venue:`XNYS);qt]
.t.ok["tca buy at ask pays half spread";1e-9>abs c2[`JPM;`slippageBps]-2f]
