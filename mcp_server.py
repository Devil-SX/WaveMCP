"""MCP server for viewing and parsing VCD and FST waveform files."""

from mcp.server.fastmcp import FastMCP

from src.tools import waveform_tools, float_tools

# Initialize FastMCP server
mcp = FastMCP(
    "wave-viewer",
    instructions=(
        "Waveform file viewer for VCD and FST formats. "
        "Use load_waveform to load a file, get_signals to list signals, "
        "get_time_range to get the time range, and get_signal_values to query values. "
        "Format is auto-detected from the file extension. "
        "Float conversion tools (hex_to_float, float_to_hex, bin_to_float, float_to_bin) "
        "are available for IEEE 754 float32, float16, and bfloat16 formats."
    ),
)

# Register all tools
waveform_tools.register(mcp)
float_tools.register(mcp)


def main():
    """Initialize and run the server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
