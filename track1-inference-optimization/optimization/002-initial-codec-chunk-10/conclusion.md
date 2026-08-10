# Conclusion

Reject the 10-frame initial / 25-frame steady activation.

At concurrency 1 it works as intended: audio TTFP improves 17.1%, throughput
improves 4.7%, E2E improves 4.5%, and continuity remains 100%. At concurrency
8 the extra short Code2Wav scheduling event dominates: throughput regresses
19.7%, E2E regresses 24.6%, audio TTFP regresses 10.4%, and RTF regresses
25.4% relative to the promoted Stage2=6 candidate.

Keep the generic, default-off implementation for further experiments, but do
not ship this activation. The next candidate pairs the 10-frame first chunk
with a larger 32-frame steady chunk to offset the additional scheduling event.
