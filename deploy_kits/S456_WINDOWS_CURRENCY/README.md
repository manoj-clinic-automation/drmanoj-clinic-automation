# S456_WINDOWS_CURRENCY — session 292, 03-Oct-2026 (F-700, F-694)

**Why.** On 03-Oct the owner learned from a photograph of a Windows Update screen that the reception PC's Windows had had no security fix since November 2025. The rule that came out of it: *the kit that sets a PC up also reads how current its Windows is, and says so on the health page.*

**And the owner's correction of 03-Oct, in the same file:** *"you have only mentioned the consultation report."* Reception downloads **two** files from Docterz every evening — the consultation report (Day Revenue) and the follow-up log (the follow-up tracker and the Callback Tracker's follow-up list). The row named only the first; the second went undownloaded from 7 July to 2 October without a word on the health page. The row now names both with the time each was last downloaded (the newest across the PC's two folders) and is `warn` the next morning when a clinic evening was missed for either (Sundays skipped unless `pipeline.clinic_sunday` is 1). This part needs no change on the PC.

**What it changes.**

| where | file | from → to | what |
|---|---|---|---|
| server | `/root/finance/reception_door.py` | `d0a79231` (S453) → `built/reception_door.py` | `reports_note()` + `windows_note()` + the last branch of `health_row()`: the *Reception PC* row names both Docterz reports and adds the PC's own words about its Windows. More than 75 days without a cumulative update → the row is `info` (*Worth knowing*), says since when, and the hint says it is the owner's decision. Never `warn`. |
| reception PC | `reception_agent.py` | `a87b129b` (S453.1) → `d3d4b67b` (**S456.1**) | `windows_state()`: `CurrentVersion` (product, release, build.UBR), the `Package_for_RollupFix` package of this build under *Component Based Servicing* (its install day), and the date of `ntoskrnl.exe`. Registry and one `stat`; no PowerShell, no Windows Update call; cached six hours; never raises. The heartbeat gains `windows`, the text heartbeat a `WINDOWS :` line. |
| repository | `deploy_kits/S448_RECEPTION_AGENT/` (the living kit), `deploy_kits/PC_KITS/reception/kit.zip` + `KIT_INFO.txt` | — | the agent, its tests (158 checks), `MD5SUMS.txt`, `README_REINSTALL.txt` (A.1a the Wi-Fi driver, F-693; C.7 this reading). |

**Not touched:** `finance_app.py`, `pc_kits.py`, the portal, the database, any setting.

**Proved before it was built on.** The reading ran on the reception PC itself as a signed read-only job (j41, 03-Oct 10:52 IST, 0.02 s, user `dell`): `Windows 10 Home Single Language 22H2`, build `19045.6466`, system files dated `2025-10-15`, cumulative update installed `2025-11-12`.

**The owner's line (one line; it carries its own pull, F-464):**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S456_WINDOWS_CURRENCY/install_S456_WINDOWS_CURRENCY.sh
```

It takes the build lock (`/root/deploy/.claude_code_build.lock`, released on every exit — F-694), holds `reception_door.py` to its S453 pin, walks the new file beside the live one (41 checks: the trouble rows read as before; both reports named; the Windows words appear only when the PC sends them; RED on its negative control), backs up to `.bak_S456_d0a79231`, places, restarts `clinic-finance` (about 8 seconds), checks the doors and the journal, and puts the old file back on any red. `DRY=1` in front of `bash` places nothing.

**Then, by a signed job at 08:30 on a clinic day:** the agent S456.1 through the agent's own update path (compiled first; the guard puts the old one back if the new one dies). Until then the row carries the two reports and no Windows words.

**Undo:** `\cp -p /root/finance/reception_door.py.bak_S456_d0a79231 /root/finance/reception_door.py && systemctl restart clinic-finance`. The agent: the guard's `.prev`, or the S453.1 file from `git`.

**Settings (optional, none written):** `reception.windows_stale_days` (default 75) · `reception.report_missed_evenings` (default 1).
