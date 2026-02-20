# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.2.1] - 2026-02-20

### Added
- Deprecation notice in README: repository archived, recommending Programmatic Tools
- cloc language badge (Python 829 lines) in README

## [0.2.0]

### Added
- Unified waveform parsing backend based on pywellen (`WellenParser`)
- Unified MCP tools: `load_waveform`, `get_signals`, `get_time_range`, `get_signal_values`
- Differential tests comparing WellenParser against legacy parsers (`tests/test_differential.py`)
- Unified tool integration tests (`tests/test_waveform_tools.py`)
- 100MB+ full-scale benchmark support
- IEEE 754 float conversion tools (hex_to_float, float_to_hex, bin_to_float, float_to_bin)
- Support for float32, float16, and bfloat16 formats
- Signal filtering with `pattern` and `use_regex` parameters
- Value format options (bin, hex, dec) for signal value queries
- Modular package structure (`src/parsers/`, `src/tools/`, `src/utils/`)
- Comprehensive corner case tests for float conversion

### Changed
- MCP server simplified from 8 format-specific tools to 4 unified tools
- `vcdvcd` and `pylibfst` moved from required to optional dependencies (`pip install wave-mcp[legacy]`)
- Benchmark report updated with file size and speedup ratio columns
- Renamed `signal_patterns` parameter to `signal_names` for clarity
- Refactored `mcp_server.py` to use modular tool structure

### Removed
- MCP server no longer exposes legacy tools (`load_vcd_file`, `get_vcd_signals`, `load_fst_file`, etc.)
- Cadence waveform conversion support (`convert_cadence_to_vcd` tool)
