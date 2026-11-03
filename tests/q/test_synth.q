\l q/synth.q

system"S 7"
q:.synth.quotes[.synth.px0;1000;0D09:30;0D16:00]
tr:.synth.trades[q;200]

.t.eq["quote count";count q;1000]
.t.eq["quote columns";cols q;`time`sym`bid`ask`bsize`asize]
.t.eq["trade columns";cols tr;`time`sym`price`size`side`venue]
.t.ok["quotes sorted by time";(asc q`time)~q`time]
.t.ok["trades sorted by time";(asc tr`time)~tr`time]
.t.ok["bid below ask";all q[`bid]<q`ask]
.t.ok["quotes in session";all q[`time] within 0D09:30 0D16:00]
.t.ok["trades only known syms";all tr[`sym] in .synth.syms]
.t.ok["trades print at bid or ask";all tr[`price] in q[`bid],q`ask]
.t.ok["prices positive";all 0<q`bid]

system"S 7"
.t.eq["seeded generation is deterministic";.synth.quotes[.synth.px0;1000;0D09:30;0D16:00];q]

m:.synth.lastMid q
.t.eq["lastMid covers every sym";asc key m;asc distinct q`sym]
