# FINDINGS — Project 1 Constrained Random Verification of a Synchronous FIFO · Dave Deonarain

> The number is the start of the argument, not the end of it. This file is
> where you say what the number means and what it does not cover.

## Score

| Pool | found | total | % |
|------|------:|------:|--:|
| released (practice) | 8 | 8 | 100.0% |
| hidden (reported at grading) | — | — | — |

**Command run:**

```bash
PYTHONPATH=../../lib python -m craft_mutate.mutate --tb . --pool mutants_released.yaml
```

## Survivors

One row per mutant your suite did not find. `Reachable?` is the important
column: a survivor you never reached is a *stimulus* problem, a survivor you
reached but did not notice is a *checking* problem, and they have different
fixes.

| Mutant | What it changes | Reachable by my stimulus? | Observable by my checks? | Why it survived |
|--------|-----------------|---------------------------|--------------------------|-----------------|
| None | N/A | yes | yes | None survived. All 8 mutants killed on the released pool.  |

## What I changed, and what it bought

| Change | Score before | Score after | Which survivors it caught |
|--------|-------------:|------------:|---------------------------|
| Added refernece scoreboard (FifoScoreboard) with exact pointer & data tracking oracle against python | 0/8 | 5/8 | count_wr_dec, rd_data_wrptr, mem_corrupt, wrptr_wrap_early, full_offbyone  |
| Added directed boundary sweeps (testing all command pairs at count 0, 1, DEPTH-1, and DEPTH) | 5/8 | 7/8 | empty_offbyone, ignore_full |
| Added boundary soak loops (continous read-while-empty and write-while-full checks) paired with falling-edge sampling | 7/8 | 8/8 | ignore_empty |

## Residual risk

What this suite still cannot catch, stated plainly. Name a fault class, not a
mutant id — the pool is a sample, not the population.

1. **Multi-cycle Asynchronous/Glitched Reset Timing**: Reset is driven synchronously with the clock edges during environment setup. If reset asserts asynchronously midway between active edges or experiences runt pulses, internal pointer corruption or register metastability would not be caught by this cycle-accurate driver.
2. **Clock Frequency / Jitter Sensitivity**: The testbench operates on a fixed 10ns clock period. Dynamic duty-cycle distortion or setup/hold margin degradation at physical interface speeds is outside the scope of this cycle-based simulation model.
3. **Multi-beat Backpressure Latency Violations**: While FWFT behavior and full/empty flags are monitored cycle-by-cycle, upstream or downstream handshake stalls with variable protocol latencies (such as AXI-Stream ready/valid handshakes) could expose corner cases not modeled by raw wr_en/rd_en strobes.

**If I had another day:** Implement concurrent SystemVerilog Assertions (SVA) bound directly to the DUT (fifo_bind.sv / fifo_sva.sv) to formally enforce immediate property checks (such as mutual exclusion of pointer divergence and flag stability during stalls) alongside formal model checking.
