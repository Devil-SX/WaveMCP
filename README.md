# Wave MCP Server

MCP server for viewing and parsing VCD (Value Change Dump) and FST (Fast Signal Trace) waveform files.

## Features

- Load VCD and FST waveform files
- List all signals with hierarchies
- Query time ranges
- Get signal values within time ranges
- Pattern-based signal matching (case-insensitive)
- **FST format support** - Native parsing of GTKWave's compressed binary format
- **Convert Cadence waveform files (SST2/PWLF) to VCD format**

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended package manager)
- Cadence `simvisdbutil` tool (for Cadence file conversion, optional)

### Setup

```bash
# Clone or navigate to the project directory
cd /path/to/wave_mcp

# Install dependencies (creates isolated virtual environment)
uv sync

# Install dev dependencies (for testing)
uv sync --group dev
```

## Usage

### As MCP Server (Claude Desktop)

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "wave-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/wave_mcp", "run", "wave-mcp"]
    }
  }
}
```

**Why use `uv --directory`?**

Each MCP server can have its own isolated Python environment. This prevents dependency conflicts when running multiple MCP servers with different library requirements.

### Debugging with MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector uv --directory /path/to/wave_mcp run wave-mcp
```

The Inspector will:
- Start a web UI (usually at http://localhost:5173)
- Connect to your MCP server
- Show available tools:
  - `load_vcd_file` - Load a VCD file for analysis
  - `get_vcd_signals` - List all signals (VCD)
  - `get_vcd_time_range` - Get time range (VCD)
  - `get_vcd_signal_values` - Get signal values in time range (VCD)
  - `load_fst_file` - Load an FST file for analysis
  - `get_fst_signals` - List all signals (FST)
  - `get_fst_time_range` - Get time range (FST)
  - `get_fst_signal_values` - Get signal values in time range (FST)
  - `convert_cadence_to_vcd` - Convert Cadence waveform to VCD format

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_mcp_server.py::test_load_vcd_file_success -v
```

## Project Structure

```
wave_mcp/
├── mcp_server.py          # Main MCP server implementation
├── pyproject.toml         # Project config and dependencies
├── tests/
│   ├── test_mcp_server.py # pytest test cases
│   └── gen_test_vcd.py    # Test VCD file generator
└── README.md
```

## Supported Formats

- **VCD** (Value Change Dump) - Native format, full support
- **FST** (Fast Signal Trace) - Native format, full support via `pylibfst`
- **Cadence SST2/PWLF** - Can be converted to VCD using `convert_cadence_to_vcd` tool (requires `simvisdbutil`)

### Cadence to VCD Conversion

The `convert_cadence_to_vcd` tool converts Cadence waveform files to VCD format:

```python
# Convert with default output path (same directory, .vcd extension)
convert_cadence_to_vcd(input_file="/path/to/wave.db")

# Convert with custom output path
convert_cadence_to_vcd(
    input_file="/path/to/wave.db",
    output_file="/path/to/output.vcd"
)
```

**Requirements:**
- `simvisdbutil` must be installed and in PATH
- The tool checks for availability before attempting conversion

**Example:**
```
Successfully converted Cadence waveform to VCD format.
Input file:  /absolute/path/to/wave.db
Output file: /absolute/path/to/wave.vcd
```

### FST Format

FST (Fast Signal Trace) is a compressed binary waveform format developed by GTKWave. It offers better compression and faster access than VCD.

**Usage:**
```python
# Load FST file
load_fst_file(fst_path="/path/to/waveform.fst")

# Get list of signals
get_fst_signals()

# Get time range
get_fst_time_range()

# Get signal values
get_fst_signal_values(
    signal_patterns=["clk", "counter"],
    start_time=0,
    end_time=1000
)
```

**Features:**
- Native FST parsing via `pylibfst` library
- Case-insensitive pattern matching for signal names
- Efficient value extraction within time ranges
