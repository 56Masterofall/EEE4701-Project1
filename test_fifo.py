"""Synchronous FIFO Verification Testbench with Layered Architecture."""

import os
os.environ["COCOTB_RESOLVE_X"] = "ZEROS"

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from tb.driver import FifoDriver, FifoTxn, WIDTH, MASK
from tb.monitor import FifoMonitor
from tb.scoreboard import FifoScoreboard, DEPTH


class FifoEnv:
    """Top-level verification environment connecting driver, monitor, and scoreboard."""

    def __init__(self, dut):
        self.dut = dut
        self.driver = FifoDriver(dut)
        self.monitor = FifoMonitor(dut)
        self.scoreboard = FifoScoreboard(WIDTH, DEPTH)

    async def reset(self):
        await self.driver.reset()
        self.scoreboard.reset()

    async def step(self, wr_en: int, rd_en: int, wr_data: int = 0):
        txn = FifoTxn(wr_en=wr_en, rd_en=rd_en, wr_data=wr_data)
        # Drive on falling edge
        await self.driver.cycle(txn)
        # Sample after rising edge
        sample = await self.monitor.sample()
        # Verify against reference oracle
        self.scoreboard.check(txn, sample)
        # Return to falling edge for next cycle
        await FallingEdge(self.dut.clk)


@cocotb.test()
async def test_fifo_corners_and_random(dut):
    """Execute directed corner tests followed by seeded random stress testing."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    env = FifoEnv(dut)
    await env.reset()

    # 1. Empty boundary: read-while-empty (over-read)
    for _ in range(3):
        await env.step(wr_en=0, rd_en=1, wr_data=0)

    # 2. Fill to full: write DEPTH items
    for i in range(DEPTH):
        await env.step(wr_en=1, rd_en=0, wr_data=(0x10 + i))

    # 3. Full boundary: write-while-full (over-write drop test)
    for i in range(3):
        await env.step(wr_en=1, rd_en=0, wr_data=(0xAA + i))

    # 4. Drain to empty
    for _ in range(DEPTH):
        await env.step(wr_en=0, rd_en=1, wr_data=0)

    # 5. Over-read again after drain
    for _ in range(2):
        await env.step(wr_en=0, rd_en=1, wr_data=0)

    # 6. Simultaneous read and write (at empty, partial, and full)
    # At empty: simultaneous read and write (write happens, read ignored)
    await env.step(wr_en=1, rd_en=1, wr_data=0x55)

    # Fill partially to 4 items
    for i in range(3):
        await env.step(wr_en=1, rd_en=0, wr_data=(0x20 + i))

    # Simultaneous read and write when partial (count stays constant)
    for i in range(5):
        await env.step(wr_en=1, rd_en=1, wr_data=(0x30 + i))

    # Fill to full
    while env.scoreboard.model.count < DEPTH:
        await env.step(wr_en=1, rd_en=0, wr_data=0x77)

    # Simultaneous read and write when full (read happens, write dropped in RTL gating)
    for i in range(3):
        await env.step(wr_en=1, rd_en=1, wr_data=(0x80 + i))

    # 7. Pointer wrap-around test: push/pop past 2 * DEPTH
    await env.reset()
    for i in range(DEPTH * 3):
        await env.step(wr_en=1, rd_en=0, wr_data=(i & MASK))
        await env.step(wr_en=0, rd_en=1, wr_data=0)

    # 8. Seeded pseudo-random interleave test (multi-hundred cycles)
    await env.reset()
    rng = random.Random(42)

    for _ in range(1000):
        wr = rng.choice([0, 1])
        rd = rng.choice([0, 1])
        data = rng.randint(0, MASK)
        await env.step(wr_en=wr, rd_en=rd, wr_data=data)