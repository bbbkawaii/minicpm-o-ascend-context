# Hypothesis: reduce the Code2Wav solver from ten steps to nine

The promoted one-card stack already uses Stage 2 `max_num_seqs=6` and Stage 0
`max_num_seqs=5`.  Its remaining audio tail is dominated by Code2Wav's
conditional-flow solver.  The deployment YAML leaves that solver at its
default of ten integration steps.

`MiniCPMO45Code2Wav` reads
`connector_of_shared_memory.extra.token2wav_n_timesteps` and passes it to the
actual solver.  Setting the value to nine removes exactly one of ten solver
iterations without changing prompt formatting, model weights, scheduling or
the public serving API.

Expected outcome:

- improve high-concurrency Seed-TTS throughput, E2E latency, audio TTFP and
  audio RTF;
- keep all responses successful;
- remain below the source Seed-TTS English WER gate of `0.05`.

This is deliberately a TTS-path optimization.  Performance alone is not an
accuracy result, so the candidate is promoted only after the WER gate passes.
