# Conclusion

Promote `token2wav_n_timesteps=8` on top of Stage 2 `max_num_seqs=6` and
Stage 0 `max_num_seqs=5`.

The clean-restart c1/32 comparison completed 32/32 requests with zero failures
on both sides. Against nine solver steps, eight steps improves request
throughput **6.65%**, TTFT **2.39%**, E2E **6.23%**, audio TTFP **5.44%**, and
audio RTF **6.18%**. Input/output length arrays and total audio duration are
identical between the two c1 runs.

The same-host paired c8/128 comparison also completed 128/128 requests on both
sides and improves all five metrics: throughput **11.75%**, TTFT **9.65%**,
E2E **10.62%**, audio TTFP **12.41%**, and audio RTF **10.79%**. A supplemental
c4/64 candidate run completed 64/64 requests with no failures.

The source Seed-TTS English WER run completed **1,088/1,088** available items
with mean WER **0.033804**, below the required **0.05**, and zero request, PCM,
or ASR failures. The candidate source commit is `1c4e4c58`; raw benchmark JSON
is retained in `reports/token2wav-steps8-910c-20260811/`.
