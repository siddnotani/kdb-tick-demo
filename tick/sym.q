/ Schemas published by the tickerplant. time and sym must be the first two columns.
/ time is stamped by the tickerplant (timespan since midnight, local time).
trade:([]time:`timespan$();sym:`g#`symbol$();price:`float$();size:`long$();side:`symbol$();venue:`symbol$())
quote:([]time:`timespan$();sym:`g#`symbol$();bid:`float$();ask:`float$();bsize:`long$();asize:`long$())
