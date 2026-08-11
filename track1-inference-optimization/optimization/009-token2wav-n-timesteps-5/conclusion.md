# Conclusion

Promote `token2wav_n_timesteps=5` on Stage 2 `max_num_seqs=6` and Stage 0
`max_num_seqs=5`.

Relative to six steps, c1/32 improves every measured metric: throughput
**1.22%**, TTFT **1.94%**, E2E **1.19%**, audio TTFP **3.83%**, and RTF
**1.29%**. At c8/128, throughput improves **8.99%**, TTFT **0.52%**, E2E
**8.16%**, and RTF **8.13%**, while audio TTFP is **2.55% slower**. Both
matched comparisons have zero failures and identical input/output token
lengths; c4/64 is also 64/64.

The complete 1,088-item Seed-TTS English gate reports mean WER **0.035373 <=
0.05**, with zero request, PCM, and ASR failures. The WER is higher than the
six-step run (`0.034221`) but remains inside the source gate. Source commit:
`0dced5d4`.
