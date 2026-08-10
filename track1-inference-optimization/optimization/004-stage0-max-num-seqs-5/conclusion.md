# Conclusion

Promote Stage 0 `max_num_seqs=5` together with the explicit Ascend capture
shape `[1, 2, 4, 5]` as the next one-card performance candidate.

The candidate and controls completed the official Seed-TTS matrix with zero
failed requests.  It has a small c1 trade-off (core geometric score -0.61%),
but c4 improves +5.78% and c8 improves +2.15%.  Across c1/c4/c8, the neutral
equal-cell geometric aggregate for TTFT, audio TTFP and RTF is **+2.409%**.
Including throughput and E2E under the same neutral weighting gives **+2.856%**.

The strongest cell is c4: throughput +11.22%, E2E -10.42%, audio TTFP -10.84%
and RTF -9.66%; TTFT is +4.91% slower.  At c8 all five reported metrics improve
in the paired run.  This is a performance decision only: official Video-MME,
Daily-Omni and TTS-Seed ASV/WER gates remain required before a competition
submission.
