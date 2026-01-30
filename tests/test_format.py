"""Tests for value formatting utilities."""

import pytest

from src.utils.format import format_value, contains_unknown


class TestContainsUnknown:
    """Tests for contains_unknown function."""

    def test_no_unknown(self):
        """Test value without unknown states."""
        assert contains_unknown("1010") is False
        assert contains_unknown("0") is False
        assert contains_unknown("11111111") is False

    def test_with_x(self):
        """Test value with x state."""
        assert contains_unknown("x") is True
        assert contains_unknown("1x0") is True
        assert contains_unknown("X") is True
        assert contains_unknown("1X0") is True

    def test_with_z(self):
        """Test value with z state."""
        assert contains_unknown("z") is True
        assert contains_unknown("1z0") is True
        assert contains_unknown("Z") is True
        assert contains_unknown("1Z0") is True

    def test_with_both(self):
        """Test value with both x and z states."""
        assert contains_unknown("xz") is True
        assert contains_unknown("1x0z") is True


class TestFormatValue:
    """Tests for format_value function."""

    def test_binary_format_simple(self):
        """Test binary format for simple values."""
        result, warning = format_value("1010", "bin")
        assert result == "b1010"
        assert warning is None

    def test_binary_format_with_unknown(self):
        """Test binary format with unknown states."""
        result, warning = format_value("1x0z", "bin")
        assert result == "b1x0z"
        assert warning is None  # Binary format doesn't warn

    def test_hex_format_simple(self):
        """Test hex format for simple values."""
        # 1010 binary = 10 decimal = A hex
        result, warning = format_value("1010", "hex")
        assert result == "0xA"
        assert warning is None

    def test_hex_format_full_byte(self):
        """Test hex format for full byte."""
        # 11111111 binary = 255 decimal = FF hex
        result, warning = format_value("11111111", "hex")
        assert result == "0xFF"
        assert warning is None

    def test_hex_format_zero(self):
        """Test hex format for zero."""
        result, warning = format_value("0", "hex")
        assert result == "0x0"
        assert warning is None

    def test_hex_format_with_unknown(self):
        """Test hex format falls back to binary with unknown states."""
        result, warning = format_value("1x0z", "hex")
        assert result == "b1x0z"
        assert warning is not None
        assert "x/z" in warning.lower() or "fallback" in warning.lower()

    def test_dec_format_simple(self):
        """Test decimal format for simple values."""
        # 1010 binary = 10 decimal
        result, warning = format_value("1010", "dec")
        assert result == "10"
        assert warning is None

    def test_dec_format_full_byte(self):
        """Test decimal format for full byte."""
        # 11111111 binary = 255 decimal
        result, warning = format_value("11111111", "dec")
        assert result == "255"
        assert warning is None

    def test_dec_format_zero(self):
        """Test decimal format for zero."""
        result, warning = format_value("0", "dec")
        assert result == "0"
        assert warning is None

    def test_dec_format_with_unknown(self):
        """Test decimal format falls back to binary with unknown states."""
        result, warning = format_value("x", "dec")
        assert result == "bx"
        assert warning is not None

    def test_case_insensitive_format(self):
        """Test that format parameter is case insensitive."""
        result1, _ = format_value("1010", "BIN")
        result2, _ = format_value("1010", "HEX")
        result3, _ = format_value("1010", "DEC")

        assert result1 == "b1010"
        assert result2 == "0xA"
        assert result3 == "10"

    def test_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            format_value("1010", "invalid")
        assert "invalid" in str(exc_info.value).lower()

    def test_known_values_table(self):
        """Test the specific values from the plan's table."""
        # | Raw Value | bin | hex | dec |
        # |-----------|-----|-----|-----|
        # | 1010 | b1010 | 0xA | 10 |
        assert format_value("1010", "bin") == ("b1010", None)
        assert format_value("1010", "hex") == ("0xA", None)
        assert format_value("1010", "dec") == ("10", None)

        # | 11111111 | b11111111 | 0xFF | 255 |
        assert format_value("11111111", "bin") == ("b11111111", None)
        assert format_value("11111111", "hex") == ("0xFF", None)
        assert format_value("11111111", "dec") == ("255", None)

        # | 0 | b0 | 0x0 | 0 |
        assert format_value("0", "bin") == ("b0", None)
        assert format_value("0", "hex") == ("0x0", None)
        assert format_value("0", "dec") == ("0", None)

        # | x | bx | bx (fallback) | bx (fallback) |
        result_bin, warn_bin = format_value("x", "bin")
        result_hex, warn_hex = format_value("x", "hex")
        result_dec, warn_dec = format_value("x", "dec")
        assert result_bin == "bx"
        assert result_hex == "bx"
        assert result_dec == "bx"
        assert warn_bin is None
        assert warn_hex is not None
        assert warn_dec is not None

        # | 1x0z | b1x0z | b1x0z (fallback) | b1x0z (fallback) |
        result_bin, warn_bin = format_value("1x0z", "bin")
        result_hex, warn_hex = format_value("1x0z", "hex")
        result_dec, warn_dec = format_value("1x0z", "dec")
        assert result_bin == "b1x0z"
        assert result_hex == "b1x0z"
        assert result_dec == "b1x0z"
        assert warn_bin is None
        assert warn_hex is not None
        assert warn_dec is not None
