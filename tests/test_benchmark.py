"""Performance benchmark tests for VCD and FST waveform parsing.

This module provides comprehensive performance benchmarking for:
- File loading (VCD vs FST)
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
from src.parsers import FstParser, WaveformParser, set_vcd_parser, set_fst_parser, get_vcd_parser, get_fst_parser


# Wrapper functions for MCP tools (to maintain compatibility with benchmark tests)
async def load_vcd_file(vcd_path: str) -> str:
    """Load a VCD file."""
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
    """Load an FST file."""
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


async def get_vcd_signals() -> str:
    """Get VCD signal list."""
    try:
        parser = get_vcd_parser()
    except ValueError as e:
        return str(e)
    signals, total_count = parser.get_signal_list(limit=0)
    if not signals:
        return "No signals found in VCD file."
    lines = [f"Signals in VCD file (showing {len(signals)}/{total_count}):"]
    for sig in signals:
        lines.append(f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}")
    return "\n".join(lines)


async def get_fst_signals() -> str:
    """Get FST signal list."""
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)
    signals, total_count = parser.get_signal_list(limit=0)
    if not signals:
        return "No signals found in FST file."
    lines = [f"Signals in FST file (showing {len(signals)}/{total_count}):"]
    for sig in signals:
        lines.append(f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}")
    return "\n".join(lines)


async def get_vcd_time_range() -> str:
    """Get VCD time range."""
    try:
        parser = get_vcd_parser()
    except ValueError as e:
        return str(e)
    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


async def get_fst_time_range() -> str:
    """Get FST time range."""
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)
    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


async def get_vcd_signal_values(
    signal_patterns: list[str], start_time: int, end_time: int
) -> str:
    """Get VCD signal values."""
    try:
        parser = get_vcd_parser()
    except ValueError as e:
        return str(e)
    if start_time > end_time:
        return "Error: start_time must be less than or equal to end_time"
    values, _ = parser.get_signal_values(signal_patterns, start_time, end_time)
    if not values:
        return f"No matching signals found or no values in time range [{start_time}, {end_time}]"
    lines = [f"Signal values in time range [{start_time}, {end_time}]:"]
    for signal, changes in values.items():
        lines.append(f"\n{signal}:")
        for t, v in changes:
            lines.append(f"  {t:>10}: {v}")
    return "\n".join(lines)


async def get_fst_signal_values(
    signal_patterns: list[str], start_time: int, end_time: int
) -> str:
    """Get FST signal values."""
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)
    if start_time > end_time:
        return "Error: start_time must be less than or equal to end_time"
    values, _ = parser.get_signal_values(signal_patterns, start_time, end_time)
    if not values:
        return f"No matching signals found or no values in time range [{start_time}, {end_time}]"
    lines = [f"Signal values in time range [{start_time}, {end_time}]:"]
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
}

CONFIG = SCALE_CONFIG.get(SCALE, SCALE_CONFIG["medium"])


def generate_large_vcd(path: str, num_signals: int, num_timesteps: int) -> int:
    """Generate a VCD file with specified number of signals and timesteps.

    Args:
        path: Output file path
        num_signals: Number of signals to generate
        num_timesteps: Number of time steps to simulate

    Returns:
        File size in bytes
    """
    from vcd.writer import VCDWriter

    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        with VCDWriter(f, timescale="1ns", date="benchmark") as writer:
            # Create signals
            signals = []
            for i in range(num_signals):
                # Mix of different signal sizes
                if i % 3 == 0:
                    size = 1  # 1-bit signals
                elif i % 3 == 1:
                    size = 8  # 8-bit signals
                else:
                    size = 32  # 32-bit signals

                sig = writer.register_var(
                    "bench", f"sig_{i:04d}", "wire", size=size, init=0
                )
                signals.append((sig, size))

            # Generate time steps with value changes
            for t in range(num_timesteps):
                timestamp = t * 10

                # Change a subset of signals at each timestep
                # This simulates realistic waveform activity
                for i, (sig, size) in enumerate(signals):
                    # Change signal based on pattern
                    if t % (i + 1) == 0:
                        if size == 1:
                            value = t % 2
                        else:
                            value = (t * (i + 1)) % (2**size)
                        writer.change(sig, timestamp, value)

    return Path(path).stat().st_size


def generate_large_fst(path: str, num_signals: int, num_timesteps: int) -> int:
    """Generate an FST file with specified number of signals and timesteps.

    Args:
        path: Output file path
        num_signals: Number of signals to generate
        num_timesteps: Number of time steps to simulate

    Returns:
        File size in bytes
    """
    import pylibfst
    from pylibfst import lib, ffi

    Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Create writer context with compression
    ctx = lib.fstWriterCreate(path.encode("utf-8"), 1)
    if ctx == ffi.NULL:
        raise RuntimeError("Failed to create FST writer")

    try:
        # Set timescale to 1ns (-9)
        lib.fstWriterSetTimescale(ctx, -9)

        # Set scope
        lib.fstWriterSetScope(ctx, lib.FST_ST_VCD_MODULE, b"bench", ffi.NULL)

        # Create signals
        handles = []
        for i in range(num_signals):
            # Mix of different signal sizes
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

        # Emit initial values at time 0
        lib.fstWriterEmitTimeChange(ctx, 0)
        for handle, size in handles:
            init_val = "0" * size
            lib.fstWriterEmitValueChange(ctx, handle, init_val.encode("utf-8"))

        # Generate time steps with value changes
        for t in range(1, num_timesteps):
            timestamp = t * 10
            lib.fstWriterEmitTimeChange(ctx, timestamp)

            # Change a subset of signals at each timestep
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
    """Run a function multiple times and return timing statistics.

    Args:
        func: Function to benchmark
        *args: Arguments to pass to the function
        repeat: Number of times to repeat the measurement

    Returns:
        Dictionary with min, max, mean, stdev timing statistics (in seconds)
    """
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
    """Run an async function multiple times and return timing statistics.

    Args:
        func: Async function to benchmark
        *args: Arguments to pass to the function
        repeat: Number of times to repeat the measurement

    Returns:
        Dictionary with min, max, mean, stdev timing statistics (in seconds)
    """
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
        self.load_times = []  # (signals, timesteps, vcd_time, fst_time)
        self.get_signals_times = []  # (signals, timesteps, vcd_time, fst_time)
        self.get_time_range_times = []  # (signals, timesteps, vcd_time, fst_time)
        self.get_values_times = []  # (signals, timesteps, query_range, vcd_time, fst_time)
        self.conversion_times = []  # (signals, timesteps, vcd_to_fst, fst_to_vcd)

    def generate_report(self, output_path: str):
        """Generate a Markdown report of the benchmark results."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

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

        # Load performance
        lines.append("## Load Performance\n")
        lines.append("| Signals | Time Steps | VCD Load | FST Load | FST Speedup |")
        lines.append("|---------|------------|----------|----------|-------------|")
        for signals, timesteps, vcd_time, fst_time in self.load_times:
            speedup = vcd_time / fst_time if fst_time > 0 else 0
            lines.append(
                f"| {signals} | {timesteps} | {format_time(vcd_time)} | {format_time(fst_time)} | {speedup:.2f}x |"
            )
        lines.append("")

        # Get signals performance
        lines.append("## Signal List Retrieval Performance\n")
        lines.append("| Signals | Time Steps | VCD get_signals | FST get_signals | FST Speedup |")
        lines.append("|---------|------------|-----------------|-----------------|-------------|")
        for signals, timesteps, vcd_time, fst_time in self.get_signals_times:
            speedup = vcd_time / fst_time if fst_time > 0 else 0
            lines.append(
                f"| {signals} | {timesteps} | {format_time(vcd_time)} | {format_time(fst_time)} | {speedup:.2f}x |"
            )
        lines.append("")

        # Get time range performance
        lines.append("## Time Range Query Performance\n")
        lines.append("| Signals | Time Steps | VCD get_time_range | FST get_time_range | FST Speedup |")
        lines.append("|---------|------------|--------------------|--------------------|-------------|")
        for signals, timesteps, vcd_time, fst_time in self.get_time_range_times:
            speedup = vcd_time / fst_time if fst_time > 0 else 0
            lines.append(
                f"| {signals} | {timesteps} | {format_time(vcd_time)} | {format_time(fst_time)} | {speedup:.2f}x |"
            )
        lines.append("")

        # Get signal values performance
        lines.append("## Signal Value Query Performance\n")
        lines.append("| Signals | Time Steps | Query Range | VCD get_values | FST get_values | FST Speedup |")
        lines.append("|---------|------------|-------------|----------------|----------------|-------------|")
        for signals, timesteps, query_range, vcd_time, fst_time in self.get_values_times:
            speedup = vcd_time / fst_time if fst_time > 0 else 0
            lines.append(
                f"| {signals} | {timesteps} | {query_range} | {format_time(vcd_time)} | {format_time(fst_time)} | {speedup:.2f}x |"
            )
        lines.append("")

        # Conversion performance
        if self.conversion_times:
            lines.append("## VCD <-> FST Conversion Performance\n")
            lines.append("| Signals | Time Steps | VCD -> FST | FST -> VCD |")
            lines.append("|---------|------------|------------|------------|")
            for signals, timesteps, vcd_to_fst, fst_to_vcd in self.conversion_times:
                lines.append(
                    f"| {signals} | {timesteps} | {format_time(vcd_to_fst)} | {format_time(fst_to_vcd)} |"
                )
            lines.append("")

        # Summary and conclusions
        lines.append("## Summary\n")

        # Calculate average compression ratio
        if self.file_sizes:
            avg_compression = statistics.mean(
                vcd / fst for _, _, vcd, fst in self.file_sizes if fst > 0
            )
            lines.append(f"- **Average FST compression ratio**: {avg_compression:.2f}x smaller than VCD")

        # Calculate average load speedup
        if self.load_times:
            avg_load_speedup = statistics.mean(
                vcd / fst for _, _, vcd, fst in self.load_times if fst > 0
            )
            lines.append(f"- **Average FST load speedup**: {avg_load_speedup:.2f}x faster than VCD")

        # Calculate average value query speedup
        if self.get_values_times:
            avg_query_speedup = statistics.mean(
                vcd / fst for _, _, _, vcd, fst in self.get_values_times if fst > 0
            )
            lines.append(f"- **Average FST value query speedup**: {avg_query_speedup:.2f}x faster than VCD")

        lines.append("")
        lines.append("## Recommendations\n")
        lines.append("- Use **FST format** for large waveforms to save disk space and improve load times")
        lines.append("- Use **VCD format** for maximum compatibility and text-based debugging")
        lines.append("- For interactive waveform viewing, FST provides better random access performance")
        lines.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(lines))

        return output_path


# Global results collector
_benchmark_results = BenchmarkResults()


@pytest.fixture(scope="module")
def benchmark_files(tmp_path_factory):
    """Generate all benchmark test files.

    Returns a dictionary with file paths for each configuration:
    {
        (num_signals, num_timesteps): {
            'vcd_path': str,
            'fst_path': str,
            'vcd_size': int,
            'fst_size': int,
        }
    }
    """
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

            # Generate VCD
            start = time.perf_counter()
            vcd_size = generate_large_vcd(vcd_path, num_signals, num_timesteps)
            vcd_gen_time = time.perf_counter() - start
            print(f"  VCD: {format_size(vcd_size)} in {format_time(vcd_gen_time)}")

            # Generate FST
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

            # Record file sizes
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
    yield
    parsers._vcd_parser = None
    parsers._fst_parser = None


class TestBenchmark:
    """Benchmark test suite for VCD and FST performance comparison."""

    @pytest.mark.asyncio
    async def test_load_performance(self, benchmark_files):
        """Test file loading performance for VCD vs FST."""
        print("\n" + "=" * 60)
        print("Load Performance Test")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            print(f"\n{num_signals} signals x {num_timesteps} timesteps:")

            # Benchmark VCD loading
            vcd_stats = await benchmark_async_function(
                load_vcd_file, paths["vcd_path"], repeat=CONFIG["repeat"]
            )
            print(f"  VCD load: {format_time(vcd_stats['mean'])} (stdev: {format_time(vcd_stats['stdev'])})")

            # Benchmark FST loading
            fst_stats = await benchmark_async_function(
                load_fst_file, paths["fst_path"], repeat=CONFIG["repeat"]
            )
            print(f"  FST load: {format_time(fst_stats['mean'])} (stdev: {format_time(fst_stats['stdev'])})")

            speedup = vcd_stats["mean"] / fst_stats["mean"] if fst_stats["mean"] > 0 else 0
            print(f"  FST speedup: {speedup:.2f}x")

            _benchmark_results.load_times.append(
                (num_signals, num_timesteps, vcd_stats["mean"], fst_stats["mean"])
            )

    @pytest.mark.asyncio
    async def test_get_signals_performance(self, benchmark_files):
        """Test signal list retrieval performance for VCD vs FST."""
        print("\n" + "=" * 60)
        print("Get Signals Performance Test")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            print(f"\n{num_signals} signals x {num_timesteps} timesteps:")

            # Load files first
            await load_vcd_file(paths["vcd_path"])
            await load_fst_file(paths["fst_path"])

            # Benchmark VCD get_signals
            vcd_stats = await benchmark_async_function(
                get_vcd_signals, repeat=CONFIG["repeat"]
            )
            print(f"  VCD get_signals: {format_time(vcd_stats['mean'])}")

            # Benchmark FST get_signals
            fst_stats = await benchmark_async_function(
                get_fst_signals, repeat=CONFIG["repeat"]
            )
            print(f"  FST get_signals: {format_time(fst_stats['mean'])}")

            speedup = vcd_stats["mean"] / fst_stats["mean"] if fst_stats["mean"] > 0 else 0
            print(f"  FST speedup: {speedup:.2f}x")

            _benchmark_results.get_signals_times.append(
                (num_signals, num_timesteps, vcd_stats["mean"], fst_stats["mean"])
            )

    @pytest.mark.asyncio
    async def test_get_time_range_performance(self, benchmark_files):
        """Test time range query performance for VCD vs FST."""
        print("\n" + "=" * 60)
        print("Get Time Range Performance Test")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            print(f"\n{num_signals} signals x {num_timesteps} timesteps:")

            # Load files first
            await load_vcd_file(paths["vcd_path"])
            await load_fst_file(paths["fst_path"])

            # Benchmark VCD get_time_range
            vcd_stats = await benchmark_async_function(
                get_vcd_time_range, repeat=CONFIG["repeat"]
            )
            print(f"  VCD get_time_range: {format_time(vcd_stats['mean'])}")

            # Benchmark FST get_time_range
            fst_stats = await benchmark_async_function(
                get_fst_time_range, repeat=CONFIG["repeat"]
            )
            print(f"  FST get_time_range: {format_time(fst_stats['mean'])}")

            speedup = vcd_stats["mean"] / fst_stats["mean"] if fst_stats["mean"] > 0 else 0
            print(f"  FST speedup: {speedup:.2f}x")

            _benchmark_results.get_time_range_times.append(
                (num_signals, num_timesteps, vcd_stats["mean"], fst_stats["mean"])
            )

    @pytest.mark.asyncio
    async def test_get_signal_values_performance(self, benchmark_files):
        """Test signal value query performance for VCD vs FST."""
        print("\n" + "=" * 60)
        print("Get Signal Values Performance Test")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            print(f"\n{num_signals} signals x {num_timesteps} timesteps:")

            # Load files first
            await load_vcd_file(paths["vcd_path"])
            await load_fst_file(paths["fst_path"])

            # Test different query ranges
            max_time = (num_timesteps - 1) * 10
            query_ranges = [
                (0, max_time // 10, "10%"),  # First 10%
                (0, max_time // 2, "50%"),  # First 50%
                (0, max_time, "100%"),  # Full range
            ]

            for start_time, end_time, range_desc in query_ranges:
                # Query a few signals
                patterns = ["sig_0000", "sig_0001", "sig_0002"]

                # Benchmark VCD get_signal_values
                vcd_stats = await benchmark_async_function(
                    get_vcd_signal_values,
                    patterns,
                    start_time,
                    end_time,
                    repeat=CONFIG["repeat"],
                )
                print(f"  VCD get_values ({range_desc}): {format_time(vcd_stats['mean'])}")

                # Benchmark FST get_signal_values
                fst_stats = await benchmark_async_function(
                    get_fst_signal_values,
                    patterns,
                    start_time,
                    end_time,
                    repeat=CONFIG["repeat"],
                )
                print(f"  FST get_values ({range_desc}): {format_time(fst_stats['mean'])}")

                speedup = vcd_stats["mean"] / fst_stats["mean"] if fst_stats["mean"] > 0 else 0
                print(f"  FST speedup ({range_desc}): {speedup:.2f}x")

                _benchmark_results.get_values_times.append(
                    (num_signals, num_timesteps, range_desc, vcd_stats["mean"], fst_stats["mean"])
                )

    @pytest.mark.asyncio
    async def test_conversion_performance(self, benchmark_files):
        """Test VCD <-> FST conversion performance."""
        print("\n" + "=" * 60)
        print("VCD <-> FST Conversion Performance Test")
        print("=" * 60)

        for (num_signals, num_timesteps), paths in benchmark_files.items():
            print(f"\n{num_signals} signals x {num_timesteps} timesteps:")

            # VCD -> FST conversion
            vcd_to_fst_times = []
            for _ in range(CONFIG["repeat"]):
                output_fst = paths["fst_path"] + ".converted.fst"
                start = time.perf_counter()
                convert_vcd_to_fst(paths["vcd_path"], output_fst)
                elapsed = time.perf_counter() - start
                vcd_to_fst_times.append(elapsed)
                # Clean up
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
                # Clean up
                if Path(output_vcd).exists():
                    Path(output_vcd).unlink()

            fst_to_vcd_mean = statistics.mean(fst_to_vcd_times)
            print(f"  FST -> VCD: {format_time(fst_to_vcd_mean)}")

            _benchmark_results.conversion_times.append(
                (num_signals, num_timesteps, vcd_to_fst_mean, fst_to_vcd_mean)
            )


def convert_vcd_to_fst(vcd_path: str, fst_path: str) -> None:
    """Convert a VCD file to FST format.

    Uses pyvcd to read the VCD and pylibfst to write the FST.
    """
    from vcdvcd import VCDVCD
    import pylibfst
    from pylibfst import lib, ffi

    # Parse VCD file
    vcd = VCDVCD(vcd_path)

    # Create FST writer
    ctx = lib.fstWriterCreate(fst_path.encode("utf-8"), 1)
    if ctx == ffi.NULL:
        raise RuntimeError("Failed to create FST writer")

    try:
        # Set timescale (default to 1ns)
        lib.fstWriterSetTimescale(ctx, -9)

        # Track scopes and create variables
        signal_handles = {}
        current_scope = None

        for signal_path in vcd.signals:
            signal = vcd[signal_path]
            parts = signal_path.split(".")

            # Handle scope
            scope = ".".join(parts[:-1]) if len(parts) > 1 else "top"
            name = parts[-1] if len(parts) > 1 else signal_path

            if scope != current_scope:
                if current_scope is not None:
                    lib.fstWriterSetUpscope(ctx)
                lib.fstWriterSetScope(
                    ctx, lib.FST_ST_VCD_MODULE, scope.encode("utf-8"), ffi.NULL
                )
                current_scope = scope

            # Get signal size (vcdvcd returns size as string)
            size_raw = signal.size if hasattr(signal, "size") else 1
            size = int(size_raw) if size_raw else 1

            # Create variable
            handle = lib.fstWriterCreateVar(
                ctx,
                lib.FST_VT_VCD_WIRE,
                lib.FST_VD_IMPLICIT,
                size,
                name.encode("utf-8"),
                0,
            )
            signal_handles[signal_path] = (handle, size)

        if current_scope is not None:
            lib.fstWriterSetUpscope(ctx)

        # Collect all time-value pairs and sort by time
        all_changes = []
        for signal_path in vcd.signals:
            signal = vcd[signal_path]
            handle, size = signal_handles[signal_path]
            for time, value in signal.tv:
                all_changes.append((time, signal_path, value))

        all_changes.sort(key=lambda x: x[0])

        # Emit value changes
        current_time = None
        for time, signal_path, value in all_changes:
            if time != current_time:
                lib.fstWriterEmitTimeChange(ctx, time)
                current_time = time

            handle, size = signal_handles[signal_path]
            # Format value as binary string
            if isinstance(value, int):
                value_str = format(value, f"0{size}b")
            else:
                value_str = str(value)
            lib.fstWriterEmitValueChange(ctx, handle, value_str.encode("utf-8"))

    finally:
        lib.fstWriterClose(ctx)


def convert_fst_to_vcd(fst_path: str, vcd_path: str) -> None:
    """Convert an FST file to VCD format.

    Uses pylibfst to read the FST and pyvcd to write the VCD.
    """
    from vcd.writer import VCDWriter

    # Parse FST file
    parser = FstParser(fst_path)

    try:
        signals, _ = parser.get_signal_list(limit=0)
        start_time, end_time = parser.get_time_range()

        with open(vcd_path, "w") as f:
            with VCDWriter(f, timescale="1ns", date="converted") as writer:
                # Register all signals
                vcd_vars = {}
                for sig in signals:
                    path_parts = sig["path"].split(".")
                    scope = path_parts[0] if len(path_parts) > 1 else "top"
                    name = path_parts[-1]
                    size = sig.get("size", 1)

                    var = writer.register_var(scope, name, "wire", size=size, init=0)
                    vcd_vars[sig["path"]] = (var, size)

                # Get all signal values
                all_patterns = [sig["path"] for sig in signals]
                values, _ = parser.get_signal_values(all_patterns, start_time, end_time)

                # Collect all changes and sort by time
                all_changes = []
                for signal_path, time_values in values.items():
                    if signal_path in vcd_vars:
                        var, size = vcd_vars[signal_path]
                        for time, value in time_values:
                            all_changes.append((time, var, value, size))

                all_changes.sort(key=lambda x: x[0])

                # Write changes
                for time, var, value, size in all_changes:
                    # Convert binary string to integer (strip 'b' prefix if present)
                    try:
                        if value.startswith('b'):
                            value = value[1:]
                        int_value = int(value, 2)
                    except ValueError:
                        int_value = 0
                    writer.change(var, time, int_value)

    finally:
        parser.close()


@pytest.fixture(scope="session", autouse=True)
def generate_report(request):
    """Generate the benchmark report after all tests complete."""
    yield
    # Generate report after all tests
    report_path = Path(__file__).parent.parent / "docs" / "benchmark_report.md"
    _benchmark_results.generate_report(str(report_path))
    print(f"\nBenchmark report generated: {report_path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
