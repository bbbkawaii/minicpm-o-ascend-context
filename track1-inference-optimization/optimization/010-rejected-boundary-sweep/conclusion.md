# Conclusion

Reject every candidate in this boundary sweep and keep source commit
`0dced5d4` as the current best one-card stack.

Stage2 7/8 and Stage0 6 regress every c8 metric. Four Token2Wav solver steps
are highly unstable across clean repeated c1/c8 runs, including one strong c8
run surrounded by major regressions. FP16 exchanges throughput/E2E/RTF for
TTFT/TTFP at c8, is worse at c1, and has a neutral ten-cell geometric aggregate
of only `+0.008%`. Codec left context 2 and chunk size 32 both regress c1.

No candidate qualifies for WER or ASV evaluation. All experimental source and
configuration changes were reverted; raw JSON is retained in
`reports/rejected-sweep-910c-20260811/`.
