# S913_PROCROOM_NEXT_DAY — Kal ke procedures: after Save, on to the next waiting day

*The parent, on the Scan App's file (PLANNED line at board v1923) · S496 · 21-Nov-2026 · built by `make_s913.py`.*

| file | pin | what changes |
|---|---|---|
| assetapp/procroom.py | 38c5bbaa → 3344e279 | Opened with no day, Shavez's morning screen opens the **oldest day still waiting** (was always yesterday, even when yesterday was done). A Save that finishes the day goes on to the next waiting day and says "Yeh din poora. Ab DD-MM ke procedures bharein (N baaki)", or "sab din poore ho gaye". Before, the same day came back looking unchanged, which read as "nothing happened". The save itself (`save_morning`) is not touched. |

## Proof
- `walk_s913.py`: **WALK 10/10**; the live file **6/10** (red).
- Rehearsal: dry, install, again, undo, undo again, red rollback — green.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s913kit && cp -rp /root/deploy/repo/deploy_kits/S913_PROCROOM_NEXT_DAY /tmp/s913kit && bash /tmp/s913kit/install_S913_PROCROOM_NEXT_DAY.sh
```
