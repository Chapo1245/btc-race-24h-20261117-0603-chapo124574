# btc-race-24h-20261117-0603 — Deep-Dip Bounce Bot

[![owner](https://img.shields.io/badge/owner-Chapo1245-blue)](https://github.com/Chapo1245)
[![bounty](https://img.shields.io/badge/make.fun-btc--race--24h--20261117--0603-green)](https://make.fun/c/btc-race-24h-20261117-0603)

A Python bot that trades Coinbase Wrapped BTC (cbBTC) against USDC, minute by
minute, in the make.fun bars replay. Long only, one position, full size,
deterministic. Standard library only, plus the kit's Python SDK shim vendored
byte-for-byte under `vendor/`.

## Strategy

This dev window is a mean-reversion market: trailing returns have negative
forward returns (momentum loses), while closes 110+ bps under their 60-bar
high bounce a median +100 bps over the next two hours.

- **Entry:** the latest close is at least 110 bps below the highest bar high
  of the last 60 bars. Buy with all cash.
- **Exit:** take profit at +200 bps above the entry close, or sell everything
  300 bars after the buy was decided, whichever comes first.
- **No stop-loss:** every stop level tested on the dev window either never
  fired or fired and re-bought into the same dip for a worse result.

## Dev-window result (local replay, exact harness fill math)

| Net PnL | Trades | Max drawdown | Fees | Net PnL at 2x fees |
|---|---|---|---|---|
| **+$20.14** | 6 fills (3 round trips) | 1.73% | $2.44 | **+$16.48** |

Buy-and-hold on the same window makes +$1.07; the house momentum and
EMA-cross baselines lose. Two independent runs produce byte-identical action
logs (deterministic).

## Files

- `main.py` — the bot (entrypoint)
- `vendor/makefun_bars.py` — the kit's Python SDK shim, byte-identical copy
- `LICENSE` — MIT

## Run locally

The kit grades the bot with `node cli/makefun.mjs grade-local --kit . --bot <repo>
--driver docker` (Python runs only inside Docker). Without Docker, the
replay harness in the build directory reproduces the official fill math to
the cent (buy-and-hold: +$1.067187, matching the official grade exactly).
