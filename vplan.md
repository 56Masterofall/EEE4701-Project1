# Verification plan — Synchronous FWFT FIFO

**Author:** Dave Deonarain **Spec version:** 1.0 (dut/specs/fifo.md) **Date:** 10/12/2026

> A vplan is an argument that "done" is definable before you write tests. Every
> row here should be something you could defend in a signoff meeting. Rows you
> cannot defend are the honest content of the Risk section, not omissions.

## 1. Scope

**In scope:** 
- Functional verification of parameterized synchronous First-Word Fall-Through (FWFT) FIFO (`WIDTH=8`, `DEPTH=8`).
- Reset behavior and flag initialization.
- Write transactions, full-flag generation, and dropped overflow writes.
- Read transactions, empty-flag generation, FWFT data presentation, and dropped underflow reads.
- Simultaneous read and write operations across mid-occupancy and boundary states.
- Data ordering (strict FIFO queue integrity) and pointer wrap-around.
- Constrained-random verification (CRV) and functional coverage closure.
- Mutation analysis against released mutant pool.

**Out of scope:** 
- Asynchronous multi-clock domain (CDC) interactions (the DUT is strictly synchronous).
- Gate-level timing / post-synthesis timing simulation.
- Power dissipation, synthesis area, and physical design metrics.

**Assumptions about the environment:** 
- A single synchronous rising-edge clock `clk` drives both read and write ports.
- Synchronous active-low reset `rst_n` is driven synchronously with the clock.
- Input data `wr_data` adheres to parameterized `WIDTH`.

## 2. Feature list

One row per behavior the spec requires. `Req` cites a line or section of the
spec — if you cannot cite one, that is a spec gap and it belongs in section 5.

| ID | Feature | Req | Priority | How it is verified |
|----|---------|-----|----------|--------------------|
| F1 | Synchronous reset clears occupancy to 0, sets `empty=1`, `full=0` | Sec 3.1 | H | directed |
| F2 | Normal write pushes data and increments `count` | Sec 3.2 | H | CRV |
| F3 | Write dropped when `full` (no overflow, no corruption) | Sec 3.2 | H | directed |
| F4 | Normal read pops data and decrements `count` | Sec 3.3 | H | CRV |
| F5 | Read ignored when `empty` (no underflow) | Sec 3.3 | H | directed |
| F6 | FWFT behavior (`rd_data` continuously shows queue head when `!empty`) | Sec 2, 3.3 | H | assertion |
| F7 | Simultaneous read + write when partially full maintains `count` | Sec 3.4 | H | CRV |
| F8 | Flag correctness (`full == (count==DEPTH)`, `empty == (count==0)`) | Sec 3.5 | H | assertion |
| F9 | Strict FIFO data ordering and data integrity across pointer wrap-around | Sec 3.6, Sec 4 | H | CRV |
| F10 | Simultaneous read + write at boundaries (at empty, at full) | Sec 4 | M | directed |

## 3. Coverage model

Coverpoints and their bins. A cross earns its place only if the interaction is
where a bug would hide — say which bug.

| ID | Coverpoint | Bins | Why these bins |
|----|-----------|------|----------------|
| C1 | `cp_count` (Occupancy) | `empty` (0), `low` (1..2), `mid` (3..DEPTH-2), `near_full` (DEPTH-1), `full` (DEPTH) | Verifies the FIFO visits every critical occupancy zone, especially boundary transitions. |
| C2 | `cp_wr_en` | `wr_idle` (0), `wr_active` (1) | Validates write control line activity. |
| C3 | `cp_rd_en` | `rd_idle` (0), `rd_active` (1) | Validates read control line activity. |
| C4 | `cp_flags` | `empty_asserted` (`empty==1, full==0`), `neither` (`empty==0, full==0`), `full_asserted` (`empty==0, full==1`) | Ensures status flags assert accurately and never conflict. |
| C5 | `cp_security_reset` (Security & Trust) | `write_during_reset` (`rst_n==0 && wr_en==1`), `read_during_reset` (`rst_n==0 && rd_en==1`) | Probes undefined/illegal control assertions during active reset. |

**Crosses**

| ID | Cross | The interaction it is aimed at |
|----|-------|-------------------------------|
| X1 | `cross_cmd = cp_wr_en x cp_rd_en` | Exercises all 4 command combinations: Idle, Write-only, Read-only, Simultaneous R/W. |
| X2 | `cross_cmd_x_count = cross_cmd x cp_count` | Tests every command type against all occupancy levels (e.g., Simultaneous R/W when Full, Write when Full, Read when Empty). |
| X3 | `cross_flags_x_cmd = cp_flags x cross_cmd` | Validates command response against visible status flags. |

**Illegal / ignore bins:** 
- `cp_flags`: The state where `full == 1 && empty == 1` is strictly illegal and must trigger a fatal check.
- `cp_count`: Values of `count > DEPTH` are illegal and excluded by assertion.

## 4. Test matrix

Every feature maps to at least one test; every test traces back to a feature.
An untraceable test is a test nobody can defend.

| Test | Features | Kind | Pass criterion |
|------|----------|------|----------------|
| `test_reset` | F1, C5 | directed | Reset immediately drives `count=0`, `empty=1`, `full=0`; writes during reset produce no state changes. |
| `test_single_push_pop_fwft` | F2, F4, F6, F9 | directed | Single write presents data immediately on `rd_data` without read enable; subsequent read empties FIFO. |
| `test_fill_drain` | F1, F2, F4, F8, F9 | directed | Sequentially writing DEPTH entries asserts `full=1`; sequential reading asserts `empty=1`; all data matches expected order. |
| `test_overflow_drop` | F3, F8 | directed | Additional writes to a full FIFO keep `full=1`, leave count at DEPTH, and do not corrupt contained data. |
| `test_underflow_ignore` | F5, F8 | directed | Read attempts when empty keep `empty=1`, do not underflow count, and do not cause spurious outputs. |
| `test_simultaneous_rw` | F7, F8, F9 | directed | Performing concurrent read and write maintains invariant `count` and checks FIFO ordering. |
| `test_crv_stress` | F2, F4, F7, F9, F10 | CRV | pyvsc randomized transactions stress burst reads/writes, random concurrent commands, wrap-around; scoreboard queue verifies zero mismatches; coverage model hits 100%. |

## 5. Risk and spec ambiguity

| # | Ambiguity or risk | Where in the spec | How I resolved it | Residual |
|---|-------------------|-------------------|-------------------|----------|
| 1 | Ambiguity | Sec 2, 3.3 | assumed | None; strict adhering to contract |
| 2 | Risk | Sec 3.3, 3.4 | tested both | Low risk; test captures DUT response |
| 3 | Risk | Sec 3.2, 3.4 | tested both | Minimal; tested both in CRV and directed corners |

## 6. Closure criteria

State the numbers *before* you start, so closure is a measurement and not a
negotiation.

- Functional coverage target: **_100_%** of the model in section 3
- Mutation target: **_8_/_8_** or **≥90** on the hidden pool
- Assertions: every property paired with a passing `cover` (no vacuous passes)
- What I will report as **not verified**: Asynchronous clock domain crossings (DUT is strictly synchronous), non-FWFT modes, and post-synthesis gate-level timing corners.
