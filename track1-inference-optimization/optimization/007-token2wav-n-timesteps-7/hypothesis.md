# Hypothesis: reduce the Code2Wav solver from eight steps to seven

The current one-card stack uses Stage 2 `max_num_seqs=6`, Stage 0
`max_num_seqs=5`, and `token2wav_n_timesteps=8`. Reducing the Code2Wav
conditional-flow solver to seven steps removes another 12.5% of its iterations
without changing model weights, prompts, scheduling, or the serving API.

Acceptance requires matched one-card c1/32 and c8/128 performance evidence,
zero request failures, identical paired input/output token-length arrays, and a
full source Seed-TTS English WER result at or below `0.05` with no request, PCM,
or ASR failures.
