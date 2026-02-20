"""Performance benchmark tests for VCD and FST waveform parsing.

This module provides comprehensive performance benchmarking for:
- File loading (Old VCD / Old FST / pywellen VCD / pywellen FST)
- Signal list retrieval
- Time range queries
- Signal value extraction
- Format conversion (VCD <-> FST)

Usage:
    # Default medium scale
    uv run pytest tests/test_benchmark.py -v -s

    # Small scale (quick)
    BENCHMARK_SCALE=small uv run pytest tests/test_benchmark.py -v -s

    # Large scale (comprehensive)
    BENCHMARK_SCALE=large uv run pytest tests/test_benchmark.py -v -s

    # Full scale (small + 100MB+, old vcdvcd skipped for large files)
    BENCHMARK_SCALE=full uv run pytest tests/test_benchmark.py -v -s
"""

import os
import sys
import time
import statistics
import platform
from datetime import datetime
from pathlib import Path

import pytest

# Import the functions and classes to test from the new module structure
from src.parsers import (
    FstParser, WaveformParser, WellenParser,
    set_vcd_parser, set_fst_parser, set_wellen_parser,
    get_vcd_parser, get_fst_parser, get_wellen_parser,
)


# Wrapper functions for MCP tools (to maintain compatibility with benchmark tests)
async def load_vcd_file(vcd_path: str) -> str:
    """Load a VCD file with old vcdvcd parser."""
    path = Path(vcd_path)
    if not path.exists():
        return f"Error: File not found: {vcd_path}"
    try:
        parser = WaveformParser(str(path))
        set_vcd_parser(parser)
        _, signal_count = parser.get_signal_list(limit=0)
        return f"Successfully loaded VCD file: {vcd_path}\nFound {signal_count} signals."
    except Exception as e:
        return f"Error loading VCD file: {e}"


async def load_fst_file(fst_path: str) -> str:
    """Load an FST file with old pylibfst parser."""
    path = Path(fst_path)
    if not path.exists():
        return f"Error: File not found: {fst_path}"
    try:
        parser = FstParser(str(path))
        set_fst_parser(parser)
        _, signal_count = parser.get_signal_list(limit=0)
        return f"Successfully loaded FST file: {fst_path}\nFound {signal_count} signals."
    except Exception as e:
        return f"Error loading FST file: {e}"


async def load_wellen(path: str) -> str:
    """Load a file with pywellen parser."""
    filepath = Path(path)
    if not filepath.exists():
        return f"Error: File not found: {path}"
    try:
        parser = WellenParser(str(filepath))
        set_wellen_parser(parser)
        _, signal_count = parser.get_signal_list(limit=0)
        return f"Successfully loaded: {path}\nFound {signal_count} signals."
    except Exception as e:
        return f"Error loading file: {e}"


async def get_vcd_signals() -> str:
    """Get VCD signal list."""
    parser = get_vcd_parser()
    signals, total_count = parser.get_signal_list(limit=0)
    lines = [f"Signals ({total_count}):"]
    for sig in signals:
        lines.append(f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}")
    return "\n".join(lines)


async def get_fst_signals() -> str:
    """Get FST signal list."""
    parser = get_fst_parser()
    signals, total_count = parser.get_signal_list(limit=0)
    lines = [f"Signals ({total_count}):"]
    for sig in signals:
        lines.append(f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}")
    return "\n".join(lines)


async def get_wellen_signals() -> str:
    """Get wellen signal list."""
    parser = get_wellen_parser()
    signals, total_count = parser.get_signal_list(limit=0)
    lines = [f"Signals ({total_count}):"]
    for sig in signals:
        lines.append(f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}")
    return "\n".join(lines)


async def get_vcd_time_range() -> str:
    """Get VCD time range."""
    parser = get_vcd_parser()
    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


async def get_fst_time_range() -> str:
    """Get FST time range."""
    parser = get_fst_parser()
    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


async def get_wellen_time_range() -> str:
    """Get wellen time range."""
    parser = get_wellen_parser()
    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


async def get_vcd_signal_values(
    signal_names: list[str], start_time: int, end_time: int
) -> str:
    """Get VCD signal values."""
    parser = get_vcd_parser()
    values, _ = parser.get_signal_values(signal_names, start_time, end_time)
    if not values:
        return f"No matching signals"
    lines = [f"Signal values [{start_time}, {end_time}]:"]
    for signal, changes in values.items():
        lines.append(f"\n{signal}:")
        for t, v in changes:
            lines.append(f"  {t:>10}: {v}")
    return "\n".join(lines)


async def get_fst_signal_values(
    signal_names: list[str], start_time: int, end_time: int
) -> str:
    """Get FST signal values."""
    parser = get_fst_parser()
    values, _ = parser.get_signal_values(signal_names, start_time, end_time)
    if not values:
        return f"No matching signals"
    lines = [f"Signal values [{start_time}, {end_time}]:"]
    for signal, changes in values.items():
        lines.append(f"\n{signal}:")
        for t, v in changes:
            lines.append(f"  {t:>10}: {v}")
    return "\n".join(lines)


async def get_wellen_signal_values(
    signal_names: list[str], start_time: int, end_time: int
) -> str:
    """Get wellen signal values."""
    parser = get_wellen_parser()
    values, _ = parser.get_signal_values(signal_names, start_time, end_time)
    if not values:
        return f"No matching signals"
    lines = [f"Signal values [{start_time}, {end_time}]:"]
    for signal, changes in values.items():
        lines.append(f"\n{signal}:")
        for t, v in changes:
            lines.append(f"  {t:>10}: {v}")
    return "\n".join(lines)


# Configurable test scale via environment variable
SCALE = os.environ.get("BENCHMARK_SCALE", "medium")

SCALE_CONFIG = {
    "small": {
        "signal_counts": [10, 50],
        "time_steps": [1000, 5000],
        "repeat": 3,
    },
    "medium": {
        "signal_counts": [10, 100, 500],
        "time_steps": [1000, 10000, 50000],
        "repeat": 3,
    },
    "large": {
        "signal_counts": [10, 100, 500, 1000],
        "time_steps": [1000, 10000, 50000, 100000],
        "repeat": 5,
    },
    "xlarge": {
        "signal_counts": [100, 500],
        "time_steps": [500000, 2000000],
        "repeat": 3,
        "skip_old_vcd": True,
    },
    "full": {
        "signal_counts": [10, 50, 100, 500],
        "time_steps": [1000, 5000, 500000, 2000000],
        "repeat": 3,
        # VCD files > OLD_VCD_SIZE_LIMIT will skip old vcdvcd parser (too slow)
        "old_vcd_size_limit": 10 * 1024 * 1024,  # 10 MB
    },
}

CONFIG = SCALE_CONFIG.get(SCALE, SCALE_CONFIG["medium"])
SKIP_OLD_VCD = CONFIG.get("skip_old_vcd", False)
SKIP_OLD_FST = CONFIG.get("skip_old_fst", False)
OLD_VCD_SIZE_LIMIT = CONFIG.get("old_vcd_size_limit", 0)  # 0 = no limit


def should_skip_old_vcd(vcd_size: int) -> bool:
    """Check whether to skip old vcdvcd parser for this test point."""
    if SKIP_OLD_VCD:
        return True
    if OLD_VCD_SIZE_LIMIT > 0 and vcd_size > OLD_VCD_SIZE_LIMIT:
        return True
    return False


def generate_large_vcd(path: str, num_signals: int, num_timesteps: int) -> int:
    """Generate a VCD file with specified number of signals and timesteps.

    Returns:
        File size in bytes
    """
    from vcd.writer import VCDWriter

    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        with VCDWriter(f, timescale="1ns", date="benchmark") as writer:
            signals = []
            for i in range(num_signals):
                if i % 3 == 0:
                    size = 1
                elif i % 3 == 1:
                    size = 8
                else:
                    size = 32

                sig = writer.register_var(
                    "bench", f"sig_{i:04d}", "wire", size=size, init=0
                )
                signals.append((sig, size))

            for t in range(num_timesteps):
                timestamp = t * 10
                for i, (sig, size) in enumerate(signals):
                    if t % (i + 1) == 0:
                        if size == 1:
                            value = t % 2
                        else:
                            value = (t * (i + 1)) % (2**size)
                        writer.change(sig, timestamp, value)

    return Path(path).stat().st_size


def generate_large_fst(path: str, num_signals: int, num_timesteps: int) -> int:
    """Generate an FST file with specified number of signals and timesteps.

    Returns:
        File size in bytes
    """
    import pylibfst
    from pylibfst import lib, ffi

    Path(path).parent.mkdir(parents=True, exist_ok=True)

    ctx = lib.fstWriterCreate(path.encode("utf-8"), 1)
    if ctx == ffi.NULL:
        raise RuntimeError("Failed to create FST writer")

    try:
        lib.fstWriterSetTimescale(ctx, -9)
        lib.fstWriterSetScope(ctx, lib.FST_ST_VCD_MODULE, b"bench", ffi.NULL)

        handles = []
        for i in range(num_signals):
            if i % 3 == 0:
                size = 1
            elif i % 3 == 1:
                size = 8
            else:
                size = 32

            name = f"sig_{i:04d}".encode("utf-8")
            handle = lib.fstWriterCreateVar(
                ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, size, name, 0
            )
            handles.append((handle, size))

        lib.fstWriterSetUpscope(ctx)

        lib.fstWriterEmitTimeChange(ctx, 0)
        for handle, size in handles:
            init_val = "0" * size
            lib.fstWriterEmitValueChange(ctx, handle, init_val.encode("utf-8"))

        for t in range(1, num_timesteps):
            timestamp = t * 10
            lib.fstWriterEmitTimeChange(ctx, timestamp)

            for i, (handle, size) in enumerate(handles):
                if t % (i + 1) == 0:
                    if size == 1:
                        value = str(t % 2)
                    else:
                        int_val = (t * (i + 1)) % (2**size)
                        value = format(int_val, f"0{size}b")
                    lib.fstWriterEmitValueChange(ctx, handle, value.encode("utf-8"))

    finally:
        lib.fstWriterClose(ctx)

    return Path(path).stat().st_size


def benchmark_function(func, *args, repeat: int = 3) -> dict:
    """Run a function multiple times and return timing statistics."""
    times = []
    result = None
    for _ in range(repeat):
        start = time.perf_counter()
        result = func(*args)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "result": result,
    }


async def benchmark_async_function(func, *args, repeat: int = 3) -> dict:
    """Run an async function multiple times and return timing statistics."""
    times = []
    result = None
    for _ in range(repeat):
        start = time.perf_counter()
        result = await func(*args)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "result": result,
    }


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def format_time(seconds: float) -> str:
    """Format time in seconds to appropriate unit."""
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f} us"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.3f} s"


class BenchmarkResults:
    """Class to collect and store benchmark results."""

    def __init__(self):
        self.file_sizes = []  # (signals, timesteps, vcd_size, fst_size)
        # 4-way: (signals, timesteps, old_vcd, old_fst, wellen_vcd, wellen_fst)
        self.load_times = []
        self.get_signals_times = []
        self.get_time_range_times = []
        # 4-way + query range: (signals, timesteps, range, old_vcd, old_fst, wellen_vcd, wellen_fst)
        self.get_values_times = []
        self.conversion_times = []  # (signals, timesteps, vcd_to_fst, fst_to_vcd)

    def generate_report(self, output_path: str):
        """Generate a Markdown report of the benchmark results."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Build file size lookup: (signals, timesteps) -> (vcd_size, fst_size)
        size_lookup = {}
        for signals, timesteps, vcd_size, fst_size in self.file_sizes:
            size_lookup[(signals, timesteps)] = (vcd_size, fst_size)

        lines = []
        lines.append("# Wave MCP Performance Benchmark Report\n")

        # Test environment
        lines.append("## Test Environment\n")
        lines.append(f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **Python**: {sys.version.split()[0]}")
        lines.append(f"- **Platform**: {platform.system()} {platform.release()}")
        lines.append(f"- **Test Scale**: {SCALE}")
        lines.append(f"- **Signal Counts**: {CONFIG['signal_counts']}")
        lines.append(f"- **Time Steps**: {CONFIG['time_steps']}")
        lines.append(f"- **Repeat Count**: {CONFIG['repeat']}")
        lines.append("")

        # File size comparison
        lines.append("## File Size Comparison\n")
        lines.append("| Signals | Time Steps | VCD Size | FST Size | Compression Ratio |")
        lines.append("|---------|------------|----------|----------|-------------------|")
        for signals, timesteps, vcd_size, fst_size in self.file_sizes:
            ratio = vcd_size / fst_size if fst_size > 0 else 0
            lines.append(
                f"| {signals} | {timesteps} | {format_size(vcd_size)} | {format_size(fst_size)} | {ratio:.2f}x |"
            )
        lines.append("")

        # Load performance (4-way)
        lines.append("## Load Performance\n")
        lines.append("| Signals | Time Steps | VCD Size | FST Size | Old VCD (vcdvcd) | Old FST (pylibfst) | pywellen VCD | pywellen FST | pywellen VCD Speedup | pywellen FST Speedup |")
        lines.append("|---------|------------|----------|----------|------------------|--------------------|--------------|--------------|----------------------|----------------------|")
        for signals, timesteps, old_vcd, old_fst, w_vcd, w_fst in self.load_times:
            vcd_s, fst_s = size_lookup.get((signals, timesteps), (0, 0))
            vcd_speedup = old_vcd / w_vcd if w_vcd > 0 and old_vcd > 0 else 0
            fst_speedup = old_fst / w_fst if w_fst > 0 and old_fst > 0 else 0
            old_vcd_str = format_time(old_vcd) if old_vcd > 0 else "N/A"
            vcd_speedup_str = f"{vcd_speedup:.2f}x" if vcd_speedup > 0 else "N/A"
            lines.append(
                f"| {signals} | {timesteps} | {format_size(vcd_s)} | {format_size(fst_s)} | {old_vcd_str} | {format_time(old_fst)} | {format_time(w_vcd)} | {format_time(w_fst)} | {vcd_speedup_str} | {fst_speedup:.2f}x |"
            )
        lines.append("")

        # Get signals performance (4-way)
        lines.append("## Signal List Retrieval Performance\n")
        lines.append("| Signals | Time Steps | VCD Size | FST Size | Old VCD | Old FST | pywellen VCD | pywellen FST | pywellen VCD Speedup | pywellen FST Speedup |")
        lines.append("|---------|------------|----------|----------|---------|---------|--------------|--------------|----------------------|----------------------|")
        for signals, timesteps, old_vcd, old_fst, w_vcd, w_fst in self.get_signals_times:
            vcd_s, fst_s = size_lookup.get((signals, timesteps), (0, 0))
            vcd_speedup = old_vcd / w_vcd if w_vcd > 0 and old_vcd > 0 else 0
            fst_speedup = old_fst / w_fst if w_fst > 0 and old_fst > 0 else 0
            old_vcd_str = format_time(old_vcd) if old_vcd > 0 else "N/A"
            old_fst_str = format_time(old_fst) if old_fst > 0 else "N/A"
            vcd_speedup_str = f"{vcd_speedup:.2f}x" if vcd_speedup > 0 else "N/A"
            fst_speedup_str = f"{fst_speedup:.2f}x" if fst_speedup > 0 else "N/A"
            lines.append(
                f"| {signals} | {timesteps} | {format_size(vcd_s)} | {format_size(fst_s)} | {old_vcd_str} | {old_fst_str} | {format_time(w_vcd)} | {format_time(w_fst)} | {vcd_speedup_str} | {fst_speedup_str} |"
            )
        lines.append("")

        # Get time range performance (4-way)
        lines.append("## Time Range Query Performance\n")
        lines.append("| Signals | Time Steps | VCD Size | FST Size | Old VCD | Old FST | pywellen VCD | pywellen FST | pywellen VCD Speedup | pywellen FST Speedup |")
        lines.append("|---------|------------|----------|----------|---------|---------|--------------|--------------|----------------------|----------------------|")
        for signals, timesteps, old_vcd, old_fst, w_vcd, w_fst in self.get_time_range_times:
            vcd_s, fst_s = size_lookup.get((signals, timesteps), (0, 0))
            vcd_speedup = old_vcd / w_vcd if w_vcd > 0 and old_vcd > 0 else 0
            fst_speedup = old_fst / w_fst if w_fst > 0 and old_fst > 0 else 0
            old_vcd_str = format_time(old_vcd) if old_vcd > 0 else "N/A"
            old_fst_str = format_time(old_fst) if old_fst > 0 else "N/A"
            vcd_speedup_str = f"{vcd_speedup:.2f}x" if vcd_speedup > 0 else "N/A"
            fst_speedup_str = f"{fst_speedup:.2f}x" if fst_speedup > 0 else "N/A"
            lines.append(
                f"| {signals} | {timesteps} | {format_size(vcd_s)} | {format_size(fst_s)} | {old_vcd_str} | {old_fst_str} | {format_time(w_vcd)} | {format_time(w_fst)} | {vcd_speedup_str} | {fst_speedup_str} |"
            )
        lines.append("")

        # Get signal values performance (4-way)
        lines.append("## Signal Value Query Performance\n")
        lines.append("| Signals | Time Steps | VCD Size | FST Size | Query Range | Old VCD | Old FST | pywellen VCD | pywellen FST | pywellen VCD Speedup | pywellen FST Speedup |")
        lines.append("|---------|------------|----------|----------|-------------|---------|---------|--------------|--------------|----------------------|----------------------|")
        for signals, timesteps, query_range, old_vcd, old_fst, w_vcd, w_fst in self.get_values_times:
            vcd_s, fst_s = size_lookup.get((signals, timesteps), (0, 0))
            vcd_speedup = old_vcd / w_vcd if w_vcd > 0 and old_vcd > 0 else 0
            fst_speedup = old_fst / w_fst if w_fst > 0 and old_fst > 0 else 0
            old_vcd_str = format_time(old_vcd) if old_vcd > 0 else "N/A"
            old_fst_str = format_time(old_fst) if old_fst > 0 else "N/A"
            vcd_speedup_str = f"{vcd_speedup:.2f}x" if vcd_speedup > 0 else "N/A"
            fst_speedup_str = f"{fst_speedup:.2f}x" if fst_speedup > 0 else "N/A"
            lines.append(
                f"| {signals} | {timesteps} | {format_size(vcd_s)} | {format_size(fst_s)} | {query_range} | {old_vcd_str} | {old_fst_str} | {format_time(w_vcd)} | {format_time(w_fst)} | {vcd_speedup_str} | {fst_speedup_str} |"
            )
        lines.append("")

        # Conversion performance
        if self.conversion_times:
            lines.append("## VCD <-> FST Conversion Performance\n")
            lines.append("| Signals | Time Steps | VCD Size | FST Size | VCD -> FST | FST -> VCD |")
            lines.append("|---------|------------|----------|----------|------------|------------|")
            for signals, timesteps, vcd_to_fst, fst_to_vcd in self.conversion_times:
                vcd_s, fst_s = size_lookup.get((signals, timesteps), (0, 0))
                lines.append(
                    f"| {signals} | {timesteps} | {format_size(vcd_s)} | {format_size(fst_s)} | {format_time(vcd_to_fst)} | {format_time(fst_to_vcd)} |"
                )
            lines.append("")

        # Summary and conclusions
        lines.append("## Summary\n")

        if self.file_sizes:
            avg_compression = statistics.mean(
                vcd / fst for _, _, vcd, fst in self.file_sizes if fst > 0
            )
            lines.append(f"- **Average FST compression ratio**: {avg_compression:.2f}x smaller than VCD")

        if self.load_times:
            vcd_load_entries = [(old_vcd, w_vcd) for _, _, old_vcd, _, w_vcd, _ in self.load_times if w_vcd > 0 and old_vcd > 0]
            fst_load_entries = [(old_fst, w_fst) for _, _, _, old_fst, _, w_fst in self.load_times if w_fst > 0 and old_fst > 0]
            if vcd_load_entries:
                avg_vcd_speedup = statistics.mean(old / new for old, new in vcd_load_entries)
                lines.append(f"- **pywellen VCD load speedup** (vs vcdvcd): {avg_vcd_speedup:.2f}x")
            if fst_load_entries:
                avg_fst_speedup = statistics.mean(old / new for old, new in fst_load_entries)
                lines.append(f"- **pywellen FST load speedup** (vs pylibfst): {avg_fst_speedup:.2f}x")

        if self.get_values_times:
            vcd_val_entries = [(old_vcd, w_vcd) for _, _, _, old_vcd, _, w_vcd, _ in self.get_values_times if w_vcd > 0 and old_vcd > 0]
            fst_val_entries = [(old_fst, w_fst) for _, _, _, _, old_fst, _, w_fst in self.get_values_times if w_fst > 0 and old_fst > 0]
            if vcd_val_entries:
                avg_vcd_speedup = statistics.mean(old / new for old, new in vcd_val_entries)
                lines.append(f"- **pywellen VCD value query speedup** (vs vcdvcd): {avg_vcd_speedup:.2f}x")
            if fst_val_entries:
                avg_fst_speedup = statistics.mean(old / new for old, new in fst_val_entries)
                lines.append(f"- **pywellen FST value query speedup** (vs pylibfst): {avg_fst_speedup:.2f}x")

        lines.append("")
        lines.append("## Recommendations\n")
        lines.append("- Use **pywellen** (unified backend) for both VCD and FST for best performance")
        lines.append("- Use **FST format** for large waveforms to save disk space and improve load times")
        lines.append("- Use **VCD format** for maximum compatibility and text-based debugging")
        lines.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(lines))

        return output_path


# Global results collector
_benchmark_results = BenchmarkResults()


@pytest.fixture(scope="module")
def benchmark_files(tmp_path_factory):
    """Generate all benchmark test files."""
    base_path = tmp_path_factory.mktemp("benchmark")
    files = {}

    print(f"\n{'='*60}")
    print(f"Generating benchmark files (scale: {SCALE})")
    print(f"{'='*60}")

    for num_signals in CONFIG["signal_counts"]:
        for num_timesteps in CONFIG["time_steps"]:
            key = (num_signals, num_timesteps)

            vcd_path = str(base_path / f"bench_{num_signals}sig_{num_timesteps}ts.vcd")
            fst_path = str(base_path / f"bench_{num_signals}sig_{num_timesteps}ts.fst")

            print(f"\nGenerating: {num_signals} signals x {num_timesteps} timesteps...")

            start = time.perf_counter()
            vcd_size = generate_large_vcd(vcd_path, num_signals, num_timesteps)
            vcd_gen_time = time.perf_counter() - start
            print(f"  VCD: {format_size(vcd_size)} in {format_time(vcd_gen_time)}")

            start = time.perf_counter()
            fst_size = generate_large_fst(fst_path, num_signals, num_timesteps)
            fst_gen_time = time.perf_counter() - start
            print(f"  FST: {format_size(fst_size)} in {format_time(fst_gen_time)}")

            files[key] = {
                "vcd_path": vcd_path,
                "fst_path": fst_path,
                "vcd_size": vcd_size,
                "fst_size": fst_size,
            }

            _benchmark_results.file_sizes.append(
                (num_signals, num_timesteps, vcd_size, fst_size)
            )

    print(f"\n{'='*60}\n")
    return files


@pytest.fixture(autouse=True)
def reset_parsers():
    """Reset global parsers before each test."""
    from src import parsers
    parsers._vcd_parser = None
    parsers._fst_parser = None
    parsers._wellen_parser = None
    yield
    parsers._vcd_parser = None
    parsers._fst_parser = None
    parsers._wellen_parser = None


class TestBenchmark:
    """Benchmark test suite for 4-way performance comparison."""

    @pytest.mark.asyncio
    async def test_load_performance(self, benchmark_files):
        """Test file loading performance: Old VCD / Old FST / pywellen VCD / pywellen FST."""
        print("\n" + "=" * 60)
        print("Load Performance Test (4-way)")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            skip_vcd = should_skip_old_vcd(paths["vcd_size"])
            print(f"\n{num_signals} signals x {num_timesteps} timesteps (VCD: {format_size(paths['vcd_size'])}, FST: {format_size(paths['fst_size'])}):")

            old_vcd_mean = 0
            if not skip_vcd:
                old_vcd_stats = await benchmark_async_function(
                    load_vcd_file, paths["vcd_path"], repeat=CONFIG["repeat"]
                )
                old_vcd_mean = old_vcd_stats["mean"]
                print(f"  Old VCD (vcdvcd):   {format_time(old_vcd_mean)}")
            else:
                print(f"  Old VCD (vcdvcd):   SKIPPED (file too large)")

            old_fst_mean = 0
            if not SKIP_OLD_FST:
                old_fst_stats = await benchmark_async_function(
                    load_fst_file, paths["fst_path"], repeat=CONFIG["repeat"]
                )
                old_fst_mean = old_fst_stats["mean"]
                print(f"  Old FST (pylibfst): {format_time(old_fst_mean)}")
            else:
                print(f"  Old FST (pylibfst): SKIPPED")

            w_vcd_stats = await benchmark_async_function(
                load_wellen, paths["vcd_path"], repeat=CONFIG["repeat"]
            )
            print(f"  pywellen VCD:       {format_time(w_vcd_stats['mean'])}")

            w_fst_stats = await benchmark_async_function(
                load_wellen, paths["fst_path"], repeat=CONFIG["repeat"]
            )
            print(f"  pywellen FST:       {format_time(w_fst_stats['mean'])}")

            if old_vcd_mean > 0:
                vcd_speedup = old_vcd_mean / w_vcd_stats["mean"]
                print(f"  pywellen VCD speedup: {vcd_speedup:.2f}x")
            if old_fst_mean > 0:
                fst_speedup = old_fst_mean / w_fst_stats["mean"]
                print(f"  pywellen FST speedup: {fst_speedup:.2f}x")

            _benchmark_results.load_times.append(
                (num_signals, num_timesteps,
                 old_vcd_mean, old_fst_mean,
                 w_vcd_stats["mean"], w_fst_stats["mean"])
            )

    @pytest.mark.asyncio
    async def test_get_signals_performance(self, benchmark_files):
        """Test signal list retrieval performance (4-way)."""
        print("\n" + "=" * 60)
        print("Get Signals Performance Test (4-way)")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            skip_vcd = should_skip_old_vcd(paths["vcd_size"])
            print(f"\n{num_signals} signals x {num_timesteps} timesteps (VCD: {format_size(paths['vcd_size'])}, FST: {format_size(paths['fst_size'])}):")

            old_vcd_mean = 0
            if not skip_vcd:
                await load_vcd_file(paths["vcd_path"])
                old_vcd_stats = await benchmark_async_function(get_vcd_signals, repeat=CONFIG["repeat"])
                old_vcd_mean = old_vcd_stats["mean"]
                print(f"  Old VCD:      {format_time(old_vcd_mean)}")
            else:
                print(f"  Old VCD:      SKIPPED")

            old_fst_mean = 0
            if not SKIP_OLD_FST:
                await load_fst_file(paths["fst_path"])
                old_fst_stats = await benchmark_async_function(get_fst_signals, repeat=CONFIG["repeat"])
                old_fst_mean = old_fst_stats["mean"]
                print(f"  Old FST:      {format_time(old_fst_mean)}")
            else:
                print(f"  Old FST:      SKIPPED")

            await load_wellen(paths["vcd_path"])
            w_vcd_stats = await benchmark_async_function(get_wellen_signals, repeat=CONFIG["repeat"])
            print(f"  pywellen VCD: {format_time(w_vcd_stats['mean'])}")

            await load_wellen(paths["fst_path"])
            w_fst_stats = await benchmark_async_function(get_wellen_signals, repeat=CONFIG["repeat"])
            print(f"  pywellen FST: {format_time(w_fst_stats['mean'])}")

            _benchmark_results.get_signals_times.append(
                (num_signals, num_timesteps,
                 old_vcd_mean, old_fst_mean,
                 w_vcd_stats["mean"], w_fst_stats["mean"])
            )

    @pytest.mark.asyncio
    async def test_get_time_range_performance(self, benchmark_files):
        """Test time range query performance (4-way)."""
        print("\n" + "=" * 60)
        print("Get Time Range Performance Test (4-way)")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            skip_vcd = should_skip_old_vcd(paths["vcd_size"])
            print(f"\n{num_signals} signals x {num_timesteps} timesteps (VCD: {format_size(paths['vcd_size'])}, FST: {format_size(paths['fst_size'])}):")

            old_vcd_mean = 0
            if not skip_vcd:
                await load_vcd_file(paths["vcd_path"])
                old_vcd_stats = await benchmark_async_function(get_vcd_time_range, repeat=CONFIG["repeat"])
                old_vcd_mean = old_vcd_stats["mean"]
                print(f"  Old VCD:      {format_time(old_vcd_mean)}")
            else:
                print(f"  Old VCD:      SKIPPED")

            old_fst_mean = 0
            if not SKIP_OLD_FST:
                await load_fst_file(paths["fst_path"])
                old_fst_stats = await benchmark_async_function(get_fst_time_range, repeat=CONFIG["repeat"])
                old_fst_mean = old_fst_stats["mean"]
                print(f"  Old FST:      {format_time(old_fst_mean)}")
            else:
                print(f"  Old FST:      SKIPPED")

            await load_wellen(paths["vcd_path"])
            w_vcd_stats = await benchmark_async_function(get_wellen_time_range, repeat=CONFIG["repeat"])
            print(f"  pywellen VCD: {format_time(w_vcd_stats['mean'])}")

            await load_wellen(paths["fst_path"])
            w_fst_stats = await benchmark_async_function(get_wellen_time_range, repeat=CONFIG["repeat"])
            print(f"  pywellen FST: {format_time(w_fst_stats['mean'])}")

            _benchmark_results.get_time_range_times.append(
                (num_signals, num_timesteps,
                 old_vcd_mean, old_fst_mean,
                 w_vcd_stats["mean"], w_fst_stats["mean"])
            )

    @pytest.mark.asyncio
    async def test_get_signal_values_performance(self, benchmark_files):
        """Test signal value query performance (4-way)."""
        print("\n" + "=" * 60)
        print("Get Signal Values Performance Test (4-way)")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            skip_vcd = should_skip_old_vcd(paths["vcd_size"])
            print(f"\n{num_signals} signals x {num_timesteps} timesteps (VCD: {format_size(paths['vcd_size'])}, FST: {format_size(paths['fst_size'])}):")

            if not skip_vcd:
                await load_vcd_file(paths["vcd_path"])
            if not SKIP_OLD_FST:
                await load_fst_file(paths["fst_path"])

            max_time = (num_timesteps - 1) * 10
            query_ranges = [
                (0, max_time // 10, "10%"),
                (0, max_time // 2, "50%"),
                (0, max_time, "100%"),
            ]

            for start_time, end_time, range_desc in query_ranges:
                patterns = ["sig_0000", "sig_0001", "sig_0002"]

                old_vcd_mean = 0
                if not skip_vcd:
                    old_vcd_stats = await benchmark_async_function(
                        get_vcd_signal_values, patterns, start_time, end_time,
                        repeat=CONFIG["repeat"],
                    )
                    old_vcd_mean = old_vcd_stats["mean"]
                    print(f"  Old VCD ({range_desc}):      {format_time(old_vcd_mean)}")
                else:
                    print(f"  Old VCD ({range_desc}):      SKIPPED")

                old_fst_mean = 0
                if not SKIP_OLD_FST:
                    old_fst_stats = await benchmark_async_function(
                        get_fst_signal_values, patterns, start_time, end_time,
                        repeat=CONFIG["repeat"],
                    )
                    old_fst_mean = old_fst_stats["mean"]
                    print(f"  Old FST ({range_desc}):      {format_time(old_fst_mean)}")
                else:
                    print(f"  Old FST ({range_desc}):      SKIPPED")

                await load_wellen(paths["vcd_path"])
                w_vcd_stats = await benchmark_async_function(
                    get_wellen_signal_values, patterns, start_time, end_time,
                    repeat=CONFIG["repeat"],
                )
                print(f"  pywellen VCD ({range_desc}): {format_time(w_vcd_stats['mean'])}")

                await load_wellen(paths["fst_path"])
                w_fst_stats = await benchmark_async_function(
                    get_wellen_signal_values, patterns, start_time, end_time,
                    repeat=CONFIG["repeat"],
                )
                print(f"  pywellen FST ({range_desc}): {format_time(w_fst_stats['mean'])}")

                if old_vcd_mean > 0:
                    print(f"  VCD speedup ({range_desc}): {old_vcd_mean / w_vcd_stats['mean']:.2f}x")
                if old_fst_mean > 0:
                    print(f"  FST speedup ({range_desc}): {old_fst_mean / w_fst_stats['mean']:.2f}x")

                _benchmark_results.get_values_times.append(
                    (num_signals, num_timesteps, range_desc,
                     old_vcd_mean, old_fst_mean,
                     w_vcd_stats["mean"], w_fst_stats["mean"])
                )

    @pytest.mark.asyncio
    async def test_conversion_performance(self, benchmark_files):
        """Test VCD <-> FST conversion performance."""
        print("\n" + "=" * 60)
        print("VCD <-> FST Conversion Performance Test")
        print("=" * 60)

        has_any = False
        for (num_signals, num_timesteps), paths in benchmark_files.items():
            if should_skip_old_vcd(paths["vcd_size"]) or SKIP_OLD_FST:
                print(f"\n{num_signals} signals x {num_timesteps} timesteps: SKIPPED (file too large)")
                continue
            has_any = True
            print(f"\n{num_signals} signals x {num_timesteps} timesteps (VCD: {format_size(paths['vcd_size'])}, FST: {format_size(paths['fst_size'])}):")

            # VCD -> FST conversion
            vcd_to_fst_times = []
            for _ in range(CONFIG["repeat"]):
                output_fst = paths["fst_path"] + ".converted.fst"
                start = time.perf_counter()
                convert_vcd_to_fst(paths["vcd_path"], output_fst)
                elapsed = time.perf_counter() - start
                vcd_to_fst_times.append(elapsed)
                if Path(output_fst).exists():
                    Path(output_fst).unlink()

            vcd_to_fst_mean = statistics.mean(vcd_to_fst_times)
            print(f"  VCD -> FST: {format_time(vcd_to_fst_mean)}")

            # FST -> VCD conversion
            fst_to_vcd_times = []
            for _ in range(CONFIG["repeat"]):
                output_vcd = paths["vcd_path"] + ".converted.vcd"
                start = time.perf_counter()
                convert_fst_to_vcd(paths["fst_path"], output_vcd)
                elapsed = time.perf_counter() - start
                fst_to_vcd_times.append(elapsed)
                if Path(output_vcd).exists():
                    Path(output_vcd).unlink()

            fst_to_vcd_mean = statistics.mean(fst_to_vcd_times)
            print(f"  FST -> VCD: {format_time(fst_to_vcd_mean)}")

            _benchmark_results.conversion_times.append(
                (num_signals, num_timesteps, vcd_to_fst_mean, fst_to_vcd_mean)
            )


def convert_vcd_to_fst(vcd_path: str, fst_path: str) -> None:
    """Convert a VCD file to FST format."""
    from vcdvcd import VCDVCD
    import pylibfst
    from pylibfst import lib, ffi

    vcd = VCDVCD(vcd_path)

    ctx = lib.fstWriterCreate(fst_path.encode("utf-8"), 1)
    if ctx == ffi.NULL:
        raise RuntimeError("Failed to create FST writer")

    try:
        lib.fstWriterSetTimescale(ctx, -9)

        signal_handles = {}
        current_scope = None

        for signal_path in vcd.signals:
            signal = vcd[signal_path]
            parts = signal_path.split(".")

            scope = ".".join(parts[:-1]) if len(parts) > 1 else "top"
            name = parts[-1] if len(parts) > 1 else signal_path

            if scope != current_scope:
                if current_scope is not None:
                    lib.fstWriterSetUpscope(ctx)
                lib.fstWriterSetScope(
                    ctx, lib.FST_ST_VCD_MODULE, scope.encode("utf-8"), ffi.NULL
                )
                current_scope = scope

            size_raw = signal.size if hasattr(signal, "size") else 1
            size = int(size_raw) if size_raw else 1

            handle = lib.fstWriterCreateVar(
                ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, size,
                name.encode("utf-8"), 0,
            )
            signal_handles[signal_path] = (handle, size)

        if current_scope is not None:
            lib.fstWriterSetUpscope(ctx)

        all_changes = []
        for signal_path in vcd.signals:
            signal = vcd[signal_path]
            for t, value in signal.tv:
                all_changes.append((t, signal_path, value))

        all_changes.sort(key=lambda x: x[0])

        current_time = None
        for t, signal_path, value in all_changes:
            if t != current_time:
                lib.fstWriterEmitTimeChange(ctx, t)
                current_time = t

            handle, size = signal_handles[signal_path]
            if isinstance(value, int):
                value_str = format(value, f"0{size}b")
            else:
                value_str = str(value)
            lib.fstWriterEmitValueChange(ctx, handle, value_str.encode("utf-8"))

    finally:
        lib.fstWriterClose(ctx)


def convert_fst_to_vcd(fst_path: str, vcd_path: str) -> None:
    """Convert an FST file to VCD format."""
    from vcd.writer import VCDWriter

    parser = FstParser(fst_path)

    try:
        signals, _ = parser.get_signal_list(limit=0)
        start_time, end_time = parser.get_time_range()

        with open(vcd_path, "w") as f:
            with VCDWriter(f, timescale="1ns", date="converted") as writer:
                vcd_vars = {}
                for sig in signals:
                    path_parts = sig["path"].split(".")
                    scope = path_parts[0] if len(path_parts) > 1 else "top"
                    name = path_parts[-1]
                    size = sig.get("size", 1)

                    var = writer.register_var(scope, name, "wire", size=size, init=0)
                    vcd_vars[sig["path"]] = (var, size)

                all_patterns = [sig["path"] for sig in signals]
                values, _ = parser.get_signal_values(all_patterns, start_time, end_time)

                all_changes = []
                for signal_path, time_values in values.items():
                    if signal_path in vcd_vars:
                        var, size = vcd_vars[signal_path]
                        for t, value in time_values:
                            all_changes.append((t, var, value, size))

                all_changes.sort(key=lambda x: x[0])

                for t, var, value, size in all_changes:
                    try:
                        if value.startswith('b'):
                            value = value[1:]
                        int_value = int(value, 2)
                    except ValueError:
                        int_value = 0
                    writer.change(var, t, int_value)

    finally:
        parser.close()


@pytest.fixture(scope="session", autouse=True)
def generate_report(request):
    """Generate the benchmark report after all tests complete."""
    yield
    report_path = Path(__file__).parent.parent / "docs" / "benchmark_report.md"
    _benchmark_results.generate_report(str(report_path))
    print(f"\nBenchmark report generated: {report_path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
