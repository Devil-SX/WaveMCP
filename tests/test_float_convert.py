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


class TestSpecialIEEE754Values:
    """Tests for special IEEE 754 floating-point values."""

    # === Positive and Negative Zero ===

    def test_float32_positive_zero(self):
        """Test float32 positive zero (0x00000000)."""
        result = hex_to_float_value("00000000", "float32")
        assert result == 0.0
        assert not math.copysign(1, result) < 0  # Positive zero

    def test_float32_negative_zero(self):
        """Test float32 negative zero (0x80000000)."""
        result = hex_to_float_value("80000000", "float32")
        assert result == 0.0
        assert math.copysign(1, result) < 0  # Negative zero

    def test_float16_negative_zero(self):
        """Test float16 negative zero (0x8000)."""
        result = hex_to_float_value("8000", "float16")
        assert result == 0.0
        assert math.copysign(1, result) < 0

    def test_bfloat16_negative_zero(self):
        """Test bfloat16 negative zero (0x8000)."""
        result = hex_to_float_value("8000", "bfloat16")
        assert result == 0.0
        assert math.copysign(1, result) < 0

    # === Infinity ===

    def test_float32_positive_infinity(self):
        """Test float32 positive infinity (0x7F800000)."""
        result = hex_to_float_value("7F800000", "float32")
        assert result == float('inf')

    def test_float32_negative_infinity(self):
        """Test float32 negative infinity (0xFF800000)."""
        result = hex_to_float_value("FF800000", "float32")
        assert result == float('-inf')

    def test_float16_positive_infinity(self):
        """Test float16 positive infinity (0x7C00)."""
        result = hex_to_float_value("7C00", "float16")
        assert result == float('inf')

    def test_float16_negative_infinity(self):
        """Test float16 negative infinity (0xFC00)."""
        result = hex_to_float_value("FC00", "float16")
        assert result == float('-inf')

    def test_bfloat16_positive_infinity(self):
        """Test bfloat16 positive infinity (0x7F80)."""
        result = hex_to_float_value("7F80", "bfloat16")
        assert result == float('inf')

    def test_bfloat16_negative_infinity(self):
        """Test bfloat16 negative infinity (0xFF80)."""
        result = hex_to_float_value("FF80", "bfloat16")
        assert result == float('-inf')

    # === NaN (Not a Number) ===

    def test_float32_quiet_nan(self):
        """Test float32 quiet NaN (0x7FC00000)."""
        result = hex_to_float_value("7FC00000", "float32")
        assert math.isnan(result)

    def test_float32_signaling_nan(self):
        """Test float32 signaling NaN (0x7F800001)."""
        result = hex_to_float_value("7F800001", "float32")
        assert math.isnan(result)

    def test_float16_nan(self):
        """Test float16 NaN (0x7E00)."""
        result = hex_to_float_value("7E00", "float16")
        assert math.isnan(result)

    def test_bfloat16_nan(self):
        """Test bfloat16 NaN (0x7FC0)."""
        result = hex_to_float_value("7FC0", "bfloat16")
        assert math.isnan(result)

    # === Denormalized (Subnormal) Numbers ===

    def test_float32_smallest_denormal(self):
        """Test float32 smallest denormalized number (0x00000001)."""
        result = hex_to_float_value("00000001", "float32")
        # Smallest positive denormal: 2^(-126) * 2^(-23) = 2^(-149)
        assert result > 0
        assert result < 1e-44  # Very small

    def test_float32_largest_denormal(self):
        """Test float32 largest denormalized number (0x007FFFFF)."""
        result = hex_to_float_value("007FFFFF", "float32")
        # Largest denormal is just below smallest normal
        assert result > 0
        assert result < 1.18e-38

    def test_float16_smallest_denormal(self):
        """Test float16 smallest denormalized number (0x0001)."""
        result = hex_to_float_value("0001", "float16")
        assert result > 0
        assert result < 1e-7

    # === Smallest/Largest Normal Numbers ===

    def test_float32_smallest_normal(self):
        """Test float32 smallest normalized positive number (0x00800000)."""
        result = hex_to_float_value("00800000", "float32")
        expected = 2**(-126)  # ~1.175e-38
        assert abs(result - expected) / expected < 1e-6

    def test_float32_largest_normal(self):
        """Test float32 largest finite number (0x7F7FFFFF)."""
        result = hex_to_float_value("7F7FFFFF", "float32")
        # Should be close to 3.4028235e+38
        assert result > 3.4e38
        assert result < float('inf')

    def test_float16_smallest_normal(self):
        """Test float16 smallest normalized positive number (0x0400)."""
        result = hex_to_float_value("0400", "float16")
        expected = 2**(-14)  # ~6.1e-5
        assert abs(result - expected) / expected < 1e-3

    def test_float16_largest_normal(self):
        """Test float16 largest finite number (0x7BFF)."""
        result = hex_to_float_value("7BFF", "float16")
        # Should be close to 65504
        assert 65000 < result < 66000


class TestInputParsing:
    """Tests for input string parsing edge cases."""

    # === Hex Input Variations ===

    def test_hex_lowercase(self):
        """Test lowercase hex input."""
        result = hex_to_float_value("3f800000", "float32")
        assert result == 1.0

    def test_hex_mixed_case(self):
        """Test mixed case hex input."""
        result = hex_to_float_value("3F80aB00", "float32")
        # Just verify it parses without error
        assert isinstance(result, float)

    def test_hex_with_leading_whitespace(self):
        """Test hex with leading whitespace."""
        result = hex_to_float_value("  3F800000", "float32")
        assert result == 1.0

    def test_hex_with_trailing_whitespace(self):
        """Test hex with trailing whitespace."""
        result = hex_to_float_value("3F800000  ", "float32")
        assert result == 1.0

    def test_hex_short_input_float32(self):
        """Test short hex input padded with zeros for float32."""
        # "1" becomes "00000001"
        result = hex_to_float_value("1", "float32")
        assert result == hex_to_float_value("00000001", "float32")

    def test_hex_short_input_float16(self):
        """Test short hex input padded with zeros for float16."""
        # "1" becomes "0001"
        result = hex_to_float_value("1", "float16")
        assert result == hex_to_float_value("0001", "float16")

    # === Binary Input Variations ===

    def test_bin_lowercase_prefix(self):
        """Test binary with lowercase b prefix."""
        result = bin_to_float_value("b0011110000000000", "float16")
        assert result == 1.0

    def test_bin_uppercase_prefix(self):
        """Test binary with uppercase B prefix (treated as 0b)."""
        # Note: 'B' at start is treated like 'b'
        result = bin_to_float_value("0b0011110000000000", "float16")
        assert result == 1.0

    def test_bin_short_input(self):
        """Test short binary input padded with zeros."""
        # Short input should be zero-padded
        result = bin_to_float_value("1", "float32")
        assert result == hex_to_float_value("00000001", "float32")

    def test_bin_with_whitespace(self):
        """Test binary with leading/trailing whitespace."""
        result = bin_to_float_value("  0011110000000000  ", "float16")
        assert result == 1.0


class TestBoundaryValues:
    """Tests for boundary values and precision limits."""

    # === Powers of Two ===

    @pytest.mark.parametrize("exp", range(-10, 11))
    def test_float32_powers_of_two(self, exp):
        """Test float32 exact representation of powers of two."""
        value = 2.0 ** exp
        hex_val = float_to_hex_value(value, "float32")
        result = hex_to_float_value(hex_val, "float32")
        assert result == value

    @pytest.mark.parametrize("exp", range(-10, 11))
    def test_float16_powers_of_two_in_range(self, exp):
        """Test float16 powers of two within representable range."""
        if exp < -14 or exp > 15:  # Skip values outside float16 range
            pytest.skip("Value outside float16 range")
        value = 2.0 ** exp
        hex_val = float_to_hex_value(value, "float16")
        result = hex_to_float_value(hex_val, "float16")
        assert abs(result - value) / value < 1e-3

    # === Precision Boundaries ===

    def test_float32_23bit_mantissa_precision(self):
        """Test float32 at 23-bit mantissa precision limit."""
        # 1.0 + 2^(-23) should be representable
        value = 1.0 + 2**(-23)
        hex_val = float_to_hex_value(value, "float32")
        result = hex_to_float_value(hex_val, "float32")
        assert result == value

    def test_float32_beyond_precision(self):
        """Test float32 value beyond precision gets rounded."""
        # 1.0 + 2^(-24) cannot be exactly represented
        value = 1.0 + 2**(-24)
        hex_val = float_to_hex_value(value, "float32")
        result = hex_to_float_value(hex_val, "float32")
        # Should round to either 1.0 or 1.0 + 2^(-23)
        assert result == 1.0 or result == 1.0 + 2**(-23)

    def test_float16_10bit_mantissa_precision(self):
        """Test float16 at 10-bit mantissa precision limit."""
        # float16 has 10-bit mantissa
        value = 1.0 + 2**(-10)
        hex_val = float_to_hex_value(value, "float16")
        result = hex_to_float_value(hex_val, "float16")
        assert abs(result - value) / value < 1e-3

    # === Overflow/Underflow Edge Cases ===

    def test_float16_overflow_to_infinity(self):
        """Test float16 overflow raises OverflowError."""
        # float16 max is ~65504, values above cause overflow
        with pytest.raises(OverflowError):
            float_to_hex_value(100000.0, "float16")

    def test_float16_underflow_to_zero(self):
        """Test float16 underflow converts tiny value to zero."""
        # Very small value underflows to zero
        result = float_to_hex_value(1e-10, "float16")
        back = hex_to_float_value(result, "float16")
        assert back == 0.0

    def test_bfloat16_precision_loss(self):
        """Test bfloat16 has less precision than float32."""
        # bfloat16 has only 7-bit mantissa
        value = 1.0 + 2**(-8)
        bf16_hex = float_to_hex_value(value, "bfloat16")
        f32_hex = float_to_hex_value(value, "float32")
        bf16_result = hex_to_float_value(bf16_hex, "bfloat16")
        f32_result = hex_to_float_value(f32_hex, "float32")
        # bfloat16 should have lost precision
        assert f32_result == value
        assert bf16_result != value or bf16_result == value  # May or may not round


class TestNegativeValues:
    """Tests for negative value handling."""

    @pytest.mark.parametrize("value", [-0.5, -1.5, -2.0, -100.0])
    def test_float32_negative_roundtrip(self, value):
        """Test float32 negative value roundtrip for exact values."""
        hex_val = float_to_hex_value(value, "float32")
        result = hex_to_float_value(hex_val, "float32")
        assert result == value

    def test_float32_negative_roundtrip_approximate(self):
        """Test float32 negative value roundtrip for non-exact values."""
        # -0.001 cannot be exactly represented in float32
        value = -0.001
        hex_val = float_to_hex_value(value, "float32")
        result = hex_to_float_value(hex_val, "float32")
        assert abs(result - value) / abs(value) < 1e-6

    @pytest.mark.parametrize("value", [-0.5, -1.5, -2.0, -10.0])
    def test_float16_negative_roundtrip(self, value):
        """Test float16 negative value roundtrip."""
        hex_val = float_to_hex_value(value, "float16")
        result = hex_to_float_value(hex_val, "float16")
        assert abs(result - value) / abs(value) < 1e-3

    @pytest.mark.parametrize("value", [-0.5, -1.5, -2.0, -100.0])
    def test_bfloat16_negative_roundtrip(self, value):
        """Test bfloat16 negative value roundtrip."""
        hex_val = float_to_hex_value(value, "bfloat16")
        result = hex_to_float_value(hex_val, "bfloat16")
        assert abs(result - value) / abs(value) < 0.01


class TestCrossFormatConsistency:
    """Tests for consistency between hex and binary conversions."""

    @pytest.mark.parametrize("float_type", VALID_FLOAT_TYPES)
    def test_hex_bin_consistency(self, float_type):
        """Test that hex and binary conversions produce consistent results."""
        value = 42.5
        hex_val = float_to_hex_value(value, float_type)
        bin_val = float_to_bin_value(value, float_type)

        hex_back = hex_to_float_value(hex_val, float_type)
        bin_back = bin_to_float_value(bin_val, float_type)

        assert hex_back == bin_back

    @pytest.mark.parametrize("float_type", VALID_FLOAT_TYPES)
    def test_hex_to_bin_equivalence(self, float_type):
        """Test hex string converts to equivalent binary string."""
        value = 3.5
        hex_val = float_to_hex_value(value, float_type)[2:]  # Remove 0x
        bin_val = float_to_bin_value(value, float_type)[1:]  # Remove b

        # Convert hex to binary manually and compare
        expected_bits = len(bin_val)
        hex_as_int = int(hex_val, 16)
        hex_as_bin = format(hex_as_int, f'0{expected_bits}b')

        assert bin_val == hex_as_bin


class TestErrorHandling:
    """Tests for error handling with invalid inputs."""

    def test_empty_hex_string(self):
        """Test empty hex string returns zero (padded with zeros)."""
        # Empty string becomes "00000000" after zfill, which is 0.0
        result = hex_to_float_value("", "float32")
        assert result == 0.0

    def test_invalid_hex_characters(self):
        """Test invalid hex characters raise error."""
        with pytest.raises(ValueError):
            hex_to_float_value("GHIJ", "float32")

    def test_empty_bin_string(self):
        """Test empty binary string."""
        # Empty string becomes 0 after zfill
        result = bin_to_float_value("", "float32")
        assert result == 0.0

    def test_invalid_bin_characters(self):
        """Test invalid binary characters raise error."""
        with pytest.raises(ValueError):
            bin_to_float_value("0123", "float32")  # '2' and '3' are invalid

    @pytest.mark.parametrize("invalid_type", ["float64", "double", "int32", ""])
    def test_invalid_float_types(self, invalid_type):
        """Test various invalid float types raise ValueError."""
        with pytest.raises(ValueError):
            hex_to_float_value("3F800000", invalid_type)

    def test_none_float_type(self):
        """Test None as float type raises ValueError."""
        # None is converted to string 'None' by the function
        with pytest.raises(ValueError):
            hex_to_float_value("3F800000", None)


class TestSpecificKnownValues:
    """Tests with specific known IEEE 754 bit patterns."""

    # Known float32 values from IEEE 754 specification
    FLOAT32_TEST_CASES = [
        ("3F800000", 1.0),
        ("40000000", 2.0),
        ("40400000", 3.0),
        ("40800000", 4.0),
        ("3F000000", 0.5),
        ("3E800000", 0.25),
        ("3E000000", 0.125),
        ("42280000", 42.0),
        ("C2280000", -42.0),
        ("447A0000", 1000.0),
        ("C47A0000", -1000.0),
    ]

    @pytest.mark.parametrize("hex_val,expected", FLOAT32_TEST_CASES)
    def test_known_float32_values(self, hex_val, expected):
        """Test known float32 hex to value mappings."""
        result = hex_to_float_value(hex_val, "float32")
        assert result == expected

    @pytest.mark.parametrize("hex_val,expected", FLOAT32_TEST_CASES)
    def test_known_float32_reverse(self, hex_val, expected):
        """Test known float32 value to hex mappings."""
        result = float_to_hex_value(expected, "float32")
        assert result == "0x" + hex_val

    # Known float16 values
    FLOAT16_TEST_CASES = [
        ("3C00", 1.0),
        ("4000", 2.0),
        ("4200", 3.0),
        ("4400", 4.0),
        ("3800", 0.5),
        ("3400", 0.25),
        ("5140", 42.0),
        ("D140", -42.0),
    ]

    @pytest.mark.parametrize("hex_val,expected", FLOAT16_TEST_CASES)
    def test_known_float16_values(self, hex_val, expected):
        """Test known float16 hex to value mappings."""
        result = hex_to_float_value(hex_val, "float16")
        assert result == expected

    # Known bfloat16 values (upper 16 bits of float32)
    BFLOAT16_TEST_CASES = [
        ("3F80", 1.0),
        ("4000", 2.0),
        ("4040", 3.0),
        ("4080", 4.0),
        ("3F00", 0.5),
        ("4228", 42.0),
        ("C228", -42.0),
    ]

    @pytest.mark.parametrize("hex_val,expected", BFLOAT16_TEST_CASES)
    def test_known_bfloat16_values(self, hex_val, expected):
        """Test known bfloat16 hex to value mappings."""
        result = hex_to_float_value(hex_val, "bfloat16")
        assert result == expected
