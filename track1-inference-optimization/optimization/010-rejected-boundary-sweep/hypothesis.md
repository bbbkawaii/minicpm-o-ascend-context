# Hypothesis: search the boundaries around the five-step candidate

The promoted five-step stack may still leave performance at three boundaries:
stage admission limits, Token2Wav precision/solver count, and codec window
geometry. Test one variable at a time against `0dced5d4`.

Promote only a repeatable candidate with a clear c1/c8 net gain, zero request
failures, and no unexplained token-length change. Candidates that change audio
generation must subsequently pass the full Seed-TTS WER gate and the applicable
ASV gate; performance failure stops the experiment before those expensive
checks.
