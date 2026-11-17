"""Deep-dip bounce bot for btc-race-24h-20261117-0603.

Strategy (long only, one position, full size, deterministic):
  * Entry: the latest close sits at least DIP_BPS below the highest bar high
    of the last HIGH_LOOKBACK bars. Mean reversion: this dev window's
    trailing returns are negative-forward (momentum loses), while closes
    110+ bps under their 60-bar high bounce a median +100 bps over the
    next two hours.
  * Exit: take profit at TAKE_PROFIT_BPS above the entry close, or sell
    everything HOLD_BARS bars after the buy was decided, whichever first.
    No stop-loss: on the dev window every stop level tested either never
    fired or fired and re-bought into the same dip for a worse result.
  * One order per reply at most; buys spend all cash, sells empty the
    position. Nothing random, no clock, no network, no files.

Protocol: agent-fun/bars-replay/v1, via the kit's Python shim (vendored
byte-for-byte under vendor/). The shim owns the wire; this file only
decides orders.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
DIP_BPS = 110
HIGH_LOOKBACK = 60
TAKE_PROFIT_BPS = 200
HOLD_BARS = 300
MAX_SLIPPAGE_BPS = 100


class DipBounce:
    """State for one run: bar-high history and the open position's entry."""

    def __init__(self):
        self.highs = []          # bar high of every bar seen, in order
        self.bars_seen = 0       # bars seen so far (decision index + 1)
        self.entry_bar = -1      # bars_seen at the buy decision (-1 = flat)
        self.entry_close = 0     # close at the buy decision

    def on_batch(self, state, batch):
        bar = state.latest.get(SYMBOL)
        if bar is None:
            return []
        close = int(bar["c"])
        self.highs.append(int(bar["h"]))
        self.bars_seen += 1

        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding is not None else 0

        if qty > 0:
            gain_bps = (close - self.entry_close) * 10000 // self.entry_close
            if gain_bps >= TAKE_PROFIT_BPS:
                return self._sell_all(state)
            if self.bars_seen - self.entry_bar >= HOLD_BARS:
                return self._sell_all(state)
            return []

        if state.warming_up:
            return []
        # Defensive: a buy that was rejected leaves entry state behind with
        # no position. Clear it so a stale entry can never linger into a
        # later position; a fresh buy always sets entry state again.
        if self.entry_bar != -1:
            self.entry_bar = -1
            self.entry_close = 0
        window = self.highs[-HIGH_LOOKBACK:]
        high = max(window)
        dip_bps = (high - close) * 10000 // high
        if dip_bps >= DIP_BPS and state.cash > 0:
            self.entry_bar = self.bars_seen
            self.entry_close = close
            return [{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    def _sell_all(self, state):
        holding = state.positions.get(SYMBOL)
        if holding is None or holding.qty <= 0:
            return []
        self.entry_bar = -1
        self.entry_close = 0
        return [{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": holding.qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]


def main():
    bot = DipBounce()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
