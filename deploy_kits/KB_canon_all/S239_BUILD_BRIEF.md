# S239 BUILD BRIEF — what was built, what is live, what is next (S239 close, 11-Sep-2026)
**The one document to read instead of the six S239 papers.** `START_HERE_SESSION_240` carries the full
context for the next chat; this brief is the as-built record.

## 1 · Kits (all in `deploy_kits\`, every SUMS gate verified from inside its folder)
| kit | what it did | live after |
|---|---|---|
| `S239_DOCTERZ_PICKUP` | Docterz auto-pickup on the tracker PC (D455): archive, per-day decisions, `run_daily`, VPS upload + patient push for the latest day, Day_Tenders rebuild; rev 2 adds `--refresh-latest`; `revenue.py` S223 fix; `push_followups_today.py` name-date pick (D456) | PC `docterz_pickup.py` `d117786f…` · `revenue.py` `5d8f2a71…` · `push_followups_today.py` `74122185…` · task DocterzPickup (5 min) |
| (owner sed line) | VPS `/root/wa/push_followups_vps.py` picks the latest day by the date in the name | `PATCHED`, backup `.bak_S239`; **md5 unread** |
| `S239_STAFF_PWA_P1` · `S239_STAFF_PWA_P1b` | tile grants v9, then v10 by one owner line (login spellings, F-427); P1b is the record | `tile_grants.json` `812cbbc6…` |
| `S239_SHEET2_OT` | Money page fines table: leave-days column out; late min, OT (min, ₹), cover in — display only | `salary_policy.py` v1.13 |
| `S239_SHEET2_COVER1` | cover as one column `₹ (days)` — display only | v1.14 |
| `S239_SHEET2_PARTTIME` | part-time (`dates_only_staff`) out of fines/no-punch tables; days-punched list — display only | v1.15 |
| `S239_PARTTIME_PAY` | part-time pays no leave charge / absence fines (owner chose "1"); Amir ₹2,295.08 → ₹2,500.00, all others identical | **v1.16 `c7577174…`** |
| `S239_PORTAL_F242` | F-242 + AF-12: SSO-only in broker mode; device cookie cleared, never planted; `/portal/logout`; sign-out-everywhere doctor-only; staff "Sign out of this phone" | `portal.py` **`ed558b36…`** |

**Backups on the VPS:** `/root/portal/tile_grants.json.bak_S239_v8`, `.bak_S239_v9` ·
`/root/staff_register/salary_policy.py.bak_S239_*` (four) · `/root/portal/portal.py.bak_S239_F242_20260911_113255`
· `/root/wa/push_followups_vps.py.bak_S239`. **On the PC:** `revenue.py.bak_S239_a15d776e`,
`push_followups_today.py.bak_S239_7693a29a`, `D:\Downloads\DocterzArchive\_outputs_before_run\`.

## 2 · Measured, not built
- **Clinical data report** (`claude/S239_CLINICAL_DATA_REPORT_MEASURED.md`): augments, never replaces, the
  consultation report (all money component columns zero); follow-up log kept (Appointment ID); diagnoses
  96.6 % mappable; 23 % of prescriptions show no Sanjeevni sale by next day. Build plan in six steps,
  order the owner's — **he said later.**
- **Sanjeevni restart** (`claude/S239_SANJEEVNI_RESTART_PLAN.md`): eight steps with Amir's app at 6–7,
  five clubbed kits, inputs named. **Items 1–3 approved for S240** (D462).

## 3 · The owner's rulings (full text: Archive §S239)
D455 pickup rules · D456 latest day by name · D457 staff app phase 1 · D458 Money page fines table ·
D459 part-time staff · D460 the August lock sequence · D461 portal sign-in · D462 Sanjeevni items 1–3 next.

## 4 · Next, in order
1. The four checks of `START_HERE_SESSION_240` §2 (August step · Amir's exports · the VPS picker hash ·
   the pickup heartbeat).
2. **Sanjeevni items 1–3** (§3 there), then 4–8 in the plan's order.
3. When he asks: Docterz Ask 2 build; the staff-money remainder.

## 5 · Findings (Fault Register v2.71)
F-420 Day_Tenders duplicates (closed) · F-421 call list by mtime (closed) · F-422 total-row stop
(assistant's, closed) · F-423 workbook name collision (open, mitigated) · F-424 PHI Drive marker (open,
his ruling) · F-425 diagnosis seeder silent zero (open) · F-426 stale preview (assistant's) · F-427
guessed logins (assistant's) · F-428 "ready to lock" (assistant's). Closed: F-419, F-242, AF-12.

*S239_BUILD_BRIEF · 11-Sep-2026.*
