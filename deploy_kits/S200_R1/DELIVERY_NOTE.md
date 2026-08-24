# S200_R1 — D338 past-day presence correction (kit delivery note)

**What it does.** The day page (`/register/?d=YYYY-MM-DD`) gains a doctor-only
card, "Past-day presence correction (D338)", listing every machine-absent staff
member for that date with an in-time box (prefilled with the shift start —
overtype the real arrival) and a compulsory reason. Saving writes an
already-approved present-request in your name; the whole existing stack
(machine_day, att_month_report v2.6 synthetic punches, the salary engine,
Sheet 1's * mark) then treats the day as present. Staff self-requests remain
today-only (D334). Guards: approver-only (`SR_PRESENT_APPROVERS`), no future
dates, machine must have NO punch that day, one correction per staff-day,
no clinic holidays, feed must be readable. Audit row on every save.

**Pin move.** `staff_register.py` `124c6eb2c5dc03055c70ac427c8347bb` (v0.7)
→ **`e13059023b7b57fba170cb29db933119`** (v0.8). One file; no schema change,
no migration, no data write at install. Offline: py_compile clean · pyflakes
clean (the one pre-existing note unchanged) · FULL selftest GREEN including
the new D338 block (route 403 for makers · save · synthetic punch · five
guard refusals · card visible to approver, hidden from maker · grid pill).

**Install (transcribed, not from memory):**
1. PC: double-click `PUBLISH_ALL.bat` (commits `deploy_kits/S200_R1/`).
2. VPS: `cd /root/deploy/repo && git pull`
3. VPS: `bash /root/deploy/repo/deploy_kits/S200_R1/INSTALL.sh`

Expected output: `register SELFTEST OK` · `active` · the DONE line with the
new pin. Any red restores the backup automatically and nothing is half-installed.

**Known condition after install:** `verify_live_pins.py` against
`live_pins_S199close.txt` will show RED drift **exactly 1** on
`staff_register.py` — the box right, the list one build behind (the F-134
stale-list shape). The S200 close regenerates the list; do not "fix" anything.
