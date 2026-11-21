# S915_DOCTERZ_TAKEN_NOTICE — a message when the server takes a Docterz report

*The parent · S496 · 21-Nov-2026.*

| file | pin | what changes |
|---|---|---|
| portal/docterz_taken_notice.py | NEW 0c301689 | Every 5 minutes (cron `2-59/5`, its own lock): one message to the owner for the Docterz reports the server took since the last look — consultation report (day, patients), follow-up log (its day, the call days it covers, rows), clinical data report (the period it covers) — each naming **where it came from**: the reception PC, your PC (manojz), or the Docterz reports page. A report held back says "NOT used" and why. Every message ends with how far the clinical data reaches and the day to export from next. Duplicates, not-sitting marks and stray files say nothing. First run: notes the newest row, sends nothing. Read-only on finance.db; no names or numbers in a message. Off: `/root/finance/_off/DOCTERZ_TAKEN_NOTICE_OFF`. |
| portal/docterz_missing_alert.py | 5476038d → 226ef57b | Wording only: "has not come from reception **or your PC (manojz)**". |

## Proof
- `walk_s915.py` (made-up store): **WALK 19/19**; control red 7/19.
- S811's walk with the new words: 67/67 on the new alert, red on the live one.
- The probe on the live store at install; rehearsal: dry, install, again, undo, red rollback — green.
- Cold review: its SHOULDs built in (own lock on the cron line; the store read with a timeout).

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s915kit && cp -rp /root/deploy/repo/deploy_kits/S915_DOCTERZ_TAKEN_NOTICE /tmp/s915kit && bash /tmp/s915kit/install_S915_DOCTERZ_TAKEN_NOTICE.sh
```
