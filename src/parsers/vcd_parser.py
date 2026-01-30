"""VCD waveform file parser using vcdvcd."""

from pathlib import Path

from vcdvcd import VCDVCD

from ..utils.format import format_value


class WaveformParser:
    """Parser for VCD waveform files using vcdvcd."""

    def __init__(self, vcd_path: str):
        self.vcd_path = Path(vcd_path)
        self.vcd = VCDVCD(str(self.vcd_path))

    def get_signal_list(self) -> list[dict]:
        """Get list of all signals."""
        signals = []
        for sig_name in self.vcd.signals:
            sig_obj = self.vcd[sig_name]
            signals.append({
                'name': sig_name.split('.')[-1],
                'type': sig_obj.var_type,
                'size': sig_obj.size,
                'path': sig_name,
            })
        return signals

    def get_time_range(self) -> tuple[int, int]:
        """Get the total time range of the waveform."""
        return (self.vcd.begintime, self.vcd.endtime)

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
            start_time: Start time (in VCD time units)
            end_time: End time (in VCD time units)
            fmt: Output format - "bin" (default), "hex", or "dec"

        Returns:
            Tuple of (result_dict, warnings_list)
            - result_dict: Dictionary mapping signal paths to list of (time, formatted_value) tuples
            - warnings_list: List of warning messages for values that fell back to binary
        """
        result = {}
        warnings = []

        # Find matching signals
        for sig_name in self.vcd.signals:
            # Check if signal matches any pattern
            matches = any(
                pattern.lower() in sig_name.lower()
                for pattern in signal_patterns
            )
            if not matches:
                continue

            sig_obj = self.vcd[sig_name]
            values = []
            for t, v in sig_obj.tv:
                if start_time <= t <= end_time:
                    formatted, warning = format_value(str(v), fmt)
                    values.append((t, formatted))
                    if warning:
                        warnings.append(f"{sig_name}@{t}: {warning}")
            if values:
                result[sig_name] = values

        return result, warnings
