# Wave MCP Performance Benchmark Report

## Test Environment

- **Date**: 2026-01-27 19:52:57
- **Python**: 3.12.12
- **Platform**: Linux 6.6.87.2-microsoft-standard-WSL2
- **Test Scale**: medium
- **Signal Counts**: [10, 100, 500]
- **Time Steps**: [1000, 10000, 50000]
- **Repeat Count**: 3

## File Size Comparison

| Signals | Time Steps | VCD Size | FST Size | Compression Ratio |
|---------|------------|----------|----------|-------------------|
| 10 | 1000 | 27.29 KB | 2.38 KB | 11.45x |
| 10 | 10000 | 298.82 KB | 15.28 KB | 19.55x |
| 10 | 50000 | 1.57 MB | 73.22 KB | 21.93x |
| 100 | 1000 | 52.14 KB | 7.64 KB | 6.83x |
| 100 | 10000 | 549.03 KB | 43.12 KB | 12.73x |
| 100 | 50000 | 2.86 MB | 189.11 KB | 15.50x |
| 500 | 1000 | 82.14 KB | 15.27 KB | 5.38x |
| 500 | 10000 | 761.29 KB | 81.29 KB | 9.37x |
| 500 | 50000 | 3.91 MB | 318.64 KB | 12.58x |

## Load Performance

| Signals | Time Steps | VCD Load | FST Load | FST Speedup |
|---------|------------|----------|----------|-------------|
| 10 | 1000 | 1.31 ms | 165.46 us | 7.91x |
| 10 | 10000 | 20.88 ms | 258.40 us | 80.82x |
| 10 | 50000 | 69.85 ms | 183.32 us | 381.04x |
| 100 | 1000 | 4.16 ms | 275.18 us | 15.12x |
| 100 | 10000 | 19.27 ms | 519.34 us | 37.10x |
| 100 | 50000 | 138.42 ms | 419.17 us | 330.22x |
| 500 | 1000 | 10.21 ms | 1.19 ms | 8.58x |
| 500 | 10000 | 30.98 ms | 881.72 us | 35.13x |
| 500 | 50000 | 124.85 ms | 834.67 us | 149.57x |

## Signal List Retrieval Performance

| Signals | Time Steps | VCD get_signals | FST get_signals | FST Speedup |
|---------|------------|-----------------|-----------------|-------------|
| 10 | 1000 | 7.18 us | 5.36 us | 1.34x |
| 10 | 10000 | 6.49 us | 4.44 us | 1.46x |
| 10 | 50000 | 8.05 us | 6.13 us | 1.31x |
| 100 | 1000 | 50.45 us | 42.79 us | 1.18x |
| 100 | 10000 | 48.51 us | 42.86 us | 1.13x |
| 100 | 50000 | 66.68 us | 57.79 us | 1.15x |
| 500 | 1000 | 436.06 us | 437.65 us | 1.00x |
| 500 | 10000 | 260.40 us | 215.35 us | 1.21x |
| 500 | 50000 | 233.35 us | 197.11 us | 1.18x |

## Time Range Query Performance

| Signals | Time Steps | VCD get_time_range | FST get_time_range | FST Speedup |
|---------|------------|--------------------|--------------------|-------------|
| 10 | 1000 | 2.29 us | 1.50 us | 1.53x |
| 10 | 10000 | 1.19 us | 0.67 us | 1.78x |
| 10 | 50000 | 1.54 us | 1.14 us | 1.36x |
| 100 | 1000 | 1.25 us | 0.85 us | 1.46x |
| 100 | 10000 | 1.68 us | 0.95 us | 1.77x |
| 100 | 50000 | 1.65 us | 1.02 us | 1.62x |
| 500 | 1000 | 1.66 us | 1.06 us | 1.56x |
| 500 | 10000 | 1.79 us | 1.13 us | 1.59x |
| 500 | 50000 | 1.46 us | 1.33 us | 1.09x |

## Signal Value Query Performance

| Signals | Time Steps | Query Range | VCD get_values | FST get_values | FST Speedup |
|---------|------------|-------------|----------------|----------------|-------------|
| 10 | 1000 | 10% | 119.25 us | 911.31 us | 0.13x |
| 10 | 1000 | 50% | 320.36 us | 1.16 ms | 0.28x |
| 10 | 1000 | 100% | 517.53 us | 1.80 ms | 0.29x |
| 10 | 10000 | 10% | 1.36 ms | 8.13 ms | 0.17x |
| 10 | 10000 | 50% | 4.19 ms | 10.61 ms | 0.39x |
| 10 | 10000 | 100% | 5.60 ms | 11.27 ms | 0.50x |
| 10 | 50000 | 10% | 4.50 ms | 19.92 ms | 0.23x |
| 10 | 50000 | 50% | 14.13 ms | 46.11 ms | 0.31x |
| 10 | 50000 | 100% | 35.49 ms | 70.27 ms | 0.51x |
| 100 | 1000 | 10% | 146.98 us | 604.96 us | 0.24x |
| 100 | 1000 | 50% | 242.09 us | 872.11 us | 0.28x |
| 100 | 1000 | 100% | 408.26 us | 1.16 ms | 0.35x |
| 100 | 10000 | 10% | 1.16 ms | 5.51 ms | 0.21x |
| 100 | 10000 | 50% | 2.70 ms | 10.00 ms | 0.27x |
| 100 | 10000 | 100% | 5.93 ms | 13.85 ms | 0.43x |
| 100 | 50000 | 10% | 12.66 ms | 33.08 ms | 0.38x |
| 100 | 50000 | 50% | 21.94 ms | 56.56 ms | 0.39x |
| 100 | 50000 | 100% | 45.73 ms | 89.22 ms | 0.51x |
| 500 | 1000 | 10% | 488.36 us | 1.17 ms | 0.42x |
| 500 | 1000 | 50% | 525.91 us | 1.33 ms | 0.39x |
| 500 | 1000 | 100% | 724.52 us | 2.25 ms | 0.32x |
| 500 | 10000 | 10% | 1.76 ms | 7.08 ms | 0.25x |
| 500 | 10000 | 50% | 4.23 ms | 10.33 ms | 0.41x |
| 500 | 10000 | 100% | 6.85 ms | 15.34 ms | 0.45x |
| 500 | 50000 | 10% | 9.81 ms | 35.12 ms | 0.28x |
| 500 | 50000 | 50% | 28.72 ms | 58.60 ms | 0.49x |
| 500 | 50000 | 100% | 48.70 ms | 91.32 ms | 0.53x |

## VCD <-> FST Conversion Performance

| Signals | Time Steps | VCD -> FST | FST -> VCD |
|---------|------------|------------|------------|
| 10 | 1000 | 3.77 ms | 4.62 ms |
| 10 | 10000 | 30.11 ms | 54.58 ms |
| 10 | 50000 | 195.77 ms | 312.89 ms |
| 100 | 1000 | 5.34 ms | 5.63 ms |
| 100 | 10000 | 33.93 ms | 81.28 ms |
| 100 | 50000 | 215.26 ms | 594.07 ms |
| 500 | 1000 | 12.66 ms | 28.88 ms |
| 500 | 10000 | 92.55 ms | 152.53 ms |
| 500 | 50000 | 396.44 ms | 797.81 ms |

## Summary

- **Average FST compression ratio**: 12.81x smaller than VCD
- **Average FST load speedup**: 116.17x faster than VCD
- **Average FST value query speedup**: 0.35x faster than VCD

## Recommendations

- Use **FST format** for large waveforms to save disk space and improve load times
- Use **VCD format** for maximum compatibility and text-based debugging
- For interactive waveform viewing, FST provides better random access performance
