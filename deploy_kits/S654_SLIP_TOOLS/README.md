# S654_SLIP_TOOLS — a saved parchi can be renumbered or removed; the previous book's numbers stay valid (kit S654, session S354, 25-Oct-2026)

**Why.** D789. On 23-Oct a slip was saved under 1397 when the paper said 1398; on 24-Oct a new book (1401–1800) was set, and from
that moment the system refused 1397 and 1398 everywhere — even as late entries — and offered no way to change a saved slip's number
or remove a past day's slip (*Hatao* existed only in today's list). Undoing it took a server line (S354, 13:47 IST). The owner,
18:34 IST: build only the slip tools now; the rest is deferred to observe staff discipline.

**What changes.**
- **The previous book is remembered** (`slip_book.prev_first_no / prev_last_no`, added in place on first use; filled once from the
  book size: X-ray 1001–1400, OPD 19201–19600). A new book keeps the old range. A late entry or a leftover slip with the old
  book's number saves; a number of neither book is refused and the message names both ranges.
- **On the parchi desk**, every saved OPD and X-ray/Proc row of the day shown carries **No.** (new number, reason) and **Hatao**
  (reason). Both work for any day the desk offers (today and 7 days back). No. refuses a number another saved slip holds or one of
  neither book; a *skipped* number is taken over. One's own same-day entry needs no reason for Hatao (as before). Every change is
  audited; the old number is kept in the slip's note.
- `/root/finance/slip_log.py` `93103944` → `b47a5ded` (5 counted edits) · `/root/finance/parchi_desk.py` `99b7e43b` → `db5fd07f`
  (5 counted edits). No other file. Restarts clinic-finance.

**Proven.** `walk_s654.py` **25 of 25** on a made-up slip book (a throw-away Flask app over a temp database, the clock pinned):
the previous range kept on a book change; a late entry with the old number; both doors with every refusal and the skipped-number
take-over; a slip older than 7 days untouchable; the audit; the page's buttons; the old pages unchanged. `--old` on the live files:
**16 S654 red · 0 older red**. On the 25-Oct database copy the migration yields X-ray 1001–1400 / OPD 19201–19600 as the previous
books; the next numbers are unchanged (1408 / 19844).

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s654kit && cp -rp /root/deploy/repo/deploy_kits/S654_SLIP_TOOLS /tmp/s654kit && bash /tmp/s654kit/install_S654_SLIP_TOOLS.sh
```
## Undo
```
\cp -p /root/finance/slip_log.py.bak_S654 /root/finance/slip_log.py; \cp -p /root/finance/parchi_desk.py.bak_S654 /root/finance/parchi_desk.py; systemctl restart clinic-finance
```
