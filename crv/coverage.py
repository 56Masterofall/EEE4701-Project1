"""Functional coverage model for Synchronous FIFO using cocotb-coverage."""

from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
from tb.driver import FifoTxn
from tb.monitor import FifoSample

DEPTH = 8


@CoverPoint(
    "top.fifo.wr_en",
    xf=lambda txn, sample: txn.wr_en,
    bins=[0, 1],
)
@CoverPoint(
    "top.fifo.rd_en",
    xf=lambda txn, sample: txn.rd_en,
    bins=[0, 1],
)
@CoverPoint(
    "top.fifo.count",
    xf=lambda txn, sample: sample.count,
    bins=[0, 1, 2, 3, 4, 5, 6, 7, 8],
    bins_labels=[
        "empty",
        "low_1",
        "low_2",
        "mid_3",
        "mid_4",
        "mid_5",
        "mid_6",
        "near_full_7",
        "full_8",
    ],
)
@CoverPoint(
    "top.fifo.flags",
    xf=lambda txn, sample: (sample.empty, sample.full),
    bins=[(1, 0), (0, 0), (0, 1)],
    bins_labels=["empty_asserted", "neither", "full_asserted"],
)
@CoverCross(
    "top.fifo.cross_cmd",
    items=["top.fifo.wr_en", "top.fifo.rd_en"],
)
@CoverCross(
    "top.fifo.cross_cmd_x_count",
    items=["top.fifo.cross_cmd", "top.fifo.count"],
)
@CoverCross(
    "top.fifo.cross_flags_x_cmd",
    items=["top.fifo.flags", "top.fifo.cross_cmd"],
)
def sample_fifo_coverage(txn: FifoTxn, sample: FifoSample):
    """Coverage sampling callback triggered per simulation cycle."""
    pass


def report_fifo_coverage():
    """Export coverage to YAML and display coverage statistics."""
    coverage_db.export_to_yaml("coverage_report.yaml")
    print("\n================ FUNCTIONAL COVERAGE SUMMARY ================")
    for name, item in coverage_db.items():
        size = item.size
        coverage = item.coverage
        pct = (coverage / size * 100.0) if size > 0 else 0.0
        print(f"  {name:<30}: {coverage}/{size} ({pct:6.2f}%)")
    print("=============================================================\n")