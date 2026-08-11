# Hypothesis: reduce the Code2Wav solver from nine steps to eight

The promoted one-card stack already uses Stage 2 `max_num_seqs=6`, Stage 0
`max_num_seqs=5`, and `token2wav_n_timesteps=9`. Code2Wav still performs nine
conditional-flow solver iterations for every generated audio segment.

Setting `connector_of_shared_memory.extra.token2wav_n_timesteps` to eight
removes one more solver iteration without changing model weights, prompt
formatting, scheduling, the serving API, or the benchmark workload.

Acceptance requires all of the following:

- a fresh-service c1/32 comparison that improves rather than sacrifices the
  single-request path;
- a same-host paired c8/128 comparison with no failures;
- identical input/output token-length arrays within each paired comparison;
- source Seed-TTS English mean WER at or below `0.05`, with no request, PCM, or
  ASR failures.
