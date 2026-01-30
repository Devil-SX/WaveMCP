"""Cadence waveform conversion MCP tools."""

import asyncio
import shutil
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP


def _check_simvisdbutil() -> str | None:
    """Check if simvisdbutil tool is available in PATH."""
    return shutil.which("simvisdbutil")


def register(mcp: FastMCP):
    """Register conversion tools with the MCP server."""

    @mcp.tool()
    async def convert_cadence_to_vcd(
        input_file: str, output_file: str = ""
    ) -> str:
        """Convert Cadence waveform file (SST2/PWLF) to VCD format using simvisdbutil.

        Args:
            input_file: Path to the input Cadence waveform file
            output_file: Optional path to the output VCD file.
                         If not specified, output will be in the same directory
                         as input_file with .vcd extension.

        Returns:
            Success message with absolute paths of input and output files,
            or error message if conversion fails.
        """
        # Check if simvisdbutil is available
        simvis_path = _check_simvisdbutil()
        if simvis_path is None:
            return "Error: simvisdbutil tool not found in PATH. Please ensure Cadence tools are installed and accessible."

        # Validate input file
        input_path = Path(input_file)
        if not input_path.exists():
            return f"Error: Input file not found: {input_file}"

        # Determine output file path
        if output_file:
            output_path = Path(output_file)
        else:
            # Default: same directory as input, with .vcd extension
            output_path = input_path.with_suffix(".vcd")

        # Build command
        cmd = [
            "simvisdbutil",
            str(input_path.absolute()),
            "-VCD",
            "-OUTPUT", str(output_path.absolute()),
            "-OVERWRITE",
            "-NOCOPYRIGHT",
        ]

        # Run conversion
        try:
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True
            )

            if result.returncode != 0:
                return f"Error: simvisdbutil failed with exit code {result.returncode}\n{result.stderr}"

            # Verify output file was created
            if not output_path.exists():
                return f"Error: Output file was not created. simvisdbutil output:\n{result.stdout}"

            return (
                f"Successfully converted Cadence waveform to VCD format.\n"
                f"Input file:  {input_path.absolute()}\n"
                f"Output file: {output_path.absolute()}"
            )
        except FileNotFoundError:
            return "Error: simvisdbutil executable not found. Please check Cadence installation."
        except Exception as e:
            return f"Error during conversion: {e}"
