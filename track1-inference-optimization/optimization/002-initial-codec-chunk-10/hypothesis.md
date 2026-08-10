# Hypothesis: emit a smaller first codec chunk

The promoted Stage2=6 candidate still spends 1.062 s to the first audio packet
at concurrency 1. The existing bridge waits for 25 codec frames before every
Code2Wav call. Add an optional `initial_codec_chunk_frames` setting so only the
first call waits for 10 frames while later calls retain the 25-frame steady
chunk.

The generic implementation is recorded in
`../patches/minicpmo-initial-codec-chunk.patch`; `activation.patch` enables the
10/25 schedule. Defaults remain unchanged when the new setting is absent.

Success requires lower audio TTFP without materially reducing c8 throughput or
raising E2E/RTF. Streaming continuity must remain 100%.
