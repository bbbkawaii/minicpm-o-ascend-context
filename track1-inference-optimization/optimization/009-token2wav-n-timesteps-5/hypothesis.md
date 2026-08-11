# Hypothesis: reduce Code2Wav from six solver steps to five

Five steps remove another solver iteration without changing weights, prompts,
scheduling, or API behavior. Promote only if c1/c8 throughput, E2E, and RTF
improve, every request succeeds with matched token lengths, and the complete
Seed-TTS English WER gate remains at or below `0.05` with zero request, PCM,
and ASR failures. Record any latency or quality tradeoff explicitly.
