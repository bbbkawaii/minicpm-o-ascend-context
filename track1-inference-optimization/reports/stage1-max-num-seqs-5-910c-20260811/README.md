# Rejected Stage 1 max_num_seqs=5 probe

On the promoted eight-step stack, increasing Talker Stage 1 `max_num_seqs`
from 4 to 5 did not improve the c8/128 result. Both sides completed 128/128
requests with no failures, but the candidate changed throughput by **-0.21%**,
E2E by **+0.21%**, audio TTFP by **+0.87%**, and audio RTF by **+0.08%**.
TTFT improved only **0.01%**, which is noise-sized. The candidate was rejected
and Stage 1 remains at 4. Raw JSON is in `raw/`.
