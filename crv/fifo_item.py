"""Constrained-random FIFO transaction class using pyvsc."""

import vsc
from tb.driver import FifoTxn, WIDTH, MASK


@vsc.randobj
class FifoSeqItem:
    def __init__(self):
        self.wr_en = vsc.rand_bit_t()
        self.rd_en = vsc.rand_bit_t()
        self.wr_data = vsc.rand_bit_t(WIDTH)

    @vsc.constraint
    def data_c(self):
        self.wr_data in vsc.rangelist(vsc.rng(0, MASK))

    def to_txn(self) -> FifoTxn:
        return FifoTxn(
            wr_en=int(self.wr_en),
            rd_en=int(self.rd_en),
            wr_data=int(self.wr_data),
        )