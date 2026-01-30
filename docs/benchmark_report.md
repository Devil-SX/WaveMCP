# Wave MCP Performance Benchmark Report

## Test Environment

- **Date**: 2026-01-30 21:03:43
- **Python**: 3.12.12
- **Platform**: Linux 6.6.87.2-microsoft-standard-WSL2
- **Test Scale**: small
- **Signal Counts**: [10, 50]
- **Time Steps**: [1000, 5000]
- **Repeat Count**: 3

## File Size Comparison

| Signals | Time Steps | VCD Size | FST Size | Compression Ratio |
|---------|------------|----------|----------|-------------------|
| 10 | 1000 | 27.29 KB | 2.38 KB | 11.45x |
| 10 | 5000 | 146.08 KB | 7.94 KB | 18.39x |
| 50 | 1000 | 43.77 KB | 5.46 KB | 8.02x |
| 50 | 5000 | 229.79 KB | 17.87 KB | 12.86x |

## Load Performance

| Signals | Time Steps | VCD Load | FST Load | FST Speedup |
|---------|------------|----------|----------|-------------|
| 10 | 1000 | 1.38 ms | 204.81 us | 6.72x |
| 10 | 5000 | 5.88 ms | 204.06 us | 28.81x |
| 50 | 1000 | 1.54 ms | 226.02 us | 6.80x |
| 50 | 5000 | 16.70 ms | 265.75 us | 62.85x |

## Signal List Retrieval Performance

| Signals | Time Steps | VCD get_signals | FST get_signals | FST Speedup |
|---------|------------|-----------------|-----------------|-------------|
| 10 | 1000 | 5.64 us | 4.45 us | 1.27x |
| 10 | 5000 | 5.17 us | 3.85 us | 1.34x |
| 50 | 1000 | 38.45 us | 30.92 us | 1.24x |
| 50 | 5000 | 16.82 us | 13.98 us | 1.20x |

## Time Range Query Performance

| Signals | Time Steps | VCD get_time_range | FST get_time_range | FST Speedup |
|---------|------------|--------------------|--------------------|-------------|
| 10 | 1000 | 1.60 us | 1.07 us | 1.50x |
| 10 | 5000 | 0.98 us | 0.62 us | 1.57x |
| 50 | 1000 | 0.73 us | 0.52 us | 1.41x |
| 50 | 5000 | 1.07 us | 0.69 us | 1.54x |

## Signal Value Query Performance

| Signals | Time Steps | Query Range | VCD get_values | FST get_values | FST Speedup |
|---------|------------|-------------|----------------|----------------|-------------|
| 10 | 1000 | 10% | 94.27 us | 430.16 us | 0.22x |
| 10 | 1000 | 50% | 225.33 us | 728.73 us | 0.31x |
| 10 | 1000 | 100% | 402.93 us | 1.08 ms | 0.37x |
| 10 | 5000 | 10% | 376.52 us | 2.08 ms | 0.18x |
| 10 | 5000 | 50% | 1.52 ms | 3.96 ms | 0.38x |
| 10 | 5000 | 100% | 3.70 ms | 5.81 ms | 0.64x |
| 50 | 1000 | 10% | 89.49 us | 449.79 us | 0.20x |
| 50 | 1000 | 50% | 224.19 us | 675.60 us | 0.33x |
| 50 | 1000 | 100% | 420.32 us | 1.03 ms | 0.41x |
| 50 | 5000 | 10% | 557.41 us | 2.15 ms | 0.26x |
| 50 | 5000 | 50% | 1.44 ms | 3.61 ms | 0.40x |
| 50 | 5000 | 100% | 2.69 ms | 5.08 ms | 0.53x |

## VCD <-> FST Conversion Performance

| Signals | Time Steps | VCD -> FST | FST -> VCD |
|---------|------------|------------|------------|
| 10 | 1000 | 2.15 ms | 3.06 ms |
| 10 | 5000 | 9.98 ms | 21.71 ms |
| 50 | 1000 | 3.66 ms | 5.52 ms |
| 50 | 5000 | 14.69 ms | 43.11 ms |

## Summary

- **Average FST compression ratio**: 12.68x smaller than VCD
- **Average FST load speedup**: 26.29x faster than VCD
- **Average FST value query speedup**: 0.35x faster than VCD

## Recommendations

- Use **FST format** for large waveforms to save disk space and improve load times
- Use **VCD format** for maximum compatibility and text-based debugging
- For interactive waveform viewing, FST provides better random access performance
