"""MCP server for viewing and parsing VCD waveform files."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from vcdvcd import VCDVCD

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


# Global parser instance (will be set when loading a VCD file)
_parser: WaveformParser | None = None


def get_parser() -> WaveformParser:
    """Get the current parser instance."""
    global _parser
    if _parser is None:
        raise ValueError("No VCD file loaded. Use load_vcd first.")
    return _parser


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


def main():
    """Initialize and run the server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
