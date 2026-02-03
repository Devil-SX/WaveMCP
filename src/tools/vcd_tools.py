"""VCD waveform MCP tools."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..parsers import WaveformParser, get_vcd_parser, set_vcd_parser


def register(mcp: FastMCP):
    """Register VCD tools with the MCP server."""

    @mcp.tool()
    async def load_vcd_file(vcd_path: str, max_file_size_mb: int = 100) -> str:
        """Load a VCD format waveform file for analysis (VCD format only).

        Args:
            vcd_path: Path to the VCD file (relative or absolute)
            max_file_size_mb: Maximum allowed file size in MB (default: 100MB).
                              Set to 0 to disable size check.
        """
        path = Path(vcd_path)
        if not path.exists():
            return f"Error: File not found: {vcd_path}"

        # Check file size
        if max_file_size_mb > 0:
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_file_size_mb:
                return (
                    f"Error: File size ({file_size_mb:.1f}MB) exceeds limit ({max_file_size_mb}MB).\n"
                    f"Please split the file into smaller segments, or use a more compact format like FST.\n"
                    f"To override this limit, set max_file_size_mb=0 or increase the value."
                )

        try:
            parser = WaveformParser(str(path))
            set_vcd_parser(parser)
            _, signal_count = parser.get_signal_list(limit=0)
            return f"Successfully loaded VCD file: {vcd_path}\nFound {signal_count} signals."
        except Exception as e:
            return f"Error loading VCD file: {e}"

    @mcp.tool()
    async def get_vcd_signals(
        module_path: str = "",
        max_depth: int = -1,
        limit: int = 100,
        pattern: str = "",
        use_regex: bool = False,
    ) -> str:
        """Get list of signals in the loaded VCD file with hierarchical filtering (VCD format only).

        IMPORTANT: To avoid overwhelming output, please:
        - Specify a module_path to focus on a specific module
        - Use max_depth to limit hierarchy traversal
        - Use limit to control output size (default: 100 signals)

        Args:
            module_path: Filter signals under this module (e.g., "top.cpu"). Empty string for root.
            max_depth: Maximum depth relative to module_path (-1 for unlimited, 1 for direct children only).
            limit: Maximum number of signals to display (default: 100). Use 0 for no limit.
            pattern: Filter pattern for signal names (empty string for no filter).
            use_regex: If True, treat pattern as regex; if False, use substring match.
        """
        try:
            parser = get_vcd_parser()
        except ValueError as e:
            return str(e)

        signals, total_count = parser.get_signal_list(module_path, max_depth, limit, pattern, use_regex)
        if not signals:
            if module_path:
                return f"No signals found under module: {module_path}"
            return "No signals found in VCD file."

        filter_info = ""
        if module_path:
            filter_info += f", module={module_path}"
        if max_depth >= 0:
            filter_info += f", max_depth={max_depth}"
        if pattern:
            filter_info += f", pattern={pattern}"
            if use_regex:
                filter_info += " (regex)"

        lines = [f"Signals in VCD file (showing {len(signals)}/{total_count}{filter_info}):"]
        for sig in signals:
            lines.append(
                f"  {sig['path']:<40} type={sig['type']:<4} size={sig['size']}"
            )
        if limit > 0 and total_count > limit:
            lines.append(f"\n  ... ({total_count - limit} more signals, use limit=0 to show all)")

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
        signal_names: list[str],
        start_time: int,
        end_time: int,
        format: str = "bin",
        limit: int = 100,
    ) -> str:
        """Get values for specified VCD signals within a time range (VCD format only).

        IMPORTANT: To avoid overwhelming output, please:
        - Use a narrow time range instead of the full waveform
        - Query specific signals rather than using broad patterns
        - Use the 'limit' parameter to control output size

        Args:
            signal_names: List of signal names for case-insensitive substring matching
            start_time: Start time (in VCD time units)
            end_time: End time (in VCD time units)
            format: Output format - "bin" (default, prefix b), "hex" (prefix 0x), or "dec" (no prefix).
                    If value contains x/z states, falls back to binary format.
            limit: Maximum number of value changes to display per signal (default: 100). Use 0 for no limit.
        """
        try:
            parser = get_vcd_parser()
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
                display_changes = changes if limit == 0 else changes[:limit]
                for t, v in display_changes:
                    lines.append(f"  {t:>10}: {v}")
                if limit > 0 and len(changes) > limit:
                    lines.append(f"  ... ({len(changes) - limit} more entries, use limit=0 to show all)")

        return "\n".join(lines)
