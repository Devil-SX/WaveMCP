# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- IEEE 754 float conversion tools (hex_to_float, float_to_hex, bin_to_float, float_to_bin)
- Support for float32, float16, and bfloat16 formats
- Value format options (bin, hex, dec) for signal value queries
- New `src/` modular package structure:
  - `src/parsers/` - VCD and FST parser classes
  - `src/tools/` - MCP tool implementations (vcd_tools, fst_tools, conversion_tools, float_tools)
  - `src/utils/` - Utility functions (float_convert, format)
- Tests for float conversion utilities (`tests/test_float_convert.py`)
- Tests for value formatting utilities (`tests/test_format.py`)

### Changed
- Refactored `mcp_server.py` to use modular structure with tools registered from `src/tools/`
- Updated FastMCP initialization with instructions describing available tools
- Updated all existing tests to use the new module structure
- Updated benchmark report with smaller test scale results
