"""Synchronous FIFO Verification Testbench with Layered Architecture and CRV."""

import os
os.environ["COCOTB_RESOLVE_X"] = "ZEROS"

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

from tb.driver import FifoDriver, FifoTxn, WIDTH, MASK
from tb.monitor import FifoMonitor
from tb.scoreboard import FifoScoreboard, DEPTH
from crv.fifo_item import FifoSeqItem
from crv.coverage import sample_fifo_coverage, report_fifo_coverage


class FifoEnv:
    """Top-level verification environment connecting driver, monitor, scoreboard, and coverage."""

    def __init__(self, dut):
        self.dut = dut
        self.driver = FifoDriver(dut)
        self.monitor = FifoMonitor(dut)
        self.scoreboard = FifoScoreboard(WIDTH, DEPTH)

    async def reset(self):
        await self.driver.reset()
        self.scoreboard.reset()

    async def step(self, txn: FifoTxn):
        # 1. Sample state on falling edge (at stimulus time) for input x state coverage
        pre_sample = self.monitor.sample_now()
        sample_fifo_coverage(txn, pre_sample)

        # 2. Drive transaction on falling clock edge
        await self.driver.cycle(txn)

        # 3. Wait for rising edge + 1ns to sample post-clock result
        post_sample = await self.monitor.sample()

        # 4. Scoreboard checks DUT output against reference model
        self.scoreboard.check(txn, post_sample)

        # 5. Advance to next falling edge
        await FallingEdge(self.dut.clk)


@cocotb.test()
async def test_fifo_directed_and_crv(dut):
    """Run comprehensive state-command sweeps followed by pyvsc constrained-random stimulus."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    env = FifoEnv(dut)
    await env.reset()

    # 1. Sweep all 4 commands at every possible FIFO occupancy (0 through DEPTH)
    for target_count in range(DEPTH + 1):
        for wr in [0, 1]:
            for rd in [0, 1]:
                await env.reset()
                for i in range(target_count):
                    await env.step(FifoTxn(wr_en=1, rd_en=0, wr_data=0x10 + i))
                await env.step(FifoTxn(wr_en=wr, rd_en=rd, wr_data=0x99))

    # 2. Multi-cycle boundary stress: empty boundary
    await env.reset()
    for wr in [0, 1]:
        for rd in [0, 1]:
            for _ in range(3):
                await env.step(FifoTxn(wr_en=wr, rd_en=rd, wr_data=0xAA))

    # 3. Multi-cycle boundary stress: full boundary
    for wr in [0, 1]:
        for rd in [0, 1]:
            await env.reset()
            for i in range(DEPTH):
                await env.step(FifoTxn(wr_en=1, rd_en=0, wr_data=0x30 + i))
            for _ in range(3):
                await env.step(FifoTxn(wr_en=wr, rd_en=rd, wr_data=0xEE))

    # 4. Burst fill and drain stress cycles
    await env.reset()
    for _ in range(5):
        for i in range(DEPTH + 2):
            await env.step(FifoTxn(wr_en=1, rd_en=0, wr_data=i & MASK))
        for _ in range(DEPTH + 2):
            await env.step(FifoTxn(wr_en=0, rd_en=1, wr_data=0))

    # 5. Constrained-random stimulus with pyvsc
    await env.reset()
    item = FifoSeqItem()
    for _ in range(2000):
        item.randomize()
        await env.step(item.to_txn())

    # Report coverage metrics
    report_fifo_coverage()