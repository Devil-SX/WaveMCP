"""Differential tests: compare old parsers (vcdvcd/pylibfst) with new WellenParser."""

from pathlib import Path

import pytest
from vcd.writer import VCDWriter

from src.parsers import WaveformParser, FstParser, WellenParser


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
    """Create a test FST file with the same 5 signals."""
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


@pytest.fixture
def test_vcd_file(tmp_path):
    """Generate a test VCD file."""
    vcd_path = tmp_path / "test.vcd"
    generate_test_vcd(vcd_path)
    return str(vcd_path)


@pytest.fixture
def test_fst_file(tmp_path):
    """Generate a test FST file."""
    fst_path = tmp_path / "test.fst"
    create_test_fst_file(str(fst_path))
    return str(fst_path)


class TestDifferentialVCD:
    """Compare WaveformParser (vcdvcd) vs WellenParser on VCD files."""

    def test_signal_list_paths(self, test_vcd_file):
        """Signal paths should match between old and new parser."""
        old = WaveformParser(test_vcd_file)
        new = WellenParser(test_vcd_file)

        old_sigs, old_count = old.get_signal_list(limit=0)
        new_sigs, new_count = new.get_signal_list(limit=0)

        assert old_count == new_count

        old_paths = sorted(s['path'] for s in old_sigs)
        new_paths = sorted(s['path'] for s in new_sigs)
        assert old_paths == new_paths

    def test_signal_list_sizes(self, test_vcd_file):
        """Signal sizes should match."""
        old = WaveformParser(test_vcd_file)
        new = WellenParser(test_vcd_file)

        old_sigs, _ = old.get_signal_list(limit=0)
        new_sigs, _ = new.get_signal_list(limit=0)

        old_by_path = {s['path']: s for s in old_sigs}
        new_by_path = {s['path']: s for s in new_sigs}

        for path in old_by_path:
            # vcdvcd returns size as str, pywellen as int
            assert int(old_by_path[path]['size']) == int(new_by_path[path]['size']), (
                f"Size mismatch for {path}: old={old_by_path[path]['size']}, new={new_by_path[path]['size']}"
            )

    def test_time_range(self, test_vcd_file):
        """Time range should match exactly."""
        old = WaveformParser(test_vcd_file)
        new = WellenParser(test_vcd_file)

        assert old.get_time_range() == new.get_time_range()

    def test_signal_values_dec(self, test_vcd_file):
        """Signal values in dec format should match (avoids leading zero differences)."""
        old = WaveformParser(test_vcd_file)
        new = WellenParser(test_vcd_file)

        old_sigs, _ = old.get_signal_list(limit=0)
        start, end = old.get_time_range()

        for sig in old_sigs:
            path = sig['path']
            old_vals, _ = old.get_signal_values([path], start, end, fmt="dec")
            new_vals, _ = new.get_signal_values([path], start, end, fmt="dec")

            old_changes = old_vals.get(path, [])
            new_changes = new_vals.get(path, [])

            assert old_changes == new_changes, (
                f"Value mismatch for {path}:\n"
                f"  old ({len(old_changes)} changes): {old_changes[:5]}...\n"
                f"  new ({len(new_changes)} changes): {new_changes[:5]}..."
            )

    def test_signal_list_with_module_path(self, test_vcd_file):
        """Filtering by module_path should produce same results."""
        old = WaveformParser(test_vcd_file)
        new = WellenParser(test_vcd_file)

        old_sigs, old_count = old.get_signal_list(module_path="top", limit=0)
        new_sigs, new_count = new.get_signal_list(module_path="top", limit=0)

        assert old_count == new_count
        old_paths = sorted(s['path'] for s in old_sigs)
        new_paths = sorted(s['path'] for s in new_sigs)
        assert old_paths == new_paths

    def test_signal_list_with_max_depth(self, test_vcd_file):
        """Filtering by max_depth should produce same results."""
        old = WaveformParser(test_vcd_file)
        new = WellenParser(test_vcd_file)

        old_sigs, old_count = old.get_signal_list(max_depth=1, limit=0)
        new_sigs, new_count = new.get_signal_list(max_depth=1, limit=0)

        assert old_count == new_count

    def test_signal_list_with_pattern(self, test_vcd_file):
        """Filtering by pattern should produce same results."""
        old = WaveformParser(test_vcd_file)
        new = WellenParser(test_vcd_file)

        old_sigs, old_count = old.get_signal_list(pattern="clk", limit=0)
        new_sigs, new_count = new.get_signal_list(pattern="clk", limit=0)

        assert old_count == new_count
        old_paths = sorted(s['path'] for s in old_sigs)
        new_paths = sorted(s['path'] for s in new_sigs)
        assert old_paths == new_paths

    def test_signal_list_with_regex(self, test_vcd_file):
        """Filtering by regex should produce same results."""
        old = WaveformParser(test_vcd_file)
        new = WellenParser(test_vcd_file)

        old_sigs, old_count = old.get_signal_list(pattern="(clk|rst)", use_regex=True, limit=0)
        new_sigs, new_count = new.get_signal_list(pattern="(clk|rst)", use_regex=True, limit=0)

        assert old_count == new_count
        old_paths = sorted(s['path'] for s in old_sigs)
        new_paths = sorted(s['path'] for s in new_sigs)
        assert old_paths == new_paths


class TestDifferentialFST:
    """Compare FstParser (pylibfst) vs WellenParser on FST files."""

    def test_signal_list_paths(self, test_fst_file):
        """Signal paths should match between old and new parser."""
        old = FstParser(test_fst_file)
        new = WellenParser(test_fst_file)

        old_sigs, old_count = old.get_signal_list(limit=0)
        new_sigs, new_count = new.get_signal_list(limit=0)

        assert old_count == new_count

        old_paths = sorted(s['path'] for s in old_sigs)
        new_paths = sorted(s['path'] for s in new_sigs)
        assert old_paths == new_paths

        old.close()

    def test_signal_list_sizes(self, test_fst_file):
        """Signal sizes should match."""
        old = FstParser(test_fst_file)
        new = WellenParser(test_fst_file)

        old_sigs, _ = old.get_signal_list(limit=0)
        new_sigs, _ = new.get_signal_list(limit=0)

        old_by_path = {s['path']: s for s in old_sigs}
        new_by_path = {s['path']: s for s in new_sigs}

        for path in old_by_path:
            assert old_by_path[path]['size'] == new_by_path[path]['size']

        old.close()

    def test_time_range(self, test_fst_file):
        """Time range should match exactly."""
        old = FstParser(test_fst_file)
        new = WellenParser(test_fst_file)

        assert old.get_time_range() == new.get_time_range()
        old.close()

    def test_signal_values_dec(self, test_fst_file):
        """Signal values in dec format should match.

        Note: pylibfst reports a value at every iterated timestep (including
        repeated/unchanged values), while pywellen only reports actual changes.
        We compare by deduplicating consecutive identical values.
        """
        old = FstParser(test_fst_file)
        new = WellenParser(test_fst_file)

        old_sigs, _ = old.get_signal_list(limit=0)
        start, end = old.get_time_range()

        def deduplicate(changes):
            """Remove consecutive duplicate values, keeping only actual changes."""
            result = []
            last_val = None
            for t, v in changes:
                if v != last_val:
                    result.append((t, v))
                    last_val = v
            return result

        for sig in old_sigs:
            path = sig['path']
            old_vals, _ = old.get_signal_values([path], start, end, fmt="dec")
            new_vals, _ = new.get_signal_values([path], start, end, fmt="dec")

            old_changes = deduplicate(old_vals.get(path, []))
            new_changes = deduplicate(new_vals.get(path, []))

            assert old_changes == new_changes, (
                f"Value mismatch for {path}:\n"
                f"  old ({len(old_changes)} changes): {old_changes[:5]}...\n"
                f"  new ({len(new_changes)} changes): {new_changes[:5]}..."
            )

        old.close()

    def test_signal_list_with_module_path(self, test_fst_file):
        """Filtering by module_path should produce same results."""
        old = FstParser(test_fst_file)
        new = WellenParser(test_fst_file)

        old_sigs, old_count = old.get_signal_list(module_path="top", limit=0)
        new_sigs, new_count = new.get_signal_list(module_path="top", limit=0)

        assert old_count == new_count
        old_paths = sorted(s['path'] for s in old_sigs)
        new_paths = sorted(s['path'] for s in new_sigs)
        assert old_paths == new_paths

        old.close()

    def test_signal_list_with_pattern(self, test_fst_file):
        """Filtering by pattern should produce same results."""
        old = FstParser(test_fst_file)
        new = WellenParser(test_fst_file)

        old_sigs, old_count = old.get_signal_list(pattern="counter", limit=0)
        new_sigs, new_count = new.get_signal_list(pattern="counter", limit=0)

        assert old_count == new_count
        old_paths = sorted(s['path'] for s in old_sigs)
        new_paths = sorted(s['path'] for s in new_sigs)
        assert old_paths == new_paths

        old.close()

    def test_signal_list_with_regex(self, test_fst_file):
        """Filtering by regex should produce same results."""
        old = FstParser(test_fst_file)
        new = WellenParser(test_fst_file)

        old_sigs, old_count = old.get_signal_list(pattern="(enable|state)", use_regex=True, limit=0)
        new_sigs, new_count = new.get_signal_list(pattern="(enable|state)", use_regex=True, limit=0)

        assert old_count == new_count
        old_paths = sorted(s['path'] for s in old_sigs)
        new_paths = sorted(s['path'] for s in new_sigs)
        assert old_paths == new_paths

        old.close()
