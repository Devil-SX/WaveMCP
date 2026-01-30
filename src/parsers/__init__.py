"""Parser module with global state management."""

from .vcd_parser import WaveformParser
from .fst_parser import FstParser

__all__ = [
    "WaveformParser",
    "FstParser",
    "get_vcd_parser",
    "set_vcd_parser",
    "get_fst_parser",
    "set_fst_parser",
]

# Global parser instances
_vcd_parser: WaveformParser | None = None
_fst_parser: FstParser | None = None


def get_vcd_parser() -> WaveformParser:
    """Get the current VCD parser instance."""
    global _vcd_parser
    if _vcd_parser is None:
        raise ValueError("No VCD file loaded. Use load_vcd first.")
    return _vcd_parser


def set_vcd_parser(parser: WaveformParser | None) -> None:
    """Set the current VCD parser instance."""
    global _vcd_parser
    _vcd_parser = parser


def get_fst_parser() -> FstParser:
    """Get the current FST parser instance."""
    global _fst_parser
    if _fst_parser is None:
        raise ValueError("No FST file loaded. Use load_fst_file first.")
    return _fst_parser


def set_fst_parser(parser: FstParser | None) -> None:
    """Set the current FST parser instance."""
    global _fst_parser
    _fst_parser = parser
