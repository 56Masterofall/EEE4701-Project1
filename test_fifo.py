"""Homework 4: Layered FIFO Verification Testbench.

Architecture:
  - FifoDriver: turns transactions into pin transitions on falling edge
  - FifoMonitor: samples DUT outputs after rising edge
  - FifoScoreboard: evaluates outputs against FifoModel oracle
"""

import os
os.environ["COCOTB_RESOLVE_X"] = "ZEROS"

import random
from dataclasses import dataclass
from typing import Optional

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

from models.fifo_model import FifoModel

WIDTH = 8
DEPTH = 8
MASK = (1 << WIDTH) - 1


@dataclass
class FifoTxn:
    wr_en: int = 0
    rd_en: int = 0
    wr_data: int = 0


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
    except ValueError:
        return None
    except Exception:
        return None
    return None


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

    async def cycle(self, wr_en: int, rd_en: int, wr_data: int = 0):
        """Drives transaction stimulus on the falling clock edge."""
        self.dut.wr_en.value = wr_en
        self.dut.rd_en.value = rd_en
        self.dut.wr_data.value = wr_data & MASK


class FifoMonitor:
    """Observes DUT pin outputs after the rising clock edge."""

    def __init__(self, dut):
        self.dut = dut

    async def sample(self) -> FifoSample:
        """Samples outputs 1ns after the rising edge to avoid race conditions."""
        await RisingEdge(self.dut.clk)
        await Timer(1, units="ns")

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


class FifoScoreboard:
    """Verifies DUT behavior against the FifoModel reference oracle."""

    def __init__(self, width: int = WIDTH, depth: int = DEPTH):
        self.model = FifoModel(width, depth)

    def reset(self):
        self.model.reset()

    def check(self, txn: FifoTxn, sample: FifoSample):
        # Step the reference oracle with pre-edge stimulus
        self.model.step(txn.wr_en, txn.wr_data, txn.rd_en)

        # 1. Check count
        assert sample.count is not None, "count output has unresolvable bits ('x'/'z')!"
        assert sample.count == self.model.count, (
            f"Count mismatch: DUT {sample.count} != Model {self.model.count} "
            f"(wr={txn.wr_en}, rd={txn.rd_en}, data=0x{txn.wr_data:02x})"
        )

        # 2. Check full flag
        assert sample.full is not None, "full flag has unresolvable bits ('x'/'z')!"
        expected_full = int(self.model.full)
        assert sample.full == expected_full, (
            f"Full mismatch: DUT {sample.full} != Model {expected_full} "
            f"(count={sample.count})"
        )

        # 3. Check empty flag
        assert sample.empty is not None, "empty flag has unresolvable bits ('x'/'z')!"
        expected_empty = int(self.model.empty)
        assert sample.empty == expected_empty, (
            f"Empty mismatch: DUT {sample.empty} != Model {expected_empty} "
            f"(count={sample.count})"
        )

        # 4. Check rd_data (FWFT head valid only when !empty)
        if not self.model.empty:
            assert sample.rd_data is not None, (
                f"rd_data is unresolvable ('x'/'z') when FIFO is not empty! "
                f"Expected head: 0x{self.model.head:02x}"
            )
            assert sample.rd_data == self.model.head, (
                f"rd_data mismatch: DUT 0x{sample.rd_data:02x} != Model 0x{self.model.head:02x} "
                f"(count={sample.count})"
            )


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
        await self.driver.cycle(txn.wr_en, txn.rd_en, txn.wr_data)
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