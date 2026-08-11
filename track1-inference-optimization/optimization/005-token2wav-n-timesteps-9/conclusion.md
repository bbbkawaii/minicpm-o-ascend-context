# Conclusion

Promote `token2wav_n_timesteps=9` on top of Stage 2 `max_num_seqs=6` and
Stage 0 `max_num_seqs=5`.

The fresh same-host c8/128 A/B run completed 128/128 requests on both sides.
Against ten solver steps, nine steps gives request throughput **+8.33%**, E2E
**-7.68%**, audio TTFP **-6.46%**, and audio RTF **-8.64%**.  Its only observed
trade-off is mean TTFT, **+0.92% slower**.  The candidate also completes the
full c1/c4/c8 official serving matrix with zero failures.

Because this configuration removes a quality iteration, it was gated with the
source Seed-TTS English WER evaluator rather than being accepted from timing
alone.  The full run completed **1,088/1,088** available English items with
mean WER **0.032571**, under the required **0.05**, and zero request, PCM or
ASR failures.

There is no published official weighted composite score to calculate here, so
this decision reports the paired raw metrics and the applicable quality gate
directly.  The candidate's source commit is `fa13e254`; its reproducibility
record and raw JSON are retained in this repository.  Full Daily-Omni and
Video-MME validation remain the final submission checks not rerun by this
TTS-only change.
