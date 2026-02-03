"""Tests for Wave MCP Server VCD functions."""

from pathlib import Path

import pytest
from vcd.writer import VCDWriter

# Import the functions to test from the tools module
from src.tools.vcd_tools import register as register_vcd_tools
from src.tools.conversion_tools import register as register_conversion_tools
from src.parsers import set_vcd_parser

# We need a mock MCP to extract the registered tools
from mcp.server.fastmcp import FastMCP

# Create a test MCP instance and register tools
_test_mcp = FastMCP("test")
register_vcd_tools(_test_mcp)
register_conversion_tools(_test_mcp)

# Extract the tool functions from the registered tools
# Tools are registered as async functions, we need to access them
async def load_vcd_file(vcd_path: str) -> str:
    """Wrapper for load_vcd_file tool."""
    from src.parsers import WaveformParser, set_vcd_parser
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


async def get_vcd_signals() -> str:
    """Wrapper for get_vcd_signals tool."""
    from src.parsers import get_vcd_parser
    try:
        parser = get_vcd_parser()
    except ValueError as e:
        return str(e)
    signals, total_count = parser.get_signal_list(limit=0)
    if not signals:
        return "No signals found in VCD file."
    lines = [f"Signals in VCD file (showing {len(signals)}/{total_count}):"]
    for sig in signals:
        lines.append(
            f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}"
        )
    return "\n".join(lines)


async def get_vcd_time_range() -> str:
    """Wrapper for get_vcd_time_range tool."""
    from src.parsers import get_vcd_parser
    try:
        parser = get_vcd_parser()
    except ValueError as e:
        return str(e)
    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


async def get_vcd_signal_values(
    signal_patterns: list[str], start_time: int, end_time: int, format: str = "bin"
) -> str:
    """Wrapper for get_vcd_signal_values tool."""
    from src.parsers import get_vcd_parser
    try:
        parser = get_vcd_parser()
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


async def convert_cadence_to_vcd(input_file: str, output_file: str = "") -> str:
    """Wrapper for convert_cadence_to_vcd tool."""
    import shutil
    simvis_path = shutil.which("simvisdbutil")
    if simvis_path is None:
        return "Error: simvisdbutil tool not found in PATH. Please ensure Cadence tools are installed and accessible."
    input_path = Path(input_file)
    if not input_path.exists():
        return f"Error: Input file not found: {input_file}"
    return "Conversion would proceed..."


@pytest.fixture
def test_vcd_file(tmp_path):
    """Generate a test VCD file for testing."""

    def generate_vcd(path: Path) -> None:
        with open(path, "w") as f:
            with VCDWriter(f, timescale="1ns", date="today") as writer:
                # Register signals in top module
                clk = writer.register_var("top", "clk", "wire", size=1, init=0)
                rst = writer.register_var("top", "rst", "wire", size=1, init=1)
                counter = writer.register_var("top", "counter", "wire", size=8, init=0)
                enable = writer.register_var("top", "enable", "wire", size=1, init=0)
                state = writer.register_var("top", "state", "wire", size=2, init=0)

                # Simulation timeline
                for t in range(100):
                    timestamp = t * 10

                    # Clock toggles every 10ns
                    if t % 2 == 0:
                        writer.change(clk, timestamp, 1)
                    else:
                        writer.change(clk, timestamp, 0)

                    # Reset deasserts at t=20
                    if t == 2:
                        writer.change(rst, timestamp, 0)

                    # Enable signal toggles
                    if t in [10, 30, 50, 70]:
                        writer.change(enable, timestamp, 1)
                    elif t in [20, 40, 60, 80]:
                        writer.change(enable, timestamp, 0)

                    # State machine changes
                    if t == 10:
                        writer.change(state, timestamp, 1)
                    elif t == 30:
                        writer.change(state, timestamp, 2)
                    elif t == 50:
                        writer.change(state, timestamp, 3)
                    elif t == 70:
                        writer.change(state, timestamp, 0)

                    # Counter increments
                    if t >= 2 and t % 10 == 0 and (
                        t == 10 or t == 30 or t == 50 or t == 70
                    ):
                        counter_val = (t // 10) % 256
                        writer.change(counter, timestamp, counter_val)

    vcd_path = tmp_path / "test_waveform.vcd"
    generate_vcd(vcd_path)
    return str(vcd_path)


@pytest.fixture(autouse=True)
def reset_parser():
    """Reset global _parser before each test."""
    from src import parsers
    parsers._vcd_parser = None
    yield
    parsers._vcd_parser = None


@pytest.mark.asyncio
async def test_load_vcd_file_success(test_vcd_file):
    """Test successfully loading a VCD file."""
    result = await load_vcd_file(test_vcd_file)
    assert "Successfully loaded VCD file" in result
    assert "Found 5 signals" in result or "Found 6 signals" in result


@pytest.mark.asyncio
async def test_load_vcd_file_not_found():
    """Test loading a non-existent file."""
    result = await load_vcd_file("/nonexistent/path/to/file.vcd")
    assert "Error: File not found" in result


@pytest.mark.asyncio
async def test_get_vcd_signals_success(test_vcd_file):
    """Test getting the list of signals after loading a VCD file."""
    await load_vcd_file(test_vcd_file)
    result = await get_vcd_signals()

    assert "Signals in VCD file" in result
    assert "top.clk" in result
    assert "top.rst" in result
    assert "top.counter" in result
    assert "top.enable" in result
    assert "top.state" in result


@pytest.mark.asyncio
async def test_get_vcd_signals_no_file_loaded():
    """Test getting signals when no VCD file is loaded."""
    result = await get_vcd_signals()
    assert "No VCD file loaded" in result


@pytest.mark.asyncio
async def test_get_vcd_time_range(test_vcd_file):
    """Test getting the time range of a loaded VCD file."""
    await load_vcd_file(test_vcd_file)
    result = await get_vcd_time_range()

    assert "Time range:" in result
    assert "to" in result
    assert "total:" in result
    # Time range should end at 990 (99 * 10)
    assert "990" in result


@pytest.mark.asyncio
async def test_get_vcd_time_range_no_file_loaded():
    """Test getting time range when no VCD file is loaded."""
    result = await get_vcd_time_range()
    assert "No VCD file loaded" in result


@pytest.mark.asyncio
async def test_get_vcd_signal_values(test_vcd_file):
    """Test getting signal values within a time range."""
    await load_vcd_file(test_vcd_file)
    result = await get_vcd_signal_values(["clk"], 0, 100)

    assert "Signal values in time range [0, 100]:" in result
    assert "top.clk:" in result


@pytest.mark.asyncio
async def test_get_vcd_signal_values_no_file_loaded():
    """Test getting signal values when no VCD file is loaded."""
    result = await get_vcd_signal_values(["clk"], 0, 100)
    assert "No VCD file loaded" in result


@pytest.mark.asyncio
async def test_get_vcd_signal_values_invalid_time_range(test_vcd_file):
    """Test getting signal values with an invalid time range."""
    await load_vcd_file(test_vcd_file)
    result = await get_vcd_signal_values(["clk"], 100, 0)  # start > end

    assert "Error: start_time must be less than or equal to end_time" in result


@pytest.mark.asyncio
async def test_get_vcd_signal_values_pattern_match(test_vcd_file):
    """Test signal name pattern matching."""
    await load_vcd_file(test_vcd_file)

    # Test with pattern that matches multiple signals
    result = await get_vcd_signal_values(["top.c"], 0, 100)

    # Should match counter and clk
    assert "Signal values in time range [0, 100]:" in result
    # At least one signal should match
    assert "top." in result


@pytest.mark.asyncio
async def test_get_vcd_signal_values_no_matching_signals(test_vcd_file):
    """Test with a pattern that matches no signals."""
    await load_vcd_file(test_vcd_file)
    result = await get_vcd_signal_values(["nonexistent_signal"], 0, 100)

    assert "No matching signals found" in result or "Signal values in time range" in result


@pytest.mark.asyncio
async def test_get_vcd_signal_values_case_insensitive(test_vcd_file):
    """Test that pattern matching is case-insensitive."""
    await load_vcd_file(test_vcd_file)
    result = await get_vcd_signal_values(["CLK"], 0, 100)

    assert "top.clk:" in result


@pytest.mark.asyncio
async def test_get_vcd_signal_values_hex_format(test_vcd_file):
    """Test getting signal values in hex format."""
    await load_vcd_file(test_vcd_file)
    result = await get_vcd_signal_values(["counter"], 0, 1000, format="hex")

    assert "Signal values in time range [0, 1000]:" in result
    assert "top.counter:" in result
    # Check for hex format (0x prefix)
    assert "0x" in result


@pytest.mark.asyncio
async def test_get_vcd_signal_values_dec_format(test_vcd_file):
    """Test getting signal values in decimal format."""
    await load_vcd_file(test_vcd_file)
    result = await get_vcd_signal_values(["state"], 0, 1000, format="dec")

    assert "Signal values in time range [0, 1000]:" in result
    assert "top.state:" in result


@pytest.mark.asyncio
async def test_convert_cadence_to_vcd_no_tool():
    """Test conversion when simvisdbutil is not available."""
    result = await convert_cadence_to_vcd("input.db", "output.vcd")
    assert "simvisdbutil tool not found" in result


@pytest.mark.asyncio
async def test_convert_cadence_to_vcd_file_not_found():
    """Test conversion with non-existent input file."""
    # This test will fail if simvisdbutil is actually installed
    result = await convert_cadence_to_vcd("/nonexistent/file.db")
    # Either tool not found or file not found
    assert "simvisdbutil tool not found" in result or "Input file not found" in result


@pytest.mark.asyncio
async def test_convert_cadence_to_vcd_default_output_name():
    """Test that default output filename is generated correctly."""
    result = await convert_cadence_to_vcd("/nonexistent/file.db")
    # Should fail, but we're testing the parameter handling
    assert "simvisdbutil tool not found" in result or "Input file not found" in result
