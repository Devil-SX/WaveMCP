"""Unified waveform file parser using pywellen (Rust wellen bindings)."""

from pathlib import Path

from pywellen import Waveform

from ..utils.format import format_value


class WellenParser:
    """Parser for VCD and FST waveform files using pywellen."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self._waveform = Waveform(str(self.filepath))
        self._hierarchy = self._waveform.hierarchy
        self._signals = self._build_signal_list()

    def _build_signal_list(self) -> list[dict]:
        """Build flat signal list from hierarchy, compatible with old parsers."""
        signals = []
        for var in self._hierarchy.all_vars():
            full_name = var.full_name(self._hierarchy)
            sig_info = {
                'name': var.name(self._hierarchy),
                'type': var.var_type().lower(),
                'size': var.bitwidth(),
                'path': full_name,
                '_var': var,
            }
            signals.append(sig_info)
        return signals

    def get_signal_list(
        self,
        module_path: str = "",
        max_depth: int = -1,
        limit: int = 100,
        pattern: str = "",
        use_regex: bool = False,
    ) -> tuple[list[dict], int]:
        """Get list of signals with hierarchical filtering.

        Args:
            module_path: Filter signals under this module path (e.g., "top.cpu").
                         Empty string means root (all modules).
            max_depth: Maximum depth relative to module_path (-1 for unlimited).
                       For example, max_depth=1 returns only direct children.
            limit: Maximum number of signals to return (default: 100, 0 for unlimited).
            pattern: Filter pattern for signal names (empty string for no filter).
            use_regex: If True, treat pattern as regex; if False, use substring match.

        Returns:
            Tuple of (signals_list, total_count)
            - signals_list: List of signal dicts (limited by 'limit')
            - total_count: Total number of matching signals before limit
        """
        import re

        regex = None
        if pattern and use_regex:
            regex = re.compile(pattern)

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

            # Filter by pattern
            if pattern:
                if use_regex:
                    if not regex.search(sig_path):
                        continue
                else:
                    if pattern not in sig_path:
                        continue

            # Return signal without internal _var reference
            signals.append({k: v for k, v in sig.items() if k != '_var'})

        total_count = len(signals)
        if limit > 0:
            signals = signals[:limit]
        return signals, total_count

    def get_time_range(self) -> tuple[int, int]:
        """Get the total time range of the waveform."""
        tt = self._waveform.time_table
        return (tt[0], tt[-1])

    def get_signal_values(
        self,
        signal_names: list[str],
        start_time: int,
        end_time: int,
        fmt: str = "bin",
    ) -> tuple[dict[str, list[tuple[int, str]]], list[str]]:
        """Get signal values within specified time range.

        Args:
            signal_names: List of signal names for case-insensitive substring matching
            start_time: Start time (in waveform time units)
            end_time: End time (in waveform time units)
            fmt: Output format - "bin" (default), "hex", or "dec"

        Returns:
            Tuple of (result_dict, warnings_list)
            - result_dict: Dictionary mapping signal paths to list of (time, formatted_value) tuples
            - warnings_list: List of warning messages for values that fell back to binary
        """
        result = {}
        warnings = []

        # Find matching signals
        matching_sigs = []
        for sig in self._signals:
            sig_path = sig['path']
            matches = any(
                name.lower() in sig_path.lower()
                for name in signal_names
            )
            if matches:
                matching_sigs.append(sig)
                result[sig_path] = []

        if not matching_sigs:
            return result, warnings

        # Get values for each matching signal
        for sig in matching_sigs:
            sig_path = sig['path']
            var = sig['_var']
            bitwidth = var.bitwidth()
            signal = self._waveform.get_signal(var)

            for time, value in signal.all_changes():
                if time < start_time:
                    continue
                if time > end_time:
                    break

                # Convert value to binary string for format_value()
                if isinstance(value, str):
                    # 4-state value (contains x/z) - pass directly
                    value_str = value
                elif isinstance(value, int):
                    # 2-state value - convert to zero-padded binary string
                    value_str = format(value, f'0{bitwidth}b')
                elif isinstance(value, float):
                    # Real signal - output as string directly
                    formatted = str(value)
                    result[sig_path].append((time, formatted))
                    continue
                else:
                    value_str = str(value)

                formatted, warning = format_value(value_str, fmt)
                result[sig_path].append((time, formatted))
                if warning:
                    warnings.append(f"{sig_path}@{time}: {warning}")

        return result, warnings
