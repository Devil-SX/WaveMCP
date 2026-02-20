"""Tests for unified waveform MCP tools (pywellen backend)."""

from pathlib import Path

import pytest
from vcd.writer import VCDWriter

from src.parsers import WellenParser, set_wellen_parser
from src.parsers import get_wellen_parser


def generate_test_vcd(path: Path) -> None:
    """Generate a test VCD file with 5 signals."""
    with open(path, "w") as f:
        with VCDWriter(f, timescale="1ns", date="today") as writer:
            clk = writer.register_var("top", "clk", "wire", size=1, init=0)
            rst = writer.register_var("top", "rst", "wire", size=1, init=1)
            counter = writer.register_var("top", "counter", "wire", size=8, init=0)
            enable = writer.register_var("top", "enable", "wire", size=1, init=0)
            state = writer.register_var("top", "state", "wire", size=2, init=0)

            for t in range(100):
                timestamp = t * 10

                if t % 2 == 0:
                    writer.change(clk, timestamp, 1)
                else:
                    writer.change(clk, timestamp, 0)

                if t == 2:
                    writer.change(rst, timestamp, 0)

                if t in [10, 30, 50, 70]:
                    writer.change(enable, timestamp, 1)
                elif t in [20, 40, 60, 80]:
                    writer.change(enable, timestamp, 0)

                if t == 10:
                    writer.change(state, timestamp, 1)
                elif t == 30:
                    writer.change(state, timestamp, 2)
                elif t == 50:
                    writer.change(state, timestamp, 3)
                elif t == 70:
                    writer.change(state, timestamp, 0)

                if t >= 2 and t % 10 == 0 and t in [10, 30, 50, 70]:
                    counter_val = (t // 10) % 256
                    writer.change(counter, timestamp, counter_val)


def create_test_fst_file(fst_path: str) -> None:
    """Create a test FST file with 5 signals."""
    import pylibfst
    from pylibfst import lib, ffi

    ctx = lib.fstWriterCreate(fst_path.encode('utf-8'), 1)
    if ctx == ffi.NULL:
        raise RuntimeError("Failed to create FST writer")

    lib.fstWriterSetTimescale(ctx, -9)
    lib.fstWriterSetScope(ctx, lib.FST_ST_VCD_MODULE, b"top", ffi.NULL)

    clk = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 1, b"clk", 0)
    rst = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 1, b"rst", 0)
    counter = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 8, b"counter", 0)
    enable = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 1, b"enable", 0)
    state = lib.fstWriterCreateVar(ctx, lib.FST_VT_VCD_WIRE, lib.FST_VD_IMPLICIT, 2, b"state", 0)

    lib.fstWriterSetUpscope(ctx)

    lib.fstWriterEmitTimeChange(ctx, 0)
    lib.fstWriterEmitValueChange(ctx, clk, b"0")
    lib.fstWriterEmitValueChange(ctx, rst, b"1")
    lib.fstWriterEmitValueChange(ctx, counter, b"00000000")
    lib.fstWriterEmitValueChange(ctx, enable, b"0")
    lib.fstWriterEmitValueChange(ctx, state, b"00")

    for t in range(1, 100):
        timestamp = t * 10
        lib.fstWriterEmitTimeChange(ctx, timestamp)

        if t % 2 == 0:
            lib.fstWriterEmitValueChange(ctx, clk, b"1")
        else:
            lib.fstWriterEmitValueChange(ctx, clk, b"0")

        if t == 2:
            lib.fstWriterEmitValueChange(ctx, rst, b"0")

        if t in [10, 30, 50, 70]:
            lib.fstWriterEmitValueChange(ctx, enable, b"1")
        elif t in [20, 40, 60, 80]:
            lib.fstWriterEmitValueChange(ctx, enable, b"0")

        if t == 10:
            lib.fstWriterEmitValueChange(ctx, state, b"01")
        elif t == 30:
            lib.fstWriterEmitValueChange(ctx, state, b"10")
        elif t == 50:
            lib.fstWriterEmitValueChange(ctx, state, b"11")
        elif t == 70:
            lib.fstWriterEmitValueChange(ctx, state, b"00")

        if t >= 2 and t % 10 == 0 and t in [10, 30, 50, 70]:
            counter_val = (t // 10) % 256
            lib.fstWriterEmitValueChange(ctx, counter, format(counter_val, '08b').encode('utf-8'))

    lib.fstWriterClose(ctx)


# --- Wrapper functions mirroring tool behavior ---

async def load_waveform(path: str) -> str:
    """Wrapper for load_waveform tool."""
    filepath = Path(path)
    if not filepath.exists():
        return f"Error: File not found: {path}"
    try:
        parser = WellenParser(str(filepath))
        set_wellen_parser(parser)
        _, signal_count = parser.get_signal_list(limit=0)
        return f"Successfully loaded waveform file: {path}\nFound {signal_count} signals."
    except Exception as e:
        return f"Error loading waveform file: {e}"


async def get_signals(module_path: str = "", pattern: str = "") -> str:
    """Wrapper for get_signals tool."""
    try:
        parser = get_wellen_parser()
    except ValueError as e:
        return str(e)
    signals, total_count = parser.get_signal_list(module_path=module_path, pattern=pattern, limit=0)
    if not signals:
        return "No signals found in waveform file."
    lines = [f"Signals in waveform file (showing {len(signals)}/{total_count}):"]
    for sig in signals:
        lines.append(
            f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}"
        )
    return "\n".join(lines)


async def get_time_range() -> str:
    """Wrapper for get_time_range tool."""
    try:
        parser = get_wellen_parser()
    except ValueError as e:
        return str(e)
    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


async def get_signal_values(
    signal_names: list[str], start_time: int, end_time: int, format: str = "bin"
) -> str:
    """Wrapper for get_signal_values tool."""
    try:
        parser = get_wellen_parser()
    except ValueError as e:
        return str(e)
    if start_time > end_time:
        return "Error: start_time must be less than or equal to end_time"
    values, warnings = parser.get_signal_values(signal_names, start_time, end_time, format)
    if not values:
        return (
            f"No matching signals found or no values in time range "
            f"[{start_time}, {end_time}] for signal names: {signal_names}"
        )
    lines = [f"Signal values in time range [{start_time}, {end_time}]:"]
    if warnings:
        lines.append("\nWarnings:")
        for warning in warnings[:10]:
            lines.append(f"  {warning}")
        lines.append("")
    for signal, changes in values.items():
        lines.append(f"\n{signal}:")
        if not changes:
            lines.append("  (no changes in this range)")
        else:
            for t, v in changes:
                lines.append(f"  {t:>10}: {v}")
    return "\n".join(lines)


# --- Fixtures ---

@pytest.fixture
def test_vcd_file(tmp_path):
    """Generate a test VCD file."""
    vcd_path = tmp_path / "test_waveform.vcd"
    generate_test_vcd(vcd_path)
    return str(vcd_path)


@pytest.fixture
def test_fst_file(tmp_path):
    """Generate a test FST file."""
    fst_path = tmp_path / "test_waveform.fst"
    create_test_fst_file(str(fst_path))
    return str(fst_path)


@pytest.fixture(autouse=True)
def reset_parser():
    """Reset global parser before each test."""
    from src import parsers
    parsers._wellen_parser = None
    yield
    parsers._wellen_parser = None


# --- VCD Tests ---

class TestVCDWaveform:
    """Test unified tools with VCD files."""

    @pytest.mark.asyncio
    async def test_load_success(self, test_vcd_file):
        result = await load_waveform(test_vcd_file)
        assert "Successfully loaded waveform file" in result
        assert "Found 5 signals" in result

    @pytest.mark.asyncio
    async def test_load_not_found(self):
        result = await load_waveform("/nonexistent/path.vcd")
        assert "Error: File not found" in result

    @pytest.mark.asyncio
    async def test_get_signals(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_signals()
        assert "Signals in waveform file" in result
        assert "top.clk" in result
        assert "top.rst" in result
        assert "top.counter" in result
        assert "top.enable" in result
        assert "top.state" in result

    @pytest.mark.asyncio
    async def test_get_signals_no_file(self):
        result = await get_signals()
        assert "No waveform file loaded" in result

    @pytest.mark.asyncio
    async def test_get_time_range(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_time_range()
        assert "Time range:" in result
        assert "990" in result

    @pytest.mark.asyncio
    async def test_get_time_range_no_file(self):
        result = await get_time_range()
        assert "No waveform file loaded" in result

    @pytest.mark.asyncio
    async def test_get_signal_values(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_signal_values(["clk"], 0, 100)
        assert "Signal values in time range [0, 100]:" in result
        assert "top.clk:" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_no_file(self):
        result = await get_signal_values(["clk"], 0, 100)
        assert "No waveform file loaded" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_invalid_range(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_signal_values(["clk"], 100, 0)
        assert "Error: start_time must be less than or equal to end_time" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_pattern_match(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_signal_values(["top.c"], 0, 100)
        assert "Signal values in time range [0, 100]:" in result
        assert "top." in result

    @pytest.mark.asyncio
    async def test_get_signal_values_no_match(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_signal_values(["nonexistent"], 0, 100)
        assert "No matching signals found" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_case_insensitive(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_signal_values(["CLK"], 0, 100)
        assert "top.clk:" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_hex(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_signal_values(["counter"], 0, 1000, format="hex")
        assert "top.counter:" in result
        assert "0x" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_dec(self, test_vcd_file):
        await load_waveform(test_vcd_file)
        result = await get_signal_values(["state"], 0, 1000, format="dec")
        assert "top.state:" in result


# --- FST Tests ---

class TestFSTWaveform:
    """Test unified tools with FST files."""

    @pytest.mark.asyncio
    async def test_load_success(self, test_fst_file):
        result = await load_waveform(test_fst_file)
        assert "Successfully loaded waveform file" in result
        assert "Found 5 signals" in result

    @pytest.mark.asyncio
    async def test_get_signals(self, test_fst_file):
        await load_waveform(test_fst_file)
        result = await get_signals()
        assert "Signals in waveform file" in result
        assert "top.clk" in result
        assert "top.rst" in result
        assert "top.counter" in result
        assert "top.enable" in result
        assert "top.state" in result

    @pytest.mark.asyncio
    async def test_get_time_range(self, test_fst_file):
        await load_waveform(test_fst_file)
        result = await get_time_range()
        assert "Time range:" in result
        assert "990" in result

    @pytest.mark.asyncio
    async def test_get_signal_values(self, test_fst_file):
        await load_waveform(test_fst_file)
        result = await get_signal_values(["clk"], 0, 100)
        assert "Signal values in time range [0, 100]:" in result
        assert "top.clk:" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_case_insensitive(self, test_fst_file):
        await load_waveform(test_fst_file)
        result = await get_signal_values(["CLK"], 0, 100)
        assert "top.clk:" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_hex(self, test_fst_file):
        await load_waveform(test_fst_file)
        result = await get_signal_values(["counter"], 0, 1000, format="hex")
        assert "top.counter:" in result
        assert "0x" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_dec(self, test_fst_file):
        await load_waveform(test_fst_file)
        result = await get_signal_values(["state"], 0, 1000, format="dec")
        assert "top.state:" in result

    @pytest.mark.asyncio
    async def test_get_signal_values_no_match(self, test_fst_file):
        await load_waveform(test_fst_file)
        result = await get_signal_values(["nonexistent"], 0, 100)
        assert "No matching signals found" in result
