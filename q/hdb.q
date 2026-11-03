/ Historical database with the analytics library loaded.
/ q q/hdb.q [hdb dir] -p 5012

\l q/analytics.q
system"l ",$[count .z.x;first .z.x;"data/sym"]
