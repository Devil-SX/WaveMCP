"""MCP server for viewing and parsing VCD and FST waveform files."""

from mcp.server.fastmcp import FastMCP

from src.tools import vcd_tools, fst_tools, conversion_tools, float_tools

# Initialize FastMCP server
mcp = FastMCP(
    "wave-viewer",
    instructions=(
        "Waveform file viewer for VCD and FST formats. "
        "Recommended: Use VCD interfaces (load_vcd_file, get_vcd_signals, "
        "get_vcd_time_range, get_vcd_signal_values) for better performance. "
        "FST interfaces are available for cases where only FST format is provided. "
        "Float conversion tools (hex_to_float, float_to_hex, bin_to_float, float_to_bin) "
        "are available for IEEE 754 float32, float16, and bfloat16 formats."
    ),
)

# Register all tools
vcd_tools.register(mcp)
fst_tools.register(mcp)
conversion_tools.register(mcp)
float_tools.register(mcp)


def main():
    """Initialize and run the server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
