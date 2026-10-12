"""FIFO Monitor: samples DUT outputs after the rising clock edge."""

from dataclasses import dataclass
from typing import Optional
from cocotb.triggers import RisingEdge, Timer


@dataclass
class FifoSample:
    count: Optional[int]
    full: Optional[int]
    empty: Optional[int]
    rd_data: Optional[int]


def safe_int(handle) -> Optional[int]:
    """Safely reads a cocotb signal handle without raising on 'x' or 'z'."""
    try:
        val = handle.value
        if val.is_resolvable:
            return int(val)
    except Exception:
        return None
    return None


class FifoMonitor:
    """Observes DUT pin outputs after the rising clock edge."""

    def __init__(self, dut):
        self.dut = dut

    def sample_now(self) -> FifoSample:
        """Immediately samples current DUT output values without advancing simulation time."""
        c = safe_int(self.dut.count)
        f = safe_int(self.dut.full)
        e = safe_int(self.dut.empty)
        r = safe_int(self.dut.rd_data) if (e == 0) else None

        return FifoSample(
            count=c,
            full=f,
            empty=e,
            rd_data=r,
        )

    async def sample(self) -> FifoSample:
        """Samples outputs 1ns after the rising edge to avoid race conditions."""
        await RisingEdge(self.dut.clk)
        await Timer(1, units="ns")
        return self.sample_now()