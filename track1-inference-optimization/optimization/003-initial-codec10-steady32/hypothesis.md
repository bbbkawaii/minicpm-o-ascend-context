# Hypothesis: offset the short first chunk with a larger steady chunk

Experiment 002 showed that a 10-frame first chunk improves c1 TTFP but an
unchanged 25-frame steady chunk creates severe c8 scheduling overhead. Keep the
10-frame first chunk and increase subsequent chunks to 32 frames so a typical
utterance uses no more Code2Wav calls than the original 25/25 schedule.

Use the promoted Stage2=6 candidate as the comparison baseline. Run c8 first;
reject immediately if audio TTFP, E2E or RTF regresses materially.
