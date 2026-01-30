"""Value formatting utilities for waveform signal values."""


def contains_unknown(value: str) -> bool:
    """Check if value contains unknown states (x or z)."""
    return 'x' in value.lower() or 'z' in value.lower()


def format_value(value: str, fmt: str = "bin") -> tuple[str, str | None]:
    """Format a binary signal value to the specified format.

    Args:
        value: Raw binary string from vcdvcd/pylibfst (e.g., "1010", "x", "z")
        fmt: Output format - "bin" (default), "hex", or "dec"

    Returns:
        Tuple of (formatted_value, warning_message or None)
        - formatted_value: The value with appropriate prefix
        - warning_message: Warning if fallback to binary was needed, None otherwise

    Format examples:
        | Raw Value | bin      | hex              | dec              |
        |-----------|----------|------------------|------------------|
        | "1010"    | "b1010"  | "0xA"            | "10"             |
        | "11111111"| "b11111111" | "0xFF"        | "255"            |
        | "0"       | "b0"     | "0x0"            | "0"              |
        | "x"       | "bx"     | "bx" (fallback)  | "bx" (fallback)  |
        | "1x0z"    | "b1x0z"  | "b1x0z" (fallback)| "b1x0z" (fallback)|
    """
    fmt = fmt.lower()

    if fmt not in ("bin", "hex", "dec"):
        raise ValueError(f"Invalid format '{fmt}'. Must be 'bin', 'hex', or 'dec'.")

    # Binary format always works
    if fmt == "bin":
        return f"b{value}", None

    # For hex and dec, check for unknown states
    if contains_unknown(value):
        warning = f"Value '{value}' contains x/z states, falling back to binary format"
        return f"b{value}", warning

    # Convert to integer for hex/dec formatting
    try:
        int_value = int(value, 2)
    except ValueError:
        # If conversion fails, fall back to binary
        warning = f"Value '{value}' could not be parsed as binary, falling back to binary format"
        return f"b{value}", warning

    if fmt == "hex":
        return f"0x{int_value:X}", None
    else:  # dec
        return str(int_value), None
