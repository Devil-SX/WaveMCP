# Wave MCP Server

MCP server for viewing and parsing VCD (Value Change Dump) waveform files.

## Features

- Load VCD waveform files
- List all signals with hierarchies
- Query time ranges
- Get signal values within time ranges
- Pattern-based signal matching (case-insensitive)

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended package manager)

### Setup

```bash
# Clone or navigate to the project directory
cd /home/sdu/wave_mcp

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
      "args": ["--directory", "/home/sdu/wave_mcp", "run", "wave-mcp"]
    }
  }
}
```

**Why use `uv --directory`?**

Each MCP server can have its own isolated Python environment. This prevents dependency conflicts when running multiple MCP servers with different library requirements.

### Debugging with MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector uv --directory /home/sdu/wave_mcp run wave-mcp
```

The Inspector will:
- Start a web UI (usually at http://localhost:5173)
- Connect to your MCP server
- Show available tools: `load_vcd_file`, `get_vcd_signals`, `get_vcd_time_range`, `get_vcd_signal_values`

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

## VCD Format Only

This server currently supports VCD (Value Change Dump) format files only. Support for other waveform formats (FST, WLF, etc.) may be added in the future.
