"""Generate test VCD waveform file."""

from pathlib import Path

from vcd.writer import VCDWriter


def generate_test_vcd(output_path: str = "test_waveform.vcd") -> None:
    """Generate a sample VCD file with various signal types for testing."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        with VCDWriter(f, timescale="1ns", date="today") as writer:
            # Register signals
            clk = writer.register_var("top", "clk", "wire", size=1, init=0)
            rst = writer.register_var("top", "rst", "wire", size=1, init=1)
            counter = writer.register_var("top", "counter", "wire", size=8, init=0)
            enable = writer.register_var("top", "enable", "wire", size=1, init=0)
            state = writer.register_var("top", "state", "wire", size=2, init=0)

            # Simulation timeline
            for t in range(100):
                timestamp = t * 10

                # Clock toggles every 5ns
                if t % 2 == 0:
                    writer.change(clk, timestamp, 1)
                else:
                    writer.change(clk, timestamp, 0)

                # Reset deasserts at t=20
                if t == 2:
                    writer.change(rst, timestamp, 0)

                # Enable signal toggles
                if t in [10, 30, 50, 70]:
                    writer.change(enable, timestamp, 1)
                elif t in [20, 40, 60, 80]:
                    writer.change(enable, timestamp, 0)

                # State machine changes
                if t == 10:
                    writer.change(state, timestamp, 1)
                elif t == 30:
                    writer.change(state, timestamp, 2)
                elif t == 50:
                    writer.change(state, timestamp, 3)
                elif t == 70:
                    writer.change(state, timestamp, 0)

                # Counter increments when enabled and not reset
                if t >= 2 and t % 10 == 0 and enable:
                    counter_val = (t // 10) % 256
                    writer.change(counter, timesta
                    mp, counter_val)

    print(f"Generated test VCD file: {output_path}")


def generate_complex_vcd(output_path: str = "test_complex.vcd") -> None:
    """Generate a more complex VCD file with buses and multiple modules."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        with VCDWriter(f, timescale="1ns", date="today") as writer:
            # Module A signals
            clk_a = writer.register_var("cpu", "clk", "wire", size=1, init=0)
            addr_a = writer.register_var("cpu", "addr", "wire", size=16, init=0)
            data_a = writer.register_var("cpu", "data", "wire", size=32, init=0)
            valid_a = writer.register_var("cpu", "valid", "wire", size=1, init=0)

            # Module B signals
            clk_b = writer.register_var("mem", "clk", "wire", size=1, init=0)
            ready_b = writer.register_var("mem", "ready", "wire", size=1, init=0)

            # Simulation
            for t in range(200):
                timestamp = t * 5

                # Clocks
                if t % 2 == 0:
                    writer.change(clk_a, timestamp, 1)
                    writer.change(clk_b, timestamp, 1)
                else:
                    writer.change(clk_a, timestamp, 0)
                    writer.change(clk_b, timestamp, 0)

                # CPU transaction
                if t % 20 == 10:
                    writer.change(valid_a, timestamp, 1)
                    writer.change(addr_a, timestamp, (t // 20) * 4)
                    writer.change(data_a, timestamp, (t // 20) * 0x1000 + 0xABCD)
                elif t % 20 == 15:
                    writer.change(valid_a, timestamp, 0)

                # Memory ready
                if t % 20 == 12:
                    writer.change(ready_b, timestamp, 1)
                elif t % 20 == 18:
                    writer.change(ready_b, timestamp, 0)

    print(f"Generated complex VCD file: {output_path}")


if __name__ == "__main__":
    # Generate test files in tests directory
    generate_test_vcd("tests/test_waveform.vcd")
    generate_complex_vcd("tests/test_complex.vcd")
