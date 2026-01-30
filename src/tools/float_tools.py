"""Float conversion MCP tools for IEEE 754 floating-point formats."""

from mcp.server.fastmcp import FastMCP

from ..utils.float_convert import (
    hex_to_float_value,
    float_to_hex_value,
    bin_to_float_value,
    float_to_bin_value,
    VALID_FLOAT_TYPES,
)


def register(mcp: FastMCP):
    """Register float conversion tools with the MCP server."""

    @mcp.tool()
    async def hex_to_float(hex_value: str, float_type: str = "float32") -> str:
        """Convert hex to floating-point number.

        Args:
            hex_value: Hex string (e.g., "0x40490FDB" or "40490FDB")
            float_type: "float32" (32-bit IEEE 754), "float16" (16-bit IEEE 754),
                       or "bfloat16" (Brain floating point, 16-bit)

        Returns:
            The floating-point value as a string, or error message.

        Examples:
            hex_to_float("40490FDB", "float32") -> "3.1415927410125732"
            hex_to_float("4248", "float16") -> "3.140625"
            hex_to_float("4049", "bfloat16") -> "3.140625"
        """
        try:
            result = hex_to_float_value(hex_value, float_type)
            return str(result)
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error converting hex to float: {e}"

    @mcp.tool()
    async def float_to_hex(float_value: float, float_type: str = "float32") -> str:
        """Convert floating-point number to hex.

        Args:
            float_value: Float number (e.g., 3.14159)
            float_type: "float32" (32-bit IEEE 754), "float16" (16-bit IEEE 754),
                       or "bfloat16" (Brain floating point, 16-bit)

        Returns:
            Hex string with 0x prefix, or error message.

        Examples:
            float_to_hex(3.14159, "float32") -> "0x40490FD0"
            float_to_hex(3.14, "float16") -> "0x4248"
            float_to_hex(3.14, "bfloat16") -> "0x4048"
        """
        try:
            result = float_to_hex_value(float_value, float_type)
            return result
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error converting float to hex: {e}"

    @mcp.tool()
    async def bin_to_float(bin_value: str, float_type: str = "float32") -> str:
        """Convert binary to floating-point number.

        Args:
            bin_value: Binary string (e.g., "01000000010010010000111111011011" or
                      "b01000000010010010000111111011011")
            float_type: "float32" (32-bit IEEE 754), "float16" (16-bit IEEE 754),
                       or "bfloat16" (Brain floating point, 16-bit)

        Returns:
            The floating-point value as a string, or error message.

        Examples:
            bin_to_float("01000000010010010000111111011011", "float32") -> "3.1415927410125732"
            bin_to_float("0100001001001000", "float16") -> "3.140625"
            bin_to_float("0100000001001001", "bfloat16") -> "3.140625"
        """
        try:
            result = bin_to_float_value(bin_value, float_type)
            return str(result)
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error converting binary to float: {e}"

    @mcp.tool()
    async def float_to_bin(float_value: float, float_type: str = "float32") -> str:
        """Convert floating-point number to binary.

        Args:
            float_value: Float number (e.g., 3.14159)
            float_type: "float32" (32-bit IEEE 754), "float16" (16-bit IEEE 754),
                       or "bfloat16" (Brain floating point, 16-bit)

        Returns:
            Binary string with b prefix, or error message.

        Examples:
            float_to_bin(3.14159, "float32") -> "b01000000010010010000111111010000"
            float_to_bin(3.14, "float16") -> "b0100001001001000"
            float_to_bin(3.14, "bfloat16") -> "b0100000001001000"
        """
        try:
            result = float_to_bin_value(float_value, float_type)
            return result
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error converting float to binary: {e}"
