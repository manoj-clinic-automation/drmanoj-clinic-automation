# S454_BILL_REGISTER · part 1D — P1D_TICK_GUARD

Session 283 (Sanjeevni), 03-Oct-2026. **A fault of part 1, found while building part 2 (03-Oct ~16:30 IST).**

Part 1 appended its block to the end of `/root/finance/order_rules.py`. That block holds the order sheet's cron pass and the one reminder
of the day, and it sat below the file's `if __name__ == "__main__":` line. The cron runs the file as a script (`order_rules.py tick`, every
ten minutes 05:00–21:50). So Python ran `main()` → `tick()` → `_s454_pass()` before that name was defined: **NameError on every tick
since 12:30 IST** (`/root/finance/order_rules.log`). Inside the service (an import) nothing was wrong. Page reads still loaded sheets,
made ties and cleared lines. The cron's own work (the 17:00 reminder, tomorrow's 05:30 nightly and 09:00 preparation) would not have run.

**The fix:** the two guard lines move to the end of the file, unchanged. Nothing else changes.

| file | FROM | TO |
|---|---|---|
| /root/finance/order_rules.py | d29efa8e6425fa359ea28d38c0758ccc | 6587dc84941f4e53ccc39d0847812123 |

- `make_s454p1d.py`: the anchored move.
- `walk_s454p1d.py`: the cron's own command run as a script on scratch copies. NEW exits 0; the live file fails with the same NameError
  (the negative control). The module imported in-process exposes the same names.
- `install_S454_P1D.sh`: restarts clinic-finance only, then runs one live tick by hand, which must exit 0.
