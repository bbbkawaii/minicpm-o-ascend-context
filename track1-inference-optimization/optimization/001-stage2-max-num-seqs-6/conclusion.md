# Conclusion

Promote Stage 2 `max_num_seqs=6` as the first official one-card performance
candidate.

The complete official Seed-TTS performance matrix finished with 224/224
successful measured requests, zero failed requests and 100% streaming
continuity. Relative to the preserved baseline, throughput improved by 4.1%,
6.4% and 14.3% at concurrency 1, 4 and 8. Mean E2E improved by 4.0%, 6.0% and
12.6%; mean audio RTF improved by 3.2%, 6.0% and 13.3%.

At concurrency 8, mean TTFT regressed 5.8% from 494.6 ms to 523.2 ms, but it
remains better than the official 547.3 ms reference. The larger gains in
throughput, E2E, audio TTFP and RTF make the change a clear performance win.

The change is not yet submission-ready: run the official Video-MME,
Daily-Omni and TTS-Seed ASV/WER accuracy gates after the final optimization
stack is chosen. Raw runner output and JSON are archived in
`reports/stage2-maxseq6-910c-20260811/`.
