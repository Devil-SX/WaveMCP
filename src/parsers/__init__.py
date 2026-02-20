"""Parser module with global state management."""

from .wellen_parser import WellenParser

try:
    from .vcd_parser import WaveformParser
except ImportError:
    WaveformParser = None

try:
    from .fst_parser import FstParser
except ImportError:
    FstParser = None

__all__ = [
    "WaveformParser",
    "FstParser",
    "WellenParser",
    "get_vcd_parser",
    "set_vcd_parser",
    "get_fst_parser",
    "set_fst_parser",
    "get_wellen_parser",
    "set_wellen_parser",
]

# Global parser instances
_vcd_parser: "WaveformParser | None" = None
_fst_parser: "FstParser | None" = None
_wellen_parser: WellenParser | None = None


def get_vcd_parser() -> "WaveformParser":
    """Get the current VCD parser instance."""
    if WaveformParser is None:
        raise ImportError(
            "vcdvcd is not installed. Install legacy dependencies: "
            "pip install wave-mcp[legacy]"
        )
    global _vcd_parser
    if _vcd_parser is None:
        raise ValueError("No VCD file loaded. Use load_vcd first.")
    return _vcd_parser


def set_vcd_parser(parser: "WaveformParser | None") -> None:
    """Set the current VCD parser instance."""
    if WaveformParser is None:
        raise ImportError(
            "vcdvcd is not installed. Install legacy dependencies: "
            "pip install wave-mcp[legacy]"
        )
    global _vcd_parser
    _vcd_parser = parser


def get_fst_parser() -> "FstParser":
    """Get the current FST parser instance."""
    if FstParser is None:
        raise ImportError(
            "pylibfst is not installed. Install legacy dependencies: "
            "pip install wave-mcp[legacy]"
        )
    global _fst_parser
    if _fst_parser is None:
        raise ValueError("No FST file loaded. Use load_fst_file first.")
    return _fst_parser


def set_fst_parser(parser: "FstParser | None") -> None:
    """Set the current FST parser instance."""
    if FstParser is None:
        raise ImportError(
            "pylibfst is not installed. Install legacy dependencies: "
            "pip install wave-mcp[legacy]"
        )
    global _fst_parser
    _fst_parser = parser


def get_wellen_parser() -> WellenParser:
    """Get the current wellen parser instance."""
    global _wellen_parser
    if _wellen_parser is None:
        raise ValueError("No waveform file loaded. Use load_waveform first.")
    return _wellen_parser


def set_wellen_parser(parser: WellenParser | None) -> None:
    """Set the current wellen parser instance."""
    global _wellen_parser
    _wellen_parser = parser
