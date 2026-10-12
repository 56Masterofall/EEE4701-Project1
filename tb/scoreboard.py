"""FIFO Scoreboard: verifies DUT behavior against the FifoModel oracle."""

from tb.driver import FifoTxn
from tb.monitor import FifoSample
from models.fifo_model import FifoModel

WIDTH = 8
DEPTH = 8

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
