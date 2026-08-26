> ## ⚠ RETIRED — DO NOT ACT ON THIS DOCUMENT
> **Retired on 26-Aug-2026.** Successors: **`MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` §3.2**
> (md5 `579ea885e440e76af73de3ecc4542d71`) for the medical-PC pins, and the **`KB_Register`
> live-file table** — `KB_Register_v5_54_S202.md` (md5 `8fede84d7126e13fca17418e449f9d0a`) — for
> everything on the VPS and manojz.
> Every VPS pin recorded here has moved many times since S195. Its one durable item, the
> `SEND_TO_CLINIC.bat` pin, was **independently re-measured on the medical PC on 26-Aug-2026** and
> is carried in master §3.2 — so that fact now has two sources for the first time.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S195 FINAL LIVE PINS — supersedes every earlier pin list in this session
**22 Aug 2026, 02:05 IST**

## VPS
- **`finance_app.py` = `e3a4ba79c2e060bcebe11c075bdbbc7b`**  ·  **SMOKE 573/573**
  Chain today: S194E `d2863c30` → S195_ENTRY `85df28fe` → S195_NCSCAN `f25ed489`
  → S195_HEALTH `fe596b29` → filing-grace `89ab3e8e` → flags-as-info `e3a4ba79`.
- `finance_ui/finance_daily.html` = `20efc5caa664c9b96be23bb66866d21c`
- `FINANCE_MARG_TOKEN` now declared in `/etc/systemd/system/clinic-finance.service`.
  **This was the crisis**: it had lived somewhere transient, so any restart killed the
  sender. Now durable.
- Backups: cron `5 1 * * *`, verified nightly, **restore proven** (126 days, 3141 items).

## Medical PC — `D:\SendToClinic`
- `GUARD_AND_SEND.bat` — the ONE icon. Finds by content → guards → sends → parks
  failures in `NEEDS_UPLOAD\`.
- `find_sale_report.ps1` — the content search, in its own file (embedded in a batch
  if-block, cmd mangled the escaped pipes and it silently found nothing).
- `SEND_TO_CLINIC.bat` — untouched proven v3 `e19a8a777ac22fe75a242f1eb9762185`.
- `marg_export_macro_v3.ahk` — PARKED. `GuardExpect` currently `"any"`; set back to
  `"yesterday"` for daily use. Next step is one line:
  `(Get-Item D:\SendToClinic\AutoHotkey64.exe).VersionInfo.FileVersion` — if 1.x,
  install AHK v2 (`AutoHotkey_2.0.26.zip` is in manojz `margsync`).

## manojz — scheduled task "Marg pull from medical", every 10 min
`D:\Downloads\margsync\MargPull\PULL_FROM_MEDICAL.bat AUTO` does three things:
1. captures + identifies every Marg export → `margsync\MargArchive` (named by the
   business date inside the file) + `index.csv`
2. mirrors the medical working folder → `margsync\medical_SendToClinic`
   (logs, alerts — this is what made tonight's 401 diagnosable from here)
3. offsite → `H:\My Drive\Clinic Data Archive\MargArchive` (drmka.ortho Drive)

## Health surfaces (S195_HEALTH)
- `GET /finance/health` (checker) · `GET /finance/api/health`
- `api_tile_meta`: a red check replaces the CHECKER's portal tile subtitle, so the
  warning reaches the portal home **with no change to the portal app**.
- `FINANCE_FILING_DUE_HOUR` (default 12): yesterday is "today's job" until then.
- **Flags are `info`, never `warn`** — they always exist, so letting them drive the
  tile would light it permanently and turn the warning into wallpaper.

Checks: Marg push freshness + pending applies · days filed (Sundays skipped) · books
vs last physical count · flags (informational) · newest verified backup.

## Two test lessons (F-106 shape) — worth remembering
1. Three checks asserted the month's non-cash was EXACTLY `"350.00"` with exactly 2
   heads. True only while no real no-payment bills existed. Darpan filed the first
   (₹3,000, 20 Aug) and all three went red **with no code change**. Now they assert
   the rule (`>=`, "included"), and the tile check asserts the tile AGREES with the
   month endpoint — stronger than the frozen number it replaced.
2. The router selftest used a real report name as its "unknown" example and went red
   the moment that report was onboarded.
**Tests must describe rules, not snapshots.**

## Owner actions outstanding
1. **Apply the 21-Aug push** (37 bills, ₹49,181).
2. **Rotate both tokens** — cron + Marg were exposed in chat.
3. **18 Aug**: total 23,879 → **25,176** (his copy AND Marg agree; the entry was short
   ₹1,297 — he counted right).
4. **17 Aug**: **₹20,000** as a salary advance → Staff Ledger, per the 16-Aug plan
   (recover 8k from Aug salary, then 4k monthly, against his scanned application).
5. After 3+4 the drawer should read **₹175,201** = Dr Bhawna 1,56,235 + owner 18,963
   + Darpan's real ₹3. The health page's "Cash position" gap should close with it.

## Owed engineering
- Selftests for the two health endpoints (smoke did not grow with the feature).
- DB off-box pull (`S195_DBPULL`) — needs an SSH key manojz→VPS; local-only until the
  copy is encrypted (passphrase decision outstanding).
- Router signatures for Labmate / Docterz / stock / purchase — one sample of each.
- `MARG_DAY_NOT_FILED x3` — likely the 17/18/19 Aug pushes that arrived before their
  days were filed; worth a look.
