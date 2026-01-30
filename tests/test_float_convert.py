"""Tests for float conversion utilities."""

import struct
import math

import pytest

from src.utils.float_convert import (
    hex_to_float_value,
    float_to_hex_value,
    bin_to_float_value,
    float_to_bin_value,
    VALID_FLOAT_TYPES,
)


class TestHexToFloat:
    """Tests for hex_to_float_value function."""

    def test_float32_pi(self):
        """Test float32 conversion for pi."""
        # IEEE 754 representation of pi (approx 3.14159265)
        result = hex_to_float_value("40490FDB", "float32")
        assert abs(result - 3.14159265) < 1e-6

    def test_float32_with_prefix(self):
        """Test float32 with 0x prefix."""
        result = hex_to_float_value("0x40490FDB", "float32")
        assert abs(result - 3.14159265) < 1e-6

    def test_float32_one(self):
        """Test float32 conversion for 1.0."""
        # IEEE 754: 1.0 = 0x3F800000
        result = hex_to_float_value("3F800000", "float32")
        assert result == 1.0

    def test_float32_negative(self):
        """Test float32 conversion for negative number."""
        # IEEE 754: -1.0 = 0xBF800000
        result = hex_to_float_value("BF800000", "float32")
        assert result == -1.0

    def test_float32_zero(self):
        """Test float32 conversion for zero."""
        result = hex_to_float_value("00000000", "float32")
        assert result == 0.0

    def test_float16_basic(self):
        """Test float16 conversion."""
        # float16: 1.0 = 0x3C00
        result = hex_to_float_value("3C00", "float16")
        assert result == 1.0

    def test_float16_pi_approx(self):
        """Test float16 conversion for pi approximation."""
        # float16 has lower precision
        result = hex_to_float_value("4248", "float16")
        assert abs(result - 3.14) < 0.1

    def test_bfloat16_basic(self):
        """Test bfloat16 conversion."""
        # bfloat16: 1.0 = 0x3F80 (upper 16 bits of float32 1.0)
        result = hex_to_float_value("3F80", "bfloat16")
        assert result == 1.0

    def test_bfloat16_pi_approx(self):
        """Test bfloat16 conversion for pi approximation."""
        # bfloat16 for pi: upper 16 bits of 0x40490FDB = 0x4049
        result = hex_to_float_value("4049", "bfloat16")
        assert abs(result - 3.14) < 0.1

    def test_invalid_float_type(self):
        """Test that invalid float type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            hex_to_float_value("40490FDB", "float64")
        assert "float64" in str(exc_info.value)


class TestFloatToHex:
    """Tests for float_to_hex_value function."""

    def test_float32_one(self):
        """Test float32 conversion for 1.0."""
        result = float_to_hex_value(1.0, "float32")
        assert result == "0x3F800000"

    def test_float32_negative_one(self):
        """Test float32 conversion for -1.0."""
        result = float_to_hex_value(-1.0, "float32")
        assert result == "0xBF800000"

    def test_float32_zero(self):
        """Test float32 conversion for 0.0."""
        result = float_to_hex_value(0.0, "float32")
        assert result == "0x00000000"

    def test_float32_pi(self):
        """Test float32 conversion for pi."""
        result = float_to_hex_value(3.14159265, "float32")
        # Should be close to 0x40490FDB
        assert result.startswith("0x4049")

    def test_float16_one(self):
        """Test float16 conversion for 1.0."""
        result = float_to_hex_value(1.0, "float16")
        assert result == "0x3C00"

    def test_float16_negative_one(self):
        """Test float16 conversion for -1.0."""
        result = float_to_hex_value(-1.0, "float16")
        assert result == "0xBC00"

    def test_bfloat16_one(self):
        """Test bfloat16 conversion for 1.0."""
        result = float_to_hex_value(1.0, "bfloat16")
        assert result == "0x3F80"

    def test_bfloat16_negative_one(self):
        """Test bfloat16 conversion for -1.0."""
        result = float_to_hex_value(-1.0, "bfloat16")
        assert result == "0xBF80"

    def test_invalid_float_type(self):
        """Test that invalid float type raises ValueError."""
        with pytest.raises(ValueError):
            float_to_hex_value(1.0, "invalid")


class TestBinToFloat:
    """Tests for bin_to_float_value function."""

    def test_float32_one(self):
        """Test float32 conversion for 1.0."""
        # 0x3F800000 in binary
        bin_val = "00111111100000000000000000000000"
        result = bin_to_float_value(bin_val, "float32")
        assert result == 1.0

    def test_float32_with_prefix(self):
        """Test float32 with b prefix."""
        bin_val = "b00111111100000000000000000000000"
        result = bin_to_float_value(bin_val, "float32")
        assert result == 1.0

    def test_float32_with_0b_prefix(self):
        """Test float32 with 0b prefix."""
        bin_val = "0b00111111100000000000000000000000"
        result = bin_to_float_value(bin_val, "float32")
        assert result == 1.0

    def test_float16_one(self):
        """Test float16 conversion for 1.0."""
        # 0x3C00 in binary
        bin_val = "0011110000000000"
        result = bin_to_float_value(bin_val, "float16")
        assert result == 1.0

    def test_bfloat16_one(self):
        """Test bfloat16 conversion for 1.0."""
        # 0x3F80 in binary
        bin_val = "0011111110000000"
        result = bin_to_float_value(bin_val, "bfloat16")
        assert result == 1.0

    def test_invalid_float_type(self):
        """Test that invalid float type raises ValueError."""
        with pytest.raises(ValueError):
            bin_to_float_value("0", "invalid")


class TestFloatToBin:
    """Tests for float_to_bin_value function."""

    def test_float32_one(self):
        """Test float32 conversion for 1.0."""
        result = float_to_bin_value(1.0, "float32")
        # Should be 32 bits with b prefix
        assert result.startswith("b")
        assert len(result) == 33  # b + 32 bits
        # 0x3F800000 in binary
        assert result == "b00111111100000000000000000000000"

    def test_float32_zero(self):
        """Test float32 conversion for 0.0."""
        result = float_to_bin_value(0.0, "float32")
        assert result == "b00000000000000000000000000000000"

    def test_float16_one(self):
        """Test float16 conversion for 1.0."""
        result = float_to_bin_value(1.0, "float16")
        # Should be 16 bits with b prefix
        assert result.startswith("b")
        assert len(result) == 17  # b + 16 bits
        # 0x3C00 in binary
        assert result == "b0011110000000000"

    def test_bfloat16_one(self):
        """Test bfloat16 conversion for 1.0."""
        result = float_to_bin_value(1.0, "bfloat16")
        # Should be 16 bits with b prefix
        assert result.startswith("b")
        assert len(result) == 17  # b + 16 bits
        # 0x3F80 in binary
        assert result == "b0011111110000000"

    def test_invalid_float_type(self):
        """Test that invalid float type raises ValueError."""
        with pytest.raises(ValueError):
            float_to_bin_value(1.0, "invalid")


class TestRoundTrip:
    """Test round-trip conversions."""

    @pytest.mark.parametrize("float_type", VALID_FLOAT_TYPES)
    def test_hex_roundtrip(self, float_type):
        """Test hex -> float -> hex roundtrip."""
        original_float = 1.5
        hex_val = float_to_hex_value(original_float, float_type)
        back_to_float = hex_to_float_value(hex_val, float_type)
        back_to_hex = float_to_hex_value(back_to_float, float_type)
        assert hex_val == back_to_hex

    @pytest.mark.parametrize("float_type", VALID_FLOAT_TYPES)
    def test_bin_roundtrip(self, float_type):
        """Test bin -> float -> bin roundtrip."""
        original_float = 2.0
        bin_val = float_to_bin_value(original_float, float_type)
        back_to_float = bin_to_float_value(bin_val, float_type)
        back_to_bin = float_to_bin_value(back_to_float, float_type)
        assert bin_val == back_to_bin

    @pytest.mark.parametrize("value", [0.0, 1.0, -1.0, 0.5, 100.0, -100.0])
    def test_float32_value_preservation(self, value):
        """Test that float32 conversions preserve values."""
        hex_val = float_to_hex_value(value, "float32")
        result = hex_to_float_value(hex_val, "float32")
        assert result == value

    def test_special_values_float32(self):
        """Test special float values."""
        # Infinity
        inf_hex = float_to_hex_value(float('inf'), "float32")
        assert hex_to_float_value(inf_hex, "float32") == float('inf')

        # Negative infinity
        ninf_hex = float_to_hex_value(float('-inf'), "float32")
        assert hex_to_float_value(ninf_hex, "float32") == float('-inf')

        # NaN
        nan_hex = float_to_hex_value(float('nan'), "float32")
        assert math.isnan(hex_to_float_value(nan_hex, "float32"))
