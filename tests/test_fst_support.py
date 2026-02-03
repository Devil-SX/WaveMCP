"""Tests for Wave MCP Server FST functions."""

from pathlib import Path

import pytest

# Import the classes and functions from the new module structure
from src.parsers import FstParser, set_fst_parser, get_fst_parser


def create_test_fst_file(fst_path: str):
    """Create a test FST file using pylibfst C API."""
    import pylibfst
    from pylibfst import lib, ffi

    # Create writer context
    ctx = lib.fstWriterCreate(fst_path.encode('utf-8'), 1)  # 1 = use compression
    if ctx == ffi.NULL:
        raise RuntimeError("Failed to create FST writer")

    # Set timescale to 1ns (-9)
    lib.fstWriterSetTimescale(ctx, -9)

    # Set scope (module name)
    lib.fstWriterSetScope(ctx, lib.FST_ST_VCD_MODULE, b"top", ffi.NULL)

    # Create variables
    clk = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 1, b"clk", 0)
    rst = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 1, b"rst", 0)
    counter = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 8, b"counter", 0)
    enable = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 1, b"enable", 0)
    state = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 2, b"state", 0)

    # Go up scope
    lib.fstWriterSetUpscope(ctx)

    # Emit initial values at time 0
    lib.fstWriterEmitTimeChange(ctx, 0)
    lib.fstWriterEmitValueChange(ctx, clk, b"0")
    lib.fstWriterEmitValueChange(ctx, rst, b"1")
    lib.fstWriterEmitValueChange(ctx, counter, b"00000000")
    lib.fstWriterEmitValueChange(ctx, enable, b"0")
    lib.fstWriterEmitValueChange(ctx, state, b"00")

    # Simulation timeline
    for t in range(1, 100):
        timestamp = t * 10

        lib.fstWriterEmitTimeChange(ctx, timestamp)

        # Clock toggles every 10ns
        if t % 2 == 0:
            lib.fstWriterEmitValueChange(ctx, clk, b"1")
        else:
            lib.fstWriterEmitValueChange(ctx, clk, b"0")

        # Reset deasserts at t=20
        if t == 2:
            lib.fstWriterEmitValueChange(ctx, rst, b"0")

        # Enable signal toggles
        if t in [10, 30, 50, 70]:
            lib.fstWriterEmitValueChange(ctx, enable, b"1")
        elif t in [20, 40, 60, 80]:
            lib.fstWriterEmitValueChange(ctx, enable, b"0")

        # State machine changes
        if t == 10:
            lib.fstWriterEmitValueChange(ctx, state, b"01")
        elif t == 30:
            lib.fstWriterEmitValueChange(ctx, state, b"10")
        elif t == 50:
            lib.fstWriterEmitValueChange(ctx, state, b"11")
        elif t == 70:
            lib.fstWriterEmitValueChange(ctx, state, b"00")

        # Counter increments
        if t >= 2 and t % 10 == 0 and t in [10, 30, 50, 70]:
            counter_val = (t // 10) % 256
            lib.fstWriterEmitValueChange(ctx, counter, format(counter_val, '08b').encode('utf-8'))

    # Close writer
    lib.fstWriterClose(ctx)


@pytest.fixture
def test_fst_file(tmp_path):
    """Generate a test FST file for testing."""
    fst_path = tmp_path / "test_waveform.fst"
    create_test_fst_file(str(fst_path))
    return str(fst_path)


@pytest.fixture(autouse=True)
def reset_fst_parser():
    """Reset global _fst_parser before each test."""
    from src import parsers
    parsers._fst_parser = None
    yield
    parsers._fst_parser = None


# Wrapper functions to test the tool functionality
async def load_fst_file(fst_path: str) -> str:
    """Wrapper for load_fst_file tool."""
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


async def get_fst_signals() -> str:
    """Wrapper for get_fst_signals tool."""
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)
    signals, total_count = parser.get_signal_list(limit=0)
    if not signals:
        return "No signals found in FST file."
    lines = [f"Signals in FST file (showing {len(signals)}/{total_count}):"]
    for sig in signals:
        lines.append(
            f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}"
        )
    return "\n".join(lines)


async def get_fst_time_range() -> str:
    """Wrapper for get_fst_time_range tool."""
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)
    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


async def get_fst_signal_values(
    signal_patterns: list[str], start_time: int, end_time: int, format: str = "bin"
) -> str:
    """Wrapper for get_fst_signal_values tool."""
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)
    if start_time > end_time:
        return "Error: start_time must be less than or equal to end_time"
    values, warnings = parser.get_signal_values(signal_patterns, start_time, end_time, format)
    if not values:
        return (
            f"No matching signals found or no values in time range "
            f"[{start_time}, {end_time}] for patterns: {signal_patterns}"
        )
    lines = [f"Signal values in time range [{start_time}, {end_time}]:"]
    if warnings:
        lines.append("\nWarnings:")
        for warning in warnings[:10]:
            lines.append(f"  {warning}")
        if len(warnings) > 10:
            lines.append(f"  ... and {len(warnings) - 10} more warnings")
        lines.append("")
    for signal, changes in values.items():
        lines.append(f"\n{signal}:")
        if not changes:
            lines.append("  (no changes in this range)")
        else:
            for t, v in changes:
                lines.append(f"  {t:>10}: {v}")
    return "\n".join(lines)


@pytest.mark.asyncio
async def test_load_fst_file_success(test_fst_file):
    """Test successfully loading an FST file."""
    result = await load_fst_file(test_fst_file)
    assert "Successfully loaded FST file" in result
    assert "Found 5 signals" in result


@pytest.mark.asyncio
async def test_load_fst_file_not_found():
    """Test loading a non-existent file."""
    result = await load_fst_file("/nonexistent/path/to/file.fst")
    assert "Error: File not found" in result


@pytest.mark.asyncio
async def test_get_fst_signals_success(test_fst_file):
    """Test getting the list of signals after loading an FST file."""
    await load_fst_file(test_fst_file)
    result = await get_fst_signals()

    assert "Signals in FST file" in result
    assert "top.clk" in result
    assert "top.rst" in result
    assert "top.counter" in result
    assert "top.enable" in result
    assert "top.state" in result


@pytest.mark.asyncio
async def test_get_fst_signals_no_file_loaded():
    """Test getting signals when no FST file is loaded."""
    result = await get_fst_signals()
    assert "No FST file loaded" in result


@pytest.mark.asyncio
async def test_get_fst_time_range(test_fst_file):
    """Test getting the time range of a loaded FST file."""
    await load_fst_file(test_fst_file)
    result = await get_fst_time_range()

    assert "Time range:" in result
    assert "to" in result
    assert "total:" in result
    # Time range should end at 990 (99 * 10)
    assert "990" in result


@pytest.mark.asyncio
async def test_get_fst_time_range_no_file_loaded():
    """Test getting time range when no FST file is loaded."""
    result = await get_fst_time_range()
    assert "No FST file loaded" in result


@pytest.mark.asyncio
async def test_get_fst_signal_values(test_fst_file):
    """Test getting signal values within a time range."""
    await load_fst_file(test_fst_file)
    result = await get_fst_signal_values(["clk"], 0, 100)

    assert "Signal values in time range [0, 100]:" in result
    assert "top.clk:" in result


@pytest.mark.asyncio
async def test_get_fst_signal_values_no_file_loaded():
    """Test getting signal values when no FST file is loaded."""
    result = await get_fst_signal_values(["clk"], 0, 100)
    assert "No FST file loaded" in result


@pytest.mark.asyncio
async def test_get_fst_signal_values_invalid_time_range(test_fst_file):
    """Test getting signal values with an invalid time range."""
    await load_fst_file(test_fst_file)
    result = await get_fst_signal_values(["clk"], 100, 0)  # start > end

    assert "Error: start_time must be less than or equal to end_time" in result


@pytest.mark.asyncio
async def test_get_fst_signal_values_pattern_match(test_fst_file):
    """Test signal name pattern matching."""
    await load_fst_file(test_fst_file)

    # Test with pattern that matches multiple signals
    result = await get_fst_signal_values(["top.c"], 0, 100)

    # Should match counter and clk
    assert "Signal values in time range [0, 100]:" in result
    # At least one signal should match
    assert "top." in result


@pytest.mark.asyncio
async def test_get_fst_signal_values_no_matching_signals(test_fst_file):
    """Test with a pattern that matches no signals."""
    await load_fst_file(test_fst_file)
    result = await get_fst_signal_values(["nonexistent_signal"], 0, 100)

    assert "No matching signals found" in result


@pytest.mark.asyncio
async def test_get_fst_signal_values_case_insensitive(test_fst_file):
    """Test that pattern matching is case-insensitive."""
    await load_fst_file(test_fst_file)
    result = await get_fst_signal_values(["CLK"], 0, 100)

    assert "top.clk:" in result


@pytest.mark.asyncio
async def test_get_fst_signal_values_hex_format(test_fst_file):
    """Test getting signal values in hex format."""
    await load_fst_file(test_fst_file)
    result = await get_fst_signal_values(["counter"], 0, 1000, format="hex")

    assert "Signal values in time range [0, 1000]:" in result
    assert "top.counter:" in result
    # Check for hex format (0x prefix)
    assert "0x" in result


@pytest.mark.asyncio
async def test_get_fst_signal_values_dec_format(test_fst_file):
    """Test getting signal values in decimal format."""
    await load_fst_file(test_fst_file)
    result = await get_fst_signal_values(["state"], 0, 1000, format="dec")

    assert "Signal values in time range [0, 1000]:" in result
    assert "top.state:" in result


class TestFstParserClass:
    """Direct tests for the FstParser class."""

    def test_parser_init(self, test_fst_file):
        """Test FstParser initialization."""
        parser = FstParser(test_fst_file)
        assert parser.fst_path == Path(test_fst_file)
        assert parser._fst is not None
        parser.close()

    def test_parser_get_signal_list(self, test_fst_file):
        """Test FstParser.get_signal_list()."""
        parser = FstParser(test_fst_file)
        signals, total_count = parser.get_signal_list(limit=0)

        assert total_count == 5
        assert len(signals) == 5
        paths = [s['path'] for s in signals]
        assert 'top.clk' in paths
        assert 'top.rst' in paths
        assert 'top.counter' in paths
        assert 'top.enable' in paths
        assert 'top.state' in paths

        # Ensure handle is not exposed
        for sig in signals:
            assert 'handle' not in sig

        parser.close()

    def test_parser_get_time_range(self, test_fst_file):
        """Test FstParser.get_time_range()."""
        parser = FstParser(test_fst_file)
        start, end = parser.get_time_range()

        assert start == 0
        assert end == 990
        parser.close()

    def test_parser_get_signal_values(self, test_fst_file):
        """Test FstParser.get_signal_values()."""
        parser = FstParser(test_fst_file)
        values, warnings = parser.get_signal_values(["rst"], 0, 50)

        assert 'top.rst' in values
        # rst should have initial value 1, then change to 0 at t=20
        rst_values = values['top.rst']
        assert len(rst_values) >= 1
        parser.close()

    def test_parser_get_signal_values_hex_format(self, test_fst_file):
        """Test FstParser.get_signal_values() with hex format."""
        parser = FstParser(test_fst_file)
        values, warnings = parser.get_signal_values(["counter"], 0, 1000, fmt="hex")

        assert 'top.counter' in values
        # Check that values have hex format
        for _, v in values['top.counter']:
            assert v.startswith("0x") or v.startswith("b")  # hex or binary fallback
        parser.close()

    def test_parser_close(self, test_fst_file):
        """Test FstParser.close()."""
        parser = FstParser(test_fst_file)
        assert parser._fst is not None
        parser.close()
        assert parser._fst is None
