# AI Log: Check the Machine

Author: Dave Deonarain (tu340511)
Module: Synchronous FIFO Verification (`code/tb/fifo`)
Tooling: cocotb, pyvsc, cocotb-coverage, Verilator

---

## 1. Context & Objectives

Per the "Check the Machine" project requirement, this log records the interactive synthesis of the Constrained-Random Verification (CRV) stimulus generators, transaction items, and functional coverage models. It documents the initial generative prompts, explicit pre-execution failure predictions, measured empirical evidence from the simulator, and the engineering remedies applied to achieve signoff-grade verification.

---

## 2. Log Entry 1: Constrained-Random Transaction (`FifoSeqItem`)

### 2.1 Prompt Given
"Draft a constrained-random FIFO transaction class FifoSeqItem using pyvsc for a synchronous FIFO with signals wr_en, rd_en, and wr_data matching WIDTH=8."

### 2.2 Prediction Before Running
* **Type Signature Hallucination**: Language models frequently conflate SystemVerilog scalar types (bit, logic, uint) or generic Python primitives with pyvsc's AST type wrappers. Expected an immediate attribute/constructor failure such as vsc.rand_uint_t instead of vsc.rand_bit_t.
* **Distribution Shaping Defect**: The prompt requested basic randomization without explicit operational modes or distribution weights. Predicted that independent 1-bit uniform randomization (wr_en, rd_en $\in \{0, 1\}$) would induce a symmetric 1D random walk centered near 50% occupancy, starving the boundary states (count == 0 and count == DEPTH) and leaving corner-case crosses unhit. 

### 2.3 Empirical Evidence
Executing a standalone CLI test of the proposed item:
```bash
python -c 'from crv.fifo_item import FifoSeqItem; item = FifoSeqItem(); item.randomize(); print("Randomized txn:", item.to_txn())'
```
Output: 
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/opt/course/cocotb-env/lib/python3.12/site-packages/vsc/rand_obj.py", line 78, in __init__
    super().__init__(*args, **kwargs)
  File "/home/net/tu340511/EEE4701/craft-vv-student/code/tb/fifo/crv/fifo_item.py", line 12, in __init__
    self.wr_data = vsc.rand_uint_t(WIDTH)
                   ^^^^^^^^^^^^^^^
AttributeError: module 'vsc' has no attribute 'rand_uint_t'. Did you mean: 'rand_int_t'?

### 2.4 Fixes & Verification
1. Type Resolution: Replaced vsc.rand_uint_t(WIDTH) with vsc.rand_bit_t(WIDTH) and control flags with vsc.rand_bit_t().
2. Payload Bounding: Added explicit range constraints on write payload words: self.wr_data in vsc.rangelist(vsc.rng(0, MASK)).
3. Distribution Tuning: Acknowledged the structural deficit of memoryless single-cycle transactions; isolated CRV execution into seeded regression runs paired with structured pre-conditioning phases to guarantee boundary dwell time.   
4. Verification: Verified standalone object creation and constraint solving via CLI:
python -c 'from crv.fifo_item import FifoSeqItem; item = FifoSeqItem(); item.randomize(); print("Randomized txn:", item.to_txn())'
---

## 3. Log Entry 2: Functional Coverage Model & Database API
### 3.1 Prompt Given
"Draft a functional coverage model in crv/coverage.py using cocotb-coverage covering wr_en, rd_en, count, flags, and command/state crosses, plus a summary reporting function."

### 3.2 Prediction Before Running
1. API Halting Defect: Expected hallucinated helper properties on the coverage container object (e.g., calling .summary directly on coverage_db).
2. Bin Interval Parsing: In cocotb-coverage, tuple syntax like (1, 2) or (3, DEPTH-2) is frequently evaluated as literal tuple values rather than integer intervals, leading to dropped bins.
3. Stimulus Distribution Skew: Uniform pseudo-random coin tosses (50% write, 50% read) naturally equilibrate the FIFO near 50% occupancy. Predicted that raw CRV would leave extreme boundary states (count == 0, count == DEPTH) and their associated cross products uncovered.
4. Sampling Race Condition: Sampling coverage post-clock would evaluate post-transition state rather than the pre-condition cross under which the command was issued.

### 3.3 Empirical Evidence
A. Database API Crash
Running make aborted at simulation end:
File "/home/net/tu340511/EEE4701/craft-vv-student/code/tb/fifo/crv/coverage.py", line 53, in report_fifo_coverage
  summary = coverage_db.summary
            ^^^^^^^^^^^^^^^^^^^
AttributeError: 'CoverageDB' object has no attribute 'summary'

B. Coverage Gaps Under Pure Uniform CRV
After patching the print method, the coverage report plateaued at 62.50% (30/48 bins):
================ FUNCTIONAL COVERAGE SUMMARY ================
  top                           : 30/48 ( 62.50%)
  top.fifo                      : 30/48 ( 62.50%)
  top.fifo.wr_en                : 2/2 (100.00%)
  top.fifo.rd_en                : 2/2 (100.00%)
  top.fifo.count                : 3/5 ( 60.00%)
  top.fifo.flags                : 3/3 (100.00%)
  top.fifo.cross_cmd            : 4/4 (100.00%)
  top.fifo.cross_cmd_x_count    : 8/20 ( 40.00%)
  top.fifo.cross_flags_x_cmd    : 8/12 ( 66.67%)
=============================================================

C. Scoreboard Desynchronization
Attempting to advance an extra clock cycle inside the monitor to re-sample state desynchronized the reference model: AssertionError: Count mismatch: DUT 3 != Model 2 (wr=1, rd=0, data=0x99)

### 3.4 Fixes & Verification
1. API Repair: Iterated directly over coverage_db.items() to extract item.size and item.coverage, calculating exact percentage coverage.
2. Explicit Bins: Defined discrete integer bins [0, 1, 2, 3, 4, 5, 6, 7, 8] with labeled intervals (empty, low_1, low_2, mid_3, ..., full_8).
3. Non-Advancing Falling-Edge Sampling: Implemented monitor.sample_now() to sample pin states immediately at the falling clock edge concurrently with transaction driving, capturing command-state crosses without consuming clock steps.
4. Boundary & Cross Sweeps: Added structured boundary sweeps across all occupancies 0..DEPTH, continuous empty/full soak phases, and burst fill/drain sequences prior to 2,000 cycles of CRV.

## 4. Final Measured Results
### 4.1 Functional Coverage Closure
Running make verified 100% closure across all single points and crosses:
================ FUNCTIONAL COVERAGE SUMMARY ================
  top                           : 68/68 (100.00%)
  top.fifo                      : 68/68 (100.00%)
  top.fifo.wr_en                : 2/2 (100.00%)
  top.fifo.rd_en                : 2/2 (100.00%)
  top.fifo.count                : 9/9 (100.00%)
  top.fifo.flags                : 3/3 (100.00%)
  top.fifo.cross_cmd            : 4/4 (100.00%)
  top.fifo.cross_cmd_x_count    : 36/36 (100.00%)
  top.fifo.cross_flags_x_cmd    : 12/12 (100.00%)
=============================================================

### 4.2 Mutation Testing Kill Score
Running PYTHONPATH=../../lib python -m craft_mutate.mutate --tb . --pool mutants_released.yaml

[baseline] running clean fifo.sv through fifo ...
  clean RTL: 1 tests passed.

  [found  ] full_offbyone        (test-failed)  -- full asserts one entry too early (cnt == DEPTH-1)
  [found  ] empty_offbyone       (test-failed)  -- empty asserts one entry too early (cnt == 1)
  [found  ] ignore_full          (test-failed)  -- writes are accepted even when full (overflow)
  [found  ] ignore_empty         (test-failed)  -- reads are accepted even when empty (underflow)
  [found  ] count_wr_dec         (test-failed)  -- a write-only cycle decrements the count
  [found  ] rd_data_wrptr        (test-failed)  -- rd_data reads from the write pointer instead of the read pointer
  [found  ] mem_corrupt          (test-failed)  -- stored data is corrupted (+1) on write
  [found  ] wrptr_wrap_early     (test-failed)  -- write pointer wraps one slot early

==== found/total = 8/8  =  100.0%  (threshold 90%) ====

AI Links: https://share.gemini.google/dz9VplFkPhtP / https://share.gemini.google/dTBQnr1b40uY 