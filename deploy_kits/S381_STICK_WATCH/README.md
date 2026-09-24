# S381_STICK_WATCH — exports saved to the pen drive are captured (Sanjeevni, session 281, 24-Sep-2026) · F-617

**The owner, 24-Sep, ~07:40 IST:** "I just exported a report from Marg and now it is saving to the pen drive which is connected to the medical PC in the root and not to the previous location … E:\ — just check and confirm."

**Checked:** it was NOT being picked up. The medical PC's heartbeat of 07:36 IST: the watcher watches `D:\MARGERP\users`, `D:\MARG REPORTS`, `C:\Users\Public\MARG`; 0 captures today, newest 23-Sep 12:50. `E:\` is the Marg backup stick (`medical_agent.py` BACKUP_STICK) and nothing looked at it.

**The change** — `marg_watch.py` 9f0bf9c4 (S259) → **f39ce036**:
- On the medical install only (the file running from `D:\SendToClinic`), the **top level of `E:\`** is swept on the watcher's 5-second safety poll, beside the three folders it already watches.
- Only `.xls` / `.xlsx` / `.pdf`, only files **written in the last 24 hours**, **never a subfolder**. Marg backups (`.mbk`) and anything older on the stick are never read, so they can never be sent.
- No event hook on the removable drive; a stick that is not plugged in is skipped quietly.
- Everything else byte-for-byte as S259: the three folders, event capture, dedup by content, the off switch, the pusher. `medical_agent.py` untouched. On manojz (its own copy against the share) nothing changes.
- Selftest 12/12 (6 old + 6 new: fresh top-level file seen; older than a day not; subfolder not; .mbk never; absent drive skipped; a sweep captures the fresh export).

**Delivery:** the Drive kit channel — the new file placed by the assistant in `H:\My Drive\Clinic Data Archive\ToMedical\_kit\marg_watch.py` (manojz; the owner granted the folder 24-Sep). `marg_watch.py` is on the agent's built-in list: the agent compile-checks it, installs it to `D:\SendToClinic\marg_watch.py`, and restarts the watcher. No KIT_MANIFEST line needed or written.

**Undo:** put `deploy_kits\S259_OFF_SWITCHES\medical\marg_watch.py` (9f0bf9c4) back into the same `_kit` folder; the agent reinstalls it and restarts the watcher.
