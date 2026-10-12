# S535_PUNCH_SOURCE_WATCH — step 1 of 2 for closing the punch listener: it only records

Kit of session 305 (the parent), 12-Oct-2026. Numbers from the System Board (`_numbers` v372): kit S535, D713.

**The owner, 12-Oct 05:33 IST:** *"close it only if it is safe and keeps attendance running glitch free."* His word waives
the attendance freeze (D247) for this change only.

The listener on port 8041 saves anything shaped like a punch, from anyone. Closing it safely needs one mark that is on
**every** genuine punch — an address can change with the clinic's internet line, so it is not assumed. This kit only
**records**: for every punch (and the first 30 other requests per sender per day) the listener appends who sent it —
the address and the machine's own headers, key- or password-named ones masked — to `/root/attlistener_sources.jsonl`.
Every reply to the machine and every row of `punches.csv` stays exactly as today; a failure of the watch is swallowed.

Each night at 01:25 `/root/att_source_summary.py` (read-only — it need not be run by hand) writes
`/root/finance/punch_sources_summary.json`: the addresses, the headers on punches, whether one header value covers every
punch, and whether every new `punches.csv` row has its source line. The 01:35 bundle carries it to the owner's PC.

**Step 2** — refuse a stranger's punch, keep it aside in its own file (never deleted), tell the owner — is built only
after a week shows one stable mark, and only then.

## Proof
`walk_s535.py` runs the old and the new listener side by side on spare ports with the machine's own request shape:
replies identical, `punches.csv` identical apart from `received_at`, one source line per punch, masked headers, the cap,
the watch failing changes nothing (negative control), the summary finds the mark and reports a row with no source line
(negative control). The installer runs the same walk on the VPS's own Python before placing anything.

## Install
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S535_PUNCH_SOURCE_WATCH/install_S535_PUNCH_SOURCE_WATCH.sh
```
## Undo
The installer prints it: the listener's backup back, restart, the cron line removed.
