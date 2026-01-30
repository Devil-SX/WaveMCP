"""Float conversion utilities for IEEE 754 floating-point formats.

Supports:
- float32 (IEEE 754 single precision, 32-bit)
- float16 (IEEE 754 half precision, 16-bit)
- bfloat16 (Brain floating point, 16-bit)
"""

import struct

VALID_FLOAT_TYPES = ("float32", "float16", "bfloat16")


def _validate_float_type(float_type: str) -> None:
    """Validate the float type parameter."""
    if float_type not in VALID_FLOAT_TYPES:
        raise ValueError(
            f"Invalid float_type '{float_type}'. "
            f"Must be one of: {', '.join(VALID_FLOAT_TYPES)}"
        )


def _normalize_hex(hex_value: str) -> str:
    """Normalize hex string by removing 0x prefix and converting to uppercase."""
    hex_value = hex_value.strip()
    if hex_value.lower().startswith("0x"):
        hex_value = hex_value[2:]
    return hex_value.upper()


def _normalize_bin(bin_value: str) -> str:
    """Normalize binary string by removing b prefix."""
    bin_value = bin_value.strip()
    if bin_value.lower().startswith("0b") or bin_value.lower().startswith("b"):
        if bin_value.lower().startswith("0b"):
            bin_value = bin_value[2:]
        else:
            bin_value = bin_value[1:]
    return bin_value


def hex_to_float_value(hex_value: str, float_type: str = "float32") -> float:
    """Convert hex string to floating-point number.

    Args:
        hex_value: Hex string (e.g., "0x40490FDB" or "40490FDB")
        float_type: "float32", "float16", or "bfloat16"

    Returns:
        The floating-point value

    Examples:
        >>> hex_to_float_value("40490FDB", "float32")  # ~3.14159
        >>> hex_to_float_value("4248", "float16")      # ~3.14
        >>> hex_to_float_value("4049", "bfloat16")     # ~3.14
    """
    _validate_float_type(float_type)
    hex_value = _normalize_hex(hex_value)

    if float_type == "float32":
        # 32-bit: 8 hex digits
        hex_value = hex_value.zfill(8)
        bytes_val = bytes.fromhex(hex_value)
        return struct.unpack(">f", bytes_val)[0]

    elif float_type == "float16":
        # 16-bit: 4 hex digits
        hex_value = hex_value.zfill(4)
        bytes_val = bytes.fromhex(hex_value)
        return struct.unpack(">e", bytes_val)[0]

    else:  # bfloat16
        # bfloat16 is upper 16 bits of float32, pad with zeros
        hex_value = hex_value.zfill(4)
        # Append 16 zero bits to form a float32
        bytes_val = bytes.fromhex(hex_value + "0000")
        return struct.unpack(">f", bytes_val)[0]


def float_to_hex_value(float_value: float, float_type: str = "float32") -> str:
    """Convert floating-point number to hex string.

    Args:
        float_value: Float number (e.g., 3.14159)
        float_type: "float32", "float16", or "bfloat16"

    Returns:
        Hex string with 0x prefix

    Examples:
        >>> float_to_hex_value(3.14159, "float32")  # "0x40490FD0"
        >>> float_to_hex_value(3.14, "float16")     # "0x4248"
        >>> float_to_hex_value(3.14, "bfloat16")    # "0x4048"
    """
    _validate_float_type(float_type)

    if float_type == "float32":
        bytes_val = struct.pack(">f", float_value)
        return "0x" + bytes_val.hex().upper()

    elif float_type == "float16":
        bytes_val = struct.pack(">e", float_value)
        return "0x" + bytes_val.hex().upper()

    else:  # bfloat16
        # Pack as float32, then take upper 16 bits
        bytes_val = struct.pack(">f", float_value)
        return "0x" + bytes_val[:2].hex().upper()


def bin_to_float_value(bin_value: str, float_type: str = "float32") -> float:
    """Convert binary string to floating-point number.

    Args:
        bin_value: Binary string (e.g., "01000000010010010000111111011011")
        float_type: "float32", "float16", or "bfloat16"

    Returns:
        The floating-point value

    Examples:
        >>> bin_to_float_value("01000000010010010000111111011011", "float32")  # ~3.14159
        >>> bin_to_float_value("0100001001001000", "float16")  # ~3.14
        >>> bin_to_float_value("0100000001001001", "bfloat16")  # ~3.14
    """
    _validate_float_type(float_type)
    bin_value = _normalize_bin(bin_value)

    # Determine expected bit length
    if float_type == "float32":
        expected_bits = 32
    else:  # float16 or bfloat16
        expected_bits = 16

    # Pad with leading zeros if needed
    bin_value = bin_value.zfill(expected_bits)

    # Convert binary to hex
    int_value = int(bin_value, 2)
    hex_digits = expected_bits // 4
    hex_value = format(int_value, f"0{hex_digits}X")

    return hex_to_float_value(hex_value, float_type)


def float_to_bin_value(float_value: float, float_type: str = "float32") -> str:
    """Convert floating-point number to binary string.

    Args:
        float_value: Float number (e.g., 3.14159)
        float_type: "float32", "float16", or "bfloat16"

    Returns:
        Binary string with b prefix

    Examples:
        >>> float_to_bin_value(3.14159, "float32")  # "b01000000010010010000111111010000"
        >>> float_to_bin_value(3.14, "float16")     # "b0100001001001000"
        >>> float_to_bin_value(3.14, "bfloat16")    # "b0100000001001000"
    """
    _validate_float_type(float_type)

    # Get hex representation (without 0x prefix)
    hex_str = float_to_hex_value(float_value, float_type)[2:]

    # Convert hex to binary
    int_value = int(hex_str, 16)

    # Determine expected bit length
    if float_type == "float32":
        expected_bits = 32
    else:  # float16 or bfloat16
        expected_bits = 16

    return "b" + format(int_value, f"0{expected_bits}b")
