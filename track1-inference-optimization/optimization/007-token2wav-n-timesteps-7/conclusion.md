# Conclusion

Promote `token2wav_n_timesteps=7` on top of Stage 2 `max_num_seqs=6` and
Stage 0 `max_num_seqs=5`.

Against eight solver steps, the matched c8/128 result improves request
throughput **11.31%**, TTFT **2.26%**, E2E **10.50%**, audio TTFP **5.71%**,
and audio RTF **10.46%**. Both runs completed 128/128 requests with no failures
and identical input/output token-length arrays.

At c1/32, seven steps improves throughput **6.07%**, E2E **5.72%**, audio TTFP
**2.57%**, and audio RTF **5.65%**, with mean TTFT **0.83% slower**. Both c1
runs completed 32/32 requests with no failures and identical input/output
lengths and total audio duration. The supplemental c4/64 candidate completed
64/64 requests without failures.

The full source Seed-TTS English evaluator completed **1,088/1,088** items with
mean WER **0.033366**, below the required **0.05**, and zero request, PCM, or
ASR failures. The candidate source commit is `e3266c5a`; raw JSON is retained
in `reports/token2wav-steps7-910c-20260811/`.
