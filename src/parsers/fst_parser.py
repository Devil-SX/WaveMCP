"""FST waveform file parser using pylibfst."""

from pathlib import Path

import pylibfst

from ..utils.format import format_value


class FstParser:
    """Parser for FST waveform files using pylibfst."""

    def __init__(self, fst_path: str):
        self.fst_path = Path(fst_path)
        self._fst = None
        self._signals = None
        self._signals_by_handle = {}
        self._start_time = 0
        self._end_time = 0
        self._load()

    def _load(self):
        """Load and parse FST file."""
        self._fst = pylibfst.lib.fstReaderOpen(str(self.fst_path).encode('utf-8'))
        if self._fst == pylibfst.ffi.NULL:
            raise ValueError(f"Failed to open FST file: {self.fst_path}")

        # Get time range
        self._start_time = pylibfst.lib.fstReaderGetStartTime(self._fst)
        self._end_time = pylibfst.lib.fstReaderGetEndTime(self._fst)

        # Get signals using pylibfst helper
        _scopes, signals_info = pylibfst.get_scopes_signals2(self._fst)

        self._signals = []
        self._signals_by_handle = {}

        for sig_path, sig in signals_info.by_name.items():
            sig_info = {
                'name': sig_path.split('.')[-1],
                'type': 'wire',  # FST doesn't expose var type easily
                'size': sig.length,
                'path': sig_path,
                'handle': sig.handle,
            }
            self._signals.append(sig_info)
            self._signals_by_handle[sig.handle] = sig_path

    def get_signal_list(
        self,
        module_path: str = "",
        max_depth: int = -1,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """Get list of signals with hierarchical filtering.

        Args:
            module_path: Filter signals under this module path (e.g., "top.cpu").
                         Empty string means root (all modules).
            max_depth: Maximum depth relative to module_path (-1 for unlimited).
                       For example, max_depth=1 returns only direct children.
            limit: Maximum number of signals to return (default: 100, 0 for unlimited).

        Returns:
            Tuple of (signals_list, total_count)
            - signals_list: List of signal dicts (limited by 'limit')
            - total_count: Total number of matching signals before limit
        """
        signals = []
        module_prefix = module_path + "." if module_path else ""
        module_depth = module_path.count(".") + 1 if module_path else 0

        for sig in self._signals:
            sig_path = sig['path']

            # Filter by module_path
            if module_path and not sig_path.startswith(module_prefix):
                continue

            # Filter by max_depth
            if max_depth >= 0:
                sig_depth = sig_path.count(".")
                relative_depth = sig_depth - module_depth + 1
                if relative_depth > max_depth:
                    continue

            # Return signal without internal handle
            signals.append({k: v for k, v in sig.items() if k != 'handle'})

        total_count = len(signals)
        if limit > 0:
            signals = signals[:limit]
        return signals, total_count

    def get_time_range(self) -> tuple[int, int]:
        """Get the total time range of the waveform."""
        return (self._start_time, self._end_time)

    def get_signal_values(
        self,
        signal_patterns: list[str],
        start_time: int,
        end_time: int,
        fmt: str = "bin",
    ) -> tuple[dict[str, list[tuple[int, str]]], list[str]]:
        """Get signal values within specified time range.

        Args:
            signal_patterns: List of signal name patterns to match
            start_time: Start time (in FST time units)
            end_time: End time (in FST time units)
            fmt: Output format - "bin" (default), "hex", or "dec"

        Returns:
            Tuple of (result_dict, warnings_list)
            - result_dict: Dictionary mapping signal paths to list of (time, formatted_value) tuples
            - warnings_list: List of warning messages for values that fell back to binary
        """
        result = {}
        warnings = []

        # Find matching signals
        matching_handles = set()
        handle_to_path = {}

        for sig in self._signals:
            sig_path = sig['path']
            matches = any(
                pattern.lower() in sig_path.lower()
                for pattern in signal_patterns
            )
            if matches:
                matching_handles.add(sig['handle'])
                handle_to_path[sig['handle']] = sig_path
                result[sig_path] = []

        if not matching_handles:
            return result, warnings

        # Clear and set specific signal masks
        pylibfst.lib.fstReaderClrFacProcessMaskAll(self._fst)
        for handle in matching_handles:
            pylibfst.lib.fstReaderSetFacProcessMask(self._fst, handle)

        # Collect raw values first (closure can't modify warnings list directly)
        raw_values = {path: [] for path in result}

        # Collect values within time range
        def value_change_callback(_user_data, time, handle, value):
            if handle in matching_handles and start_time <= time <= end_time:
                sig_path = handle_to_path[handle]
                value_str = pylibfst.string(value)
                raw_values[sig_path].append((time, value_str))

        # Read value changes
        pylibfst.fstReaderIterBlocks(self._fst, value_change_callback)

        # Format values and collect warnings
        for sig_path, values in raw_values.items():
            for t, v in values:
                formatted, warning = format_value(v, fmt)
                result[sig_path].append((t, formatted))
                if warning:
                    warnings.append(f"{sig_path}@{t}: {warning}")

        return result, warnings

    def close(self):
        """Close FST file handle."""
        if self._fst is not None and self._fst != pylibfst.ffi.NULL:
            pylibfst.lib.fstReaderClose(self._fst)
            self._fst = None
