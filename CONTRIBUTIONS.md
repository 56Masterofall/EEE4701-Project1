# Contributions — N/A · CpE

> This file and the git history are cross-checked against each other, and
> against every member's confidential peer eval. Where the three disagree, the
> conversation happens *before* the Professionalism row is scored — so make
> them agree. A file written the night of M4 will not survive that check, and
> the way it fails is by being vague.

**Members:** Dave Deonarain (tu340511)
**Repo:** ~/EEE4701/craft-vv-student
**Track:** FIFO CRV & Functional Coverage (Project 1)
**Last updated:** October 12, 2026 · **through milestone:** M1 (Project 1)

---

## How to read this file

This record reflects solo work on the synchronous FIFO verification suite. All deliverables, code commits, functional coverage closure, and mutation testing analysis were completed individually.

---

## Project 1 — Simulation Seam (Synchronous FIFO)

| Member | What they owned | Evidence (commits / files / PRs) | Approx. share |
|--------|-----------------|----------------------------------|--------------:|
| Dave Deonarain | Layered testbench architecture (Driver, Monitor, Scoreboard), CRV item generation, functional coverage model, boundary sweeps, and mutation kill sign-off | `code/tb/fifo/tb/`, `code/tb/fifo/crv/`, `code/tb/fifo/test_fifo.py`, `vplan.md`, `FINDINGS.md`, `ai_log.md` | 100% |

**Shared or paired work:**
None (solo project).

**What slipped, and who picked it up:**
Initial uniform random stimulus failed to reach corner cases at FIFO full/empty boundaries (plateauing at 62.5% coverage) and crashed on an invalid `coverage_db.summary` property call. Added `monitor.sample_now()` on falling clock edges alongside directed sweeps across all occupancy depths to resolve scoreboard desynchronization and close 100% of the coverage bins.

---

## Whole-project summary

One row per member, across all four milestones. This is the row a reader checks
first, so it must be consistent with the four sections above.

| Member | Principal contributions (all four milestones) | Overall share |
|--------|-----------------------------------------------|--------------:|
| Dave Deonarain | End-to-end FIFO verification: testbench architecture, CRV with pyvsc, cocotb-coverage closure (68/68 bins), and 100% mutation testing kill rate (8/8 mutants) | 100% |

**The three things this team did that we would each defend in an interview:**

1. Designed a layered verification environment separating cycle-accurate pin driving from transaction monitoring and scoreboard checking against an algorithmic FIFO reference model.
2. Structured constrained-random sequences with `pyvsc` and directed boundary sweeps to achieve 100.0% functional coverage closure (68/68 bins) across all state-command crosses.
3. Validated verification quality through mutation testing using `craft_mutate`, killing 8/8 mutants (100.0%) by detecting flag off-by-one errors, underflow/overflow leaks, and pointer wrapping faults.

## Non-code contributions

Real work that leaves a thin git trace — and is graded all the same. Cite the
artifact where one exists.

| Member | Contribution | Where it shows |
|--------|--------------|----------------|
| Dave Deonarain | Verification plan authoring | `vplan.md` |
| Dave Deonarain | Mutation survivor and kill root cause analysis | `FINDINGS.md` |
| Dave Deonarain | LLM interaction audit and predictive evaluation | `ai_log.md` |

## AI assistance

Consistent with the course policy and your `ctm` record: name where an assistant
was used on capstone work, and who verified the output. The verifier is a named
person, always.

| Where | Used for | Verified by | Where the verification shows |
|-------|----------|-------------|------------------------------|
| `crv/fifo_item.py` | Initial boilerplate for `pyvsc` constrained-random transaction class | Dave Deonarain | Caught and corrected syntax error (`rand_uint_t` -> `rand_bit_t`); tested via standalone CLI run documented in `ai_log.md` |
| `crv/coverage.py` | Drafting `cocotb-coverage` coverpoint and cross structures | Dave Deonarain | Identified missing range bin resolution, fixed crash on `coverage_db.summary`, and added falling-edge pre-sampling to capture correct pre-state command crosses; documented in `ai_log.md` |

---

## Attestation

- [x] Every claim above can be traced to the repo history.
- [x] This file was updated at each milestone, not reconstructed at the end.
- [x] Every member has read this file and agrees it is accurate.
- [x] Each member has separately submitted their **confidential individual peer
      eval** — teammates' main contributions, an equity judgment, one sentence
      of evidence each — outside this repo, by the M4 deadline.
