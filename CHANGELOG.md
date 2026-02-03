# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Signal filtering with `pattern` and `use_regex` parameters for `get_vcd_signals` and `get_fst_signals`
  - Substring matching (default) when `use_regex=False`
  - Regex matching when `use_regex=True`
- IEEE 754 float conversion tools (hex_to_float, float_to_hex, bin_to_float, float_to_bin)
- Support for float32, float16, and bfloat16 formats
- Value format options (bin, hex, dec) for signal value queries
- New `src/` modular package structure:
  - `src/parsers/` - VCD and FST parser classes
  - `src/tools/` - MCP tool implementations (vcd_tools, fst_tools, conversion_tools, float_tools)
  - `src/utils/` - Utility functions (float_convert, format)
- Tests for float conversion utilities (`tests/test_float_convert.py`)
- Tests for value formatting utilities (`tests/test_format.py`)
- Comprehensive corner case tests for float conversion:
  - IEEE 754 special values (positive/negative zero, infinity, NaN, denormalized numbers)
  - Input parsing edge cases (whitespace, case variations, short inputs)
  - Boundary values (powers of two, precision limits, overflow/underflow)
  - Known IEEE 754 bit patterns for all supported formats

### Changed
- Renamed `signal_patterns` parameter to `signal_names` in `get_vcd_signal_values` and `get_fst_signal_values` for clarity
- Refactored `mcp_server.py` to use modular structure with tools registered from `src/tools/`
- Updated FastMCP initialization with instructions describing available tools
- Updated all existing tests to use the new module structure
- Updated benchmark report with smaller test scale results
