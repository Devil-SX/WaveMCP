# Wave MCP Server

MCP server for viewing and parsing VCD (Value Change Dump) and FST (Fast Signal Trace) waveform files.

## Features

- Unified interface for VCD and FST waveform formats (auto-detected from file extension)
- Hierarchical signal listing with filtering (module path, depth, pattern/regex)
- Time range queries
- Signal value extraction with configurable output format (binary, hex, decimal)
- Case-insensitive substring matching for signal names
- IEEE 754 float conversion tools (float32, float16, bfloat16)

## Why pywellen?

Wave MCP uses [pywellen](https://pypi.org/project/pywellen/) — Python bindings for the Rust [wellen](https://github.com/ekiwi/wellen) library — as its waveform parsing backend.

- **Unified interface**: handles both VCD and FST formats with a single parser, eliminating the need for separate `vcdvcd` + `pylibfst` code paths
- **Performance**: VCD loading is ~5-10x faster than vcdvcd; FST value queries are ~1.8x faster than pylibfst
- **Simplicity**: 4 MCP tools instead of 8 format-specific ones

Detailed benchmarks: [waveform-bench](https://devil-sx.github.io/waveform-bench/) | [`docs/benchmark_report.md`](docs/benchmark_report.md)

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended package manager)
- **Rust** (only if no pre-built wheel is available for your platform):
  pywellen distributes pre-compiled wheels for Linux x86_64/ARM64 and macOS x86_64/ARM64.
  Most users **do not need to install Rust**. If you are on an unsupported platform or building from source, install Rust >= 1.73.0:
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  ```

### Setup

```bash
cd /path/to/wave_mcp

# Install (pywellen only — all MCP server needs)
uv sync

# Install with dev/test dependencies (includes vcdvcd, pylibfst for differential testing)
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

### Debugging with MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector uv --directory /path/to/wave_mcp run wave-mcp
```

### Available Tools

#### Waveform Tools

| Tool | Description |
|------|-------------|
| `load_waveform(path, max_file_size_mb)` | Load a VCD or FST file (format auto-detected) |
| `get_signals(module_path, max_depth, limit, pattern, use_regex)` | List signals with hierarchical filtering |
| `get_time_range()` | Get the total time range of the loaded waveform |
| `get_signal_values(signal_names, start_time, end_time, format, limit)` | Query signal values in a time range |

#### Float Conversion Tools

| Tool | Description |
|------|-------------|
| `hex_to_float(hex_value, float_type)` | Convert hex string to float (float32/float16/bfloat16) |
| `float_to_hex(float_value, float_type)` | Convert float to hex string |
| `bin_to_float(bin_value, float_type)` | Convert binary string to float |
| `float_to_bin(float_value, float_type)` | Convert float to binary string |

### Example Workflow

```
# 1. Load a waveform file
load_waveform(path="/path/to/waveform.vcd")

# 2. List signals (with optional filtering)
get_signals(module_path="top.cpu", max_depth=1, limit=50)

# 3. Get time range
get_time_range()

# 4. Query signal values
get_signal_values(
    signal_names=["clk", "counter"],
    start_time=0,
    end_time=1000,
    format="hex"
)
```

## File Size Estimation

### VCD File Size

VCD is a text-based format. File size depends on signal count (N) and timestep count (T):

```
VCD_size (bytes) ~= 10 * T * H(N)
```

Where `H(N) = sum(1/k for k=1..N)` is the N-th harmonic number, approximately `ln(N) + 0.5772`.

| Signals (N) | Timesteps (T) | Estimated VCD Size | Actual VCD Size |
|-------------|---------------|--------------------:|----------------:|
| 10          | 1,000         | ~23 KB              | 27 KB           |
| 10          | 5,000         | ~117 KB             | 146 KB          |
| 50          | 1,000         | ~48 KB              | 44 KB           |
| 100         | 1,000         | ~52 KB              | 55 KB           |
| 100         | 2,000,000     | ~104 MB             | 131 MB          |
| 500         | 2,000,000     | ~137 MB             | 160 MB          |

### FST File Size

FST is a compressed binary format. Typical compression ratio vs VCD: **8x - 20x**.

```
FST_size ~= VCD_size / compression_ratio
```

Compression ratio varies by signal activity. Low-activity signals compress better.

## MCP Output Token Consumption

Rule of thumb: **1000 Tokens ~ 750 Words**.

### `get_signals` Output

Each signal line is approximately 8 words. With the header line:

| limit | Approx Words | Approx Tokens |
|-------|-------------|---------------|
| 10    | ~90         | ~120          |
| 50    | ~410        | ~550          |
| 100   | ~810        | ~1,080        |
| 500   | ~4,010      | ~5,350        |

### `get_signal_values` Output

Each value change line is approximately 3 words. For N signals with C changes per signal:

```
Words ~= 10 + N * (5 + 3 * min(C, limit))
Tokens ~= Words * 1000 / 750
```

| Signals | Changes/Signal | limit | Approx Words | Approx Tokens |
|---------|---------------|-------|-------------|---------------|
| 1       | 100           | 100   | ~315        | ~420          |
| 3       | 100           | 100   | ~925        | ~1,230        |
| 3       | 1000          | 100   | ~925        | ~1,230        |
| 3       | 1000          | 0     | ~9,015      | ~12,020       |
| 10      | 1000          | 100   | ~3,050      | ~4,070        |

**Recommendations for controlling token consumption:**

- Use `limit` parameter (default: 100) to cap value changes per signal
- Narrow the time range (`start_time`/`end_time`) instead of querying the full waveform
- Use `module_path` and `pattern` filters in `get_signals` to reduce signal count

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run benchmark (small scale, quick)
BENCHMARK_SCALE=small uv run pytest tests/test_benchmark.py -v -s

# Run benchmark (full scale: KB to 100MB+, ~6 min)
BENCHMARK_SCALE=full uv run pytest tests/test_benchmark.py -v -s
```

## Project Structure

```
wave_mcp/
├── mcp_server.py              # MCP server entry point
├── pyproject.toml              # Project config and dependencies
├── src/
│   ├── parsers/
│   │   ├── __init__.py         # Parser exports and global state
│   │   ├── wellen_parser.py    # Unified parser (pywellen backend)
│   │   ├── vcd_parser.py       # Legacy VCD parser (vcdvcd, for diff testing)
│   │   └── fst_parser.py       # Legacy FST parser (pylibfst, for diff testing)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── waveform_tools.py   # Unified waveform MCP tools
│   │   └── float_tools.py      # IEEE 754 float conversion tools
│   └── utils/
│       └── format.py           # Value formatting utilities
├── tests/
│   ├── test_waveform_tools.py  # Unified tool integration tests
│   ├── test_differential.py    # Old vs new parser comparison tests
│   ├── test_benchmark.py       # Performance benchmarks
│   └── ...
└── docs/
    └── benchmark_report.md     # Auto-generated benchmark report
```

## Supported Formats

| Format | Extension | Type | Description |
|--------|-----------|------|-------------|
| VCD    | `.vcd`    | Text | IEEE Std 1364 Value Change Dump. Human-readable, widely supported |
| FST    | `.fst`    | Binary | GTKWave Fast Signal Trace. 8-20x smaller than VCD, faster load |
