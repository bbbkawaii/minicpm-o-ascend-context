# Hypothesis: reduce Code2Wav from seven solver steps to six

Six steps remove another solver iteration without changing weights, prompts,
scheduling, or API behavior. Promote only if c1/c8 performance improves, all
requests succeed with matched token lengths, and the complete Seed-TTS English
WER gate remains at or below `0.05` with zero request, PCM, and ASR failures.
