# S917_OLD_SLIP_NUMBER — a 14-Nov X-ray slip whose number was taken

*The parent · S498 · 21-Nov-2026.*

**What happened.** A patient's X-ray paper of 14-Nov (evening) carries **1546**. On 15-Nov Shavez re-wrote another patient's 9-Nov X-ray slip (the first, 1481, had been taken off); the old-day form then filled in *today's next number* — 1546 — and it was saved on the 9-Nov patient. The 14-Nov paper's own 1546 could then never be written ("pehle se likhi hai"). S912 (installed 07:14 today) already stops the form filling today's number on an old day.

| part | what changes |
|---|---|
| one-off `s917_fix.py` (data, one transaction, audited) | slip 1190 (9-Nov) **1546 → 1481**, that patient's own 9-Nov paper's number (slip 1017 at 1481 stays voided, as history). The discount ask still waiting on the voided 1481 is withdrawn. **1546 is free** for the 14-Nov slip. Every precondition read first; anything else found = nothing changed. Database backed up before. |
| `finance/slip_log.py` 5cfaf728 → TO | An **old day's** parchi whose number is **past a later day's saved parchi** (same book) is held: *"Parchi N … ke baad ka number hai — yeh … ki parchi nahi lagti … 'Haan, yahi number'"*. The tick (both the form and the desk already show it) lets it through. Today's slips never asked. |

**After the install:** Shavez writes 1546 on 14-Nov from the paper (X-ray form, Din 14-Nov) — its study and side are on the paper.

## Proof
- `walk_s917.py` on a copy of the 21-Nov data: **13/13** (before the fix 1546 refused; the one-off; the 14-Nov 1546 saves; the guard asks and the tick passes; today never asked; a fitting old number not asked). Live file **9/13** (red).
- S912's `walk_s912` 29/29, `walk_s840` same old/new, `walk_s844` 31/31 on the new file.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s917kit && cp -rp /root/deploy/repo/deploy_kits/S917_OLD_SLIP_NUMBER /tmp/s917kit && bash /tmp/s917kit/install_S917_OLD_SLIP_NUMBER.sh
```
`DRY=1` before `bash`: every gate and walk, nothing changed. `--undo`: the file back and the two rows back (only while 1546 is still free).
