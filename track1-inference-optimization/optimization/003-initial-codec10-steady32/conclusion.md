# Conclusion

Reject the 10-frame initial / 32-frame steady schedule.

The larger steady chunk successfully removes almost all throughput and E2E
damage seen in experiment 002: relative to Stage2=6, c8 throughput changes
-0.8% and E2E +0.8%. However, the target metric moves the wrong way: audio TTFP
regresses 8.4% from 3399.0 ms to 3683.6 ms, and RTF regresses 3.4%.

This confirms that an additional early Code2Wav scheduling event harms
high-concurrency first-packet latency on this runtime even when the total call
count is offset later. Stop exploring smaller initial chunks and retain the
original 25-frame schedule with Stage2 `max_num_seqs=6`.
