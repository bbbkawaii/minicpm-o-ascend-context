# Conclusion

Promote `token2wav_n_timesteps=6` on Stage 2 `max_num_seqs=6` and Stage 0
`max_num_seqs=5`.

Relative to seven steps, c8/128 throughput improves **14.17%**, E2E **12.22%**,
audio TTFP **8.09%**, and audio RTF **11.70%**, while TTFT is **3.02% slower**.
At c1/32, throughput improves **7.50%**, E2E **6.99%**, TTFP **5.38%**, and
RTF **7.09%**, while TTFT is **2.29% slower**. Both matched comparisons have
zero failures and identical input/output token lengths; c4/64 is also 64/64.

The complete 1,088-item Seed-TTS English gate reports mean WER **0.034221 <=
0.05**, with zero request, PCM, and ASR failures. Source commit: `7a5a95a8`.
