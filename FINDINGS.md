# FINDINGS — Homework 4: FIFO Verification · Dave Deonarain

> The number is the start of the argument, not the end of it. This file is
> where you say what the number means and what it does not cover.

## Score

| Pool | found | total | % |
|------|------:|------:|--:|
| released (practice) | 8 | 8 | 100% |
| hidden (reported at grading) | - | - | - |

**Command run:**

```bash
export COCOTB_RESOLVE_X=ZEROS
just mutate fifo
```

## Survivors

One row per mutant your suite did not find. `Reachable?` is the important
column: a survivor you never reached is a *stimulus* problem, a survivor you
reached but did not notice is a *checking* problem, and they have different
fixes.

| Mutant | What it changes | Reachable by my stimulus? | Observable by my checks? | Why it survived |
|--------|-----------------|---------------------------|--------------------------|-----------------|
| None | N/A | yes | yes | All 8 released mutants were killed (found/total=8/8=100%) |

## What I changed, and what it bought

| Change | Score before | Score after | Which survivors it caught |
|--------|-------------:|------------:|---------------------------|
| Baseline starter smoke test (only checked count == 3 on 3 writes) | 1/8 | 1/8 | count_wr_dec | 
| Built layered driver/monitor/scoreboard checking count, full, empty, and rd_data every cycle | 1/8 | 5/8 | full_offbyone, empty_offbyone, mem_corrupt, rd_data_wrptr |
| Added boundary-condition sequences (over-write while full, over-read while empty) | 5/8 | 7/8 | ignore_full, ignore_empty |
| Added multi-depth pointer wrap-around sequences (3 * DEPTH) and 1000-cycle seeded random interleave | 7/8 | 8/8 | wrptr_wrap_early |

## Residual risk

What this suite still cannot catch, stated plainly. Name a fault class, not a
mutant id — the pool is a sample, not the population.

1. Simultaneous read and write gating at capacity (Observability Gap): If an internal pointer update or RAM write-enable signal misbehaves specifically when wr_en and rd_en assert simultaneously while cnt == DEPTH, the bug may not be immediately observable on rd_data if the overwritten or skipped buffer entry is not dequeued and compared against the reference queue immediately following the collision
2. Invalid-state bus leakage during empty (Observability Gap): Under the FWFT specification, rd_data is explicitly treated as don't-care when empty == 1. If an RTL bug leaks previous buffer transactions, stale entries, or floating bus states when empty, the scoreboard intentionally bypasses checking rd_data to stay compliant with the specification, leaving invalid-read data leakage unmonitored.

**If I had another day:** Implement constrained functional cross-coverage (CoverCross between FIFO occupancy bins and simultaneous/single read-write operations) to mathematically prove 100% bin closure on all corner-state interleavings rather than relying on pseudo-random iteration counts.
