"""FIFO Driver: drives transaction stimulus synchronously on falling clock edges."""

from dataclasses import dataclass
from cocotb.triggers import FallingEdge, RisingEdge

WIDTH = 8
MASK = (1 << WIDTH) - 1

@dataclass
class FifoTxn:
    wr_en: int = 0
    rd_en: int = 0
    wr_data: int = 0

class FifoDriver:
    """Drives FIFO inputs synchronously on the falling clock edge."""

    def __init__(self, dut):
        self.dut = dut

    async def reset(self, cycles: int = 3):
        self.dut.wr_en.value = 0
        self.dut.rd_en.value = 0
        self.dut.wr_data.value = 0
        self.dut.rst_n.value = 0
        for _ in range(cycles):
            await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    async def cycle(self, txn: FifoTxn):
        """Drives transaction stimulus on the falling clock edge."""
        self.dut.wr_en.value = txn.wr_en
        self.dut.rd_en.value = txn.rd_en
        self.dut.wr_data.value = txn.wr_data & MASK
