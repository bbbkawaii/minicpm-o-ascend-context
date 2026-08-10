# Hypothesis: admit five Stage 0 sequences, with a matching graph shape

The promoted one-card baseline already admits six Code2Wav requests in Stage 2,
but Stage 0 (Thinker) still admits only four.  At c8, the fifth request waits
for the first four-request wave even when the 910C has enough headroom for one
more Thinker sequence.  Raising Stage 0 only to five is the smallest admission
change that can release that queue without returning to the known unsafe large
single-card batches.

On Ascend, a five-sequence Stage 0 must also explicitly capture shape 5.  The
implicit PIECEWISE capture list otherwise stops at `[1, 2, 4]`, leaving the
new fifth sequence on a fallback path.  Therefore this experiment changes the
admission cap and its required graph-capture shape as one inseparable runtime
configuration.

Expected result:

- c4/c8 improve request throughput, E2E, audio TTFP and RTF;
- c1 remains effectively unchanged;
- every Seed-TTS request returns complete audio, with no OOM or service error.

The test does not establish task accuracy.  Video-MME, Daily-Omni and
TTS-Seed ASV/WER remain final submission gates.
