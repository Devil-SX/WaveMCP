"""MCP server for viewing and parsing VCD and FST waveform files."""

import asyncio
import shutil
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from vcdvcd import VCDVCD
import pylibfst

# Initialize FastMCP server
mcp = FastMCP("wave-viewer")


class WaveformParser:
    """Parser for VCD waveform files using vcdvcd."""

    def __init__(self, vcd_path: str):
        self.vcd_path = Path(vcd_path)
        self.vcd = VCDVCD(str(self.vcd_path))

    def get_signal_list(self) -> list[dict]:
        """Get list of all signals."""
        signals = []
        for sig_name in self.vcd.signals:
            sig_obj = self.vcd[sig_name]
            signals.append({
                'name': sig_name.split('.')[-1],
                'type': sig_obj.var_type,
                'size': sig_obj.size,
                'path': sig_name,
            })
        return signals

    def get_time_range(self) -> tuple[int, int]:
        """Get the total time range of the waveform."""
        return (self.vcd.begintime, self.vcd.endtime)

    def get_signal_values(
        self, signal_patterns: list[str], start_time: int, end_time: int
    ) -> dict[str, list[tuple[int, str]]]:
        """Get signal values within specified time range."""
        result = {}

        # Find matching signals
        for sig_name in self.vcd.signals:
            # Check if signal matches any pattern
            matches = any(
                pattern.lower() in sig_name.lower()
                for pattern in signal_patterns
            )
            if not matches:
                continue

            sig_obj = self.vcd[sig_name]
            values = []
            for t, v in sig_obj.tv:
                if start_time <= t <= end_time:
                    values.append((t, str(v)))
            if values:
                result[sig_name] = values

        return result


class FstParser:
    """Parser for FST waveform files using pylibfst."""

    def __init__(self, fst_path: str):
        self.fst_path = Path(fst_path)
        self._fst = None
        self._signals = None
        self._signals_by_handle = {}
        self._start_time = 0
        self._end_time = 0
        self._load()

    def _load(self):
        """Load and parse FST file."""
        self._fst = pylibfst.lib.fstReaderOpen(str(self.fst_path).encode('utf-8'))
        if self._fst == pylibfst.ffi.NULL:
            raise ValueError(f"Failed to open FST file: {self.fst_path}")

        # Get time range
        self._start_time = pylibfst.lib.fstReaderGetStartTime(self._fst)
        self._end_time = pylibfst.lib.fstReaderGetEndTime(self._fst)

        # Get signals using pylibfst helper
        _scopes, signals_info = pylibfst.get_scopes_signals2(self._fst)

        self._signals = []
        self._signals_by_handle = {}

        for sig_path, sig in signals_info.by_name.items():
            sig_info = {
                'name': sig_path.split('.')[-1],
                'type': 'wire',  # FST doesn't expose var type easily
                'size': sig.length,
                'path': sig_path,
                'handle': sig.handle,
            }
            self._signals.append(sig_info)
            self._signals_by_handle[sig.handle] = sig_path

    def get_signal_list(self) -> list[dict]:
        """Get list of all signals."""
        # Return signals without the internal handle
        return [
            {k: v for k, v in sig.items() if k != 'handle'}
            for sig in self._signals
        ]

    def get_time_range(self) -> tuple[int, int]:
        """Get the total time range of the waveform."""
        return (self._start_time, self._end_time)

    def get_signal_values(
        self, signal_patterns: list[str], start_time: int, end_time: int
    ) -> dict[str, list[tuple[int, str]]]:
        """Get signal values within specified time range."""
        result = {}

        # Find matching signals
        matching_handles = set()
        handle_to_path = {}

        for sig in self._signals:
            sig_path = sig['path']
            matches = any(
                pattern.lower() in sig_path.lower()
                for pattern in signal_patterns
            )
            if matches:
                matching_handles.add(sig['handle'])
                handle_to_path[sig['handle']] = sig_path
                result[sig_path] = []

        if not matching_handles:
            return result

        # Clear and set specific signal masks
        pylibfst.lib.fstReaderClrFacProcessMaskAll(self._fst)
        for handle in matching_handles:
            pylibfst.lib.fstReaderSetFacProcessMask(self._fst, handle)

        # Collect values within time range
        def value_change_callback(_user_data, time, handle, value):
            if handle in matching_handles and start_time <= time <= end_time:
                sig_path = handle_to_path[handle]
                value_str = pylibfst.string(value)
                result[sig_path].append((time, value_str))

        # Read value changes
        pylibfst.fstReaderIterBlocks(self._fst, value_change_callback)

        return result

    def close(self):
        """Close FST file handle."""
        if self._fst is not None and self._fst != pylibfst.ffi.NULL:
            pylibfst.lib.fstReaderClose(self._fst)
            self._fst = None


# Global parser instances
_parser: WaveformParser | None = None
_fst_parser: FstParser | None = None


def get_parser() -> WaveformParser:
    """Get the current VCD parser instance."""
    global _parser
    if _parser is None:
        raise ValueError("No VCD file loaded. Use load_vcd first.")
    return _parser


def get_fst_parser() -> FstParser:
    """Get the current FST parser instance."""
    global _fst_parser
    if _fst_parser is None:
        raise ValueError("No FST file loaded. Use load_fst_file first.")
    return _fst_parser


@mcp.tool()
async def load_vcd_file(vcd_path: str) -> str:
    """Load a VCD format waveform file for analysis (VCD format only).

    Args:
        vcd_path: Path to the VCD file (relative or absolute)
    """
    global _parser
    path = Path(vcd_path)
    if not path.exists():
        return f"Error: File not found: {vcd_path}"

    try:
        _parser = WaveformParser(str(path))
        signal_count = len(_parser.get_signal_list())
        return f"Successfully loaded VCD file: {vcd_path}\nFound {signal_count} signals."
    except Exception as e:
        return f"Error loading VCD file: {e}"


@mcp.tool()
async def get_vcd_signals() -> str:
    """Get list of all signals in the loaded VCD file (VCD format only)."""
    try:
        parser = get_parser()
    except ValueError as e:
        return str(e)

    signals = parser.get_signal_list()
    if not signals:
        return "No signals found in VCD file."

    lines = ["Signals in VCD file:"]
    for sig in signals:
        lines.append(
            f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_vcd_time_range() -> str:
    """Get the total time range of the VCD waveform (VCD format only)."""
    try:
        parser = get_parser()
    except ValueError as e:
        return str(e)

    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


@mcp.tool()
async def get_vcd_signal_values(
    signal_patterns: list[str], start_time: int, end_time: int
) -> str:
    """Get values for specified VCD signals within a time range (VCD format only).

    Args:
        signal_patterns: List of signal name patterns to match
        start_time: Start time (in VCD time units)
        end_time: End time (in VCD time units)
    """
    try:
        parser = get_parser()
    except ValueError as e:
        return str(e)

    if start_time > end_time:
        return "Error: start_time must be less than or equal to end_time"

    values = parser.get_signal_values(signal_patterns, start_time, end_time)

    if not values:
        return (
            f"No matching signals found or no values in time range "
            f"[{start_time}, {end_time}] for patterns: {signal_patterns}"
        )

    lines = [f"Signal values in time range [{start_time}, {end_time}]:"]
    for signal, changes in values.items():
        lines.append(f"\n{signal}:")
        if not changes:
            lines.append("  (no changes in this range)")
        else:
            for t, v in changes:
                lines.append(f"  {t:>10}: {v}")

    return "\n".join(lines)


@mcp.tool()
async def load_fst_file(fst_path: str) -> str:
    """Load an FST format waveform file for analysis (FST format only).

    Args:
        fst_path: Path to the FST file (relative or absolute)
    """
    global _fst_parser
    path = Path(fst_path)
    if not path.exists():
        return f"Error: File not found: {fst_path}"

    try:
        _fst_parser = FstParser(str(path))
        signal_count = len(_fst_parser.get_signal_list())
        return f"Successfully loaded FST file: {fst_path}\nFound {signal_count} signals."
    except Exception as e:
        return f"Error loading FST file: {e}"


@mcp.tool()
async def get_fst_signals() -> str:
    """Get list of all signals in the loaded FST file (FST format only)."""
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)

    signals = parser.get_signal_list()
    if not signals:
        return "No signals found in FST file."

    lines = ["Signals in FST file:"]
    for sig in signals:
        lines.append(
            f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_fst_time_range() -> str:
    """Get the total time range of the FST waveform (FST format only)."""
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)

    start, end = parser.get_time_range()
    return f"Time range: {start} to {end} (total: {end - start} time units)"


@mcp.tool()
async def get_fst_signal_values(
    signal_patterns: list[str], start_time: int, end_time: int
) -> str:
    """Get values for specified FST signals within a time range (FST format only).

    Args:
        signal_patterns: List of signal name patterns to match
        start_time: Start time (in FST time units)
        end_time: End time (in FST time units)
    """
    try:
        parser = get_fst_parser()
    except ValueError as e:
        return str(e)

    if start_time > end_time:
        return "Error: start_time must be less than or equal to end_time"

    values = parser.get_signal_values(signal_patterns, start_time, end_time)

    if not values:
        return (
            f"No matching signals found or no values in time range "
            f"[{start_time}, {end_time}] for patterns: {signal_patterns}"
        )

    lines = [f"Signal values in time range [{start_time}, {end_time}]:"]
    for signal, changes in values.items():
        lines.append(f"\n{signal}:")
        if not changes:
            lines.append("  (no changes in this range)")
        else:
            for t, v in changes:
                lines.append(f"  {t:>10}: {v}")

    return "\n".join(lines)


def _check_simvisdbutil() -> str | None:
    """Check if simvisdbutil tool is available in PATH."""
    return shutil.which("simvisdbutil")


@mcp.tool()
async def convert_cadence_to_vcd(
    input_file: str, output_file: str = ""
) -> str:
    """Convert Cadence waveform file (SST2/PWLF) to VCD format using simvisdbutil.

    Args:
        input_file: Path to the input Cadence waveform file
        output_file: Optional path to the output VCD file.
                     If not specified, output will be in the same directory
                     as input_file with .vcd extension.

    Returns:
        Success message with absolute paths of input and output files,
        or error message if conversion fails.
    """
    # Check if simvisdbutil is available
    simvis_path = _check_simvisdbutil()
    if simvis_path is None:
        return "Error: simvisdbutil tool not found in PATH. Please ensure Cadence tools are installed and accessible."

    # Validate input file
    input_path = Path(input_file)
    if not input_path.exists():
        return f"Error: Input file not found: {input_file}"

    # Determine output file path
    if output_file:
        output_path = Path(output_file)
    else:
        # Default: same directory as input, with .vcd extension
        output_path = input_path.with_suffix(".vcd")

    # Build command
    cmd = [
        "simvisdbutil",
        str(input_path.absolute()),
        "-VCD",
        "-OUTPUT", str(output_path.absolute()),
        "-OVERWRITE",
        "-NOCOPYRIGHT",
    ]

    # Run conversion
    try:
        result = await asyncio.to_thread(shutil.run, cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return f"Error: simvisdbutil failed with exit code {result.returncode}\n{result.stderr}"

        # Verify output file was created
        if not output_path.exists():
            return f"Error: Output file was not created. simvisdbutil output:\n{result.stdout}"

        return (
            f"Successfully converted Cadence waveform to VCD format.\n"
            f"Input file:  {input_path.absolute()}\n"
            f"Output file: {output_path.absolute()}"
        )
    except FileNotFoundError:
        return "Error: simvisdbutil executable not found. Please check Cadence installation."
    except Exception as e:
        return f"Error during conversion: {e}"


def main():
    """Initialize and run the server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
