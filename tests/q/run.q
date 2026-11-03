/ Minimal q test runner: loads every tests/q/test_*.q, prints a summary, exits 1 on any failure.
/ q tests/q/run.q -q

.t.pass:0
.t.fail:0
.t.eq:{[name;actual;expected]
  $[actual~expected;
    .t.pass+:1;
    [.t.fail+:1; -2"FAIL ",name,"\n  expected: ",(-3!expected),"\n  actual:   ",-3!actual]];}
.t.ok:{[name;cond] .t.eq[name;cond;1b]}
.t.throws:{[name;f;arg] .t.eq[name;@[{x y;0b}[f];arg;{1b}];1b]}

.t.root:system"cd"
.t.files:asc f where (f:key `:tests/q) like "test_*.q"
{[f]
  @[system;"l tests/q/",string f;{[f;e] .t.fail+:1; -2"ERROR ",string[f],": ",e}[f]];
  system"cd ",.t.root;
  } each .t.files;

-1 string[.t.pass]," passed, ",string[.t.fail]," failed";
exit 0<.t.fail
