"""VCD waveform MCP tools."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..parsers import WaveformParser, get_vcd_parser, set_vcd_parser


def register(mcp: FastMCP):
    """Register VCD tools with the MCP server."""

    @mcp.tool()
    async def load_vcd_file(vcd_path: str) -> str:
        """Load a VCD format waveform file for analysis (VCD format only).

        Args:
            vcd_path: Path to the VCD file (relative or absolute)
        """
        path = Path(vcd_path)
        if not path.exists():
            return f"Error: File not found: {vcd_path}"

        try:
            parser = WaveformParser(str(path))
            set_vcd_parser(parser)
            signal_count = len(parser.get_signal_list())
            return f"Successfully loaded VCD file: {vcd_path}\nFound {signal_count} signals."
        except Exception as e:
            return f"Error loading VCD file: {e}"

    @mcp.tool()
    async def get_vcd_signals() -> str:
        """Get list of all signals in the loaded VCD file (VCD format only)."""
        try:
            parser = get_vcd_parser()
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
            parser = get_vcd_parser()
        except ValueError as e:
            return str(e)

        start, end = parser.get_time_range()
        return f"Time range: {start} to {end} (total: {end - start} time units)"

    @mcp.tool()
    async def get_vcd_signal_values(
        signal_patterns: list[str],
        start_time: int,
        end_time: int,
        format: str = "bin",
    ) -> str:
        """Get values for specified VCD signals within a time range (VCD format only).

        Args:
            signal_patterns: List of signal name patterns to match
            start_time: Start time (in VCD time units)
            end_time: End time (in VCD time units)
            format: Output format - "bin" (default, prefix b), "hex" (prefix 0x), or "dec" (no prefix).
                    If value contains x/z states, falls back to binary format.
        """
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

        # Add warnings if any
        if warnings:
            lines.append("\nWarnings:")
            for warning in warnings[:10]:  # Limit to first 10 warnings
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
