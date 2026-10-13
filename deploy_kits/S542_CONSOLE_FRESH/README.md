# S542_CONSOLE_FRESH — kit S542 (session 313, 13-Oct-2026)

**The owner, 07:26 IST 13-Oct:** *"check why my command console does not show the amounts. Although the 12th October amounts are showing in the relevant page of doctor's revenue ... whenever I update something through the command console, and then I come back to command console and even refresh it, then also those stale messages are not cleared."*

## The two causes, found by running the console's own builder on the 13-Oct 01:35 copy of the database

1. **₹0 for the clinic's day.** Until reception fills the counter sheet (about 08:30), the morning match stops early and carries no totals; the console took its missing Docterz figure as 0. On 13-Oct it read *Clinic ₹0* for 12-Oct while Docterz had ₹20,600.
2. **Stale lines.** The page reused a reading up to five minutes old when it was opened, reloaded or returned to; only the *as of · refresh* button asked for a new one.

## What changes

| file | from → to | what |
|---|---|---|
| `/root/finance/owner_console.py` | c09321e2 → 2b985708 | 2 counted edits: with no match yet, the clinic's day is Docterz's own day total (the Docterz Revenue page's number); with the sheet in and Docterz not yet, the sheet's total; VERSION S542 1.3 |
| `/root/finance/owner_console.html` | e6d35d88 → e0d7d62f | 2 counted edits: a fresh reading is asked for on opening / reloading and on coming back to the page (the server still makes at most one at a time, never more than once in 15 seconds) |

## Proof (S313, on manojz)

The console's own builder run as the service runs it, on a copy where the counter sheet for yesterday is taken out: 7 checks green — the Today tile and the Money line read ₹20,600 for 12-Oct (and a made-up day when yesterday is not read yet). The old files fail 4 of the 7 (they read ₹0 and reuse the old reading).

## Install — one line on the VPS

`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S542_CONSOLE_FRESH/install_S542_CONSOLE_FRESH.sh`

## Undo

`\cp -p /root/finance/owner_console.py.bak_S542_c09321e2 /root/finance/owner_console.py && \cp -p /root/finance/owner_console.html.bak_S542_e6d35d88 /root/finance/owner_console.html && systemctl restart clinic-finance`
