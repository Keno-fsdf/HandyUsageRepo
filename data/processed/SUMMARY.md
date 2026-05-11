# Data preparation summary

Source: `data\raw\combined.csv`
Sequence length: 10
Total discharge segments: 553

## Split (segment-level, no leakage)

| Split | Sequences | mean target_extrap (h) | mean target_real (h) |
|-------|-----------|------------------------|----------------------|
| train | 13901 | 11.18 | 1.09 |
| val | 3056 | 13.76 | 0.95 |
| test | 3885 | 7.68 | 1.11 |

## Per-device sequence counts

| Split | pixel_7_pro | pixel_8_pro | pixel_9_pro_xl | xiaomi_2107113sg |
|---|---|---|---|---|
| train | 4320 | 1276 | 2201 | 6104 |
| val | 489 | 581 | 414 | 1572 |
| test | 1825 | 98 | 614 | 1348 |
