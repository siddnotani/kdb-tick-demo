/ Market-data analytics loaded into the RDB and HDB.
/ Functions take in-memory tables so they work on today's RDB data and on HDB slices alike.

\d .mkt

/ rows of table tab (symbol name) for date d and symbols s; empty s means all symbols.
/ The HDB (partitioned, has a date column) is filtered by date; the RDB only holds today.
slice:{[tab;d;s]
  s:(),s;
  w:$[count s;enlist(in;`sym;enlist s);()];
  if[`date in cols tab; :delete date from ?[tab;(enlist(=;`date;d)),w;0b;()]];
  if[not d=.z.D; '"rdb only holds ",string .z.D];
  ?[tab;w;0b;()]}

/ volume-weighted average price, volume and trade count per symbol
vwap:{[t] select vwap:size wavg price, volume:sum size, trades:count i by sym from t}

/ OHLCV bars of width w (a timespan, e.g. 0D00:05) per symbol
bars:{[t;w] select open:first price, high:max price, low:min price, close:last price, volume:sum size by sym, time:w xbar time from t}

/ trades joined to the prevailing quote (as-of join on sym and time)
withQuotes:{[tr;qt] aj[`sym`time;tr;`sym`time xasc select time,sym,bid,ask from qt]}

/ quoted spread per symbol, in price and basis points of mid
spread:{[qt] select avgSpread:avg ask-bid, avgSpreadBps:avg 1e4*(ask-bid)%0.5*bid+ask by sym from qt}

/ transaction cost analysis: size-weighted slippage vs prevailing mid in bps (positive = paid away)
tca:{[tr;qt]
  t:update mid:0.5*bid+ask from withQuotes[tr;qt];
  select slippageBps:size wavg 1e4*(?[side=`B;1f;-1f])*(price-mid)%mid, notional:sum price*size by sym from t}

\d .
