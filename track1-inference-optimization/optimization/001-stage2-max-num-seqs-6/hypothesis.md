# Hypothesis: raise only Stage 2 admission capacity to 6

The official one-card Seed-TTS baseline shows that Stage 2 (Code2Wav) owns
nearly all end-to-end latency at concurrency 8: 11.389 s of 11.411 s mean
E2E. The baseline deploy file limits every stage to `max_num_seqs: 4`, so half
of an eight-request wave waits outside Code2Wav even though the 910C still has
compute capacity.

Change only Stage 2 from 4 to 6. Keep Stage 0, Stage 1, memory utilization,
batch-token limits, sampling, codec chunking, model, data order and benchmark
runner unchanged.

Expected result:

- concurrency 8 gains throughput and lowers E2E, audio TTFP and RTF;
- concurrency 1 and 4 do not materially regress;
- all requests complete, streaming continuity remains 100%, and the service
  stays within one physical Ascend 910C card without OOM.

This experiment is a performance gate only. It does not replace the official
Video-MME, Daily-Omni or TTS-Seed ASV/WER accuracy gates.
