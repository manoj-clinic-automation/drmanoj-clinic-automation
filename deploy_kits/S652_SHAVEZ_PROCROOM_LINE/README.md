# S652_SHAVEZ_PROCROOM_LINE — Shavez's list carries *Kal ke procedures* (kit S652, session S354, 25-Oct-2026)

**Why.** Carried from the S349 close (Runbook v269 §1X): once the Scan App chat's count door was live (its S648, installed 09:04 IST
25-Oct), Shavez's *Aaj ka kaam* gets a line for *Kal ke procedures*. The owner switched that screen on for Shavez at 07:0x IST 25-Oct.

**What changes.** One fetch line, `shavez.procroom_morning`, in the shape of `shavez.day_check`: the page asks
`/scanapp/procroom/morning/api/open` with Shavez's own login; the line shows only when `open` > 0, in the door's own words
(*Kal ke procedures: N din baaki (M parchi)*), in his first section, and opens `https://followup.dr-manoj.in/scanapp/procroom/morning`.
- `/root/finance/aaj_duties.json` `90219853` (S650) → `1d085d58` — 1 counted edit (`aaj_duties.json.kit`)
- `/root/finance/aaj_seed.py` `64d9a607` (S650) → `2121947f` — 1 counted edit (his panel was never saved: the seed governs, so it arrives ON)

If the owner switches *Kal ke procedures* off for the staff, the door answers without a count and Shavez's list says one door did not
answer (by the Scan App's design: never read as "nothing waits").

**Proven.** `walk_s652.py` 3/3 on the 25-Oct database copy (read-only): the fetch line on the right door in his first section, no unread
line, every other line of every list unchanged. `--old`: 1 S652 red · 0 older red.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s652kit && cp -rp /root/deploy/repo/deploy_kits/S652_SHAVEZ_PROCROOM_LINE /tmp/s652kit && bash /tmp/s652kit/install_S652_SHAVEZ_PROCROOM_LINE.sh
```
## Undo
```
\cp -p /root/finance/aaj_duties.json.bak_S652 /root/finance/aaj_duties.json; \cp -p /root/finance/aaj_seed.py.bak_S652 /root/finance/aaj_seed.py; systemctl restart clinic-finance
```
