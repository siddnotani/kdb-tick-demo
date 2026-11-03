\l q/analytics.q

/ RDB mode: tables without a date column only hold today
trade:([]time:0D09:30 0D09:31;sym:`JPM`GS;price:100 400f;size:100 50;side:`B`S;venue:`XNYS`XNYS)
.t.eq["slice filters syms";exec sym from .mkt.slice[`trade;.z.D;`JPM];enlist`JPM]
.t.eq["slice empty syms means all";count .mkt.slice[`trade;.z.D;`symbol$()];2]
.t.eq["slice atom sym";count .mkt.slice[`trade;.z.D;`GS];1]
.t.throws["slice rejects other dates in rdb";.mkt.slice[`trade;;`JPM];.z.D-1]
delete trade from `.
