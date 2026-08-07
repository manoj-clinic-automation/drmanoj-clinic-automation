# START_HERE — SESSION 154 (generated at S153 close-out, 2026-08-07)

Session counter: **this is Session 154.** Next free: **D257 · F-49.**

## Phase 0 (D247) — before any work

1. Open **`CANONICAL_MANIFEST.md`** and **verify every row by md5** — all tiers, hash-compare only. Any mismatch → HALT and reconcile (D172/D188).
2. **Read Tier 0 only:** this file · `KB_Register_v2_6_S153.md` · `HANDOFF_RUNBOOK_2026-08-07_Session153_v91.md`. No open incident.
3. Tier 1 on demand; Tier 2 hash-verified, never read in the loop, edit only by waiver (D34).

## Session-open state checks (S154-specific)

- **`att_month_report.py` on the VPS:** v2.4 `608f2a90bf9ff65f196ac4f2f13c00bb` was installed at S153; **v2.5 `e64cad19d135618dec1413553e6bdc80` was delivered but its install was NOT confirmed.** First action = complete/confirm the v2.5 install (md5 + `--selftest` + July rerun). If the owner already installed between sessions, one `md5sum` settles it.
- `staff_master.csv` on VPS should read `3b1ebcb1e339fdcdb8b47389ee206108` (v2, roster columns). The clinic-PC workbook + `build_staff_master.py` do **not** yet carry the two new columns — any rebuild before backlog item 3 completes would silently drop them.
- **August is the first billing month** (July was diagnostic-only, D256k). The run lands ~01-09 with the two-pass review loop.
- Notion catch-up spans **S151–S153** (connector absent three sessions).
- Cold kit is **due**.

## Backlog

Live backlog = **Runbook v91 §2** (item 1 = v2.5 install; item 3 = workbook shift-time pass gates the Aug run's truthfulness; item 5 = D255 maker-checker before 01-10).

*This file supersedes START_HERE_SESSION_153. The evergreen START_HERE_PROMPT_v5 remains the custom-instructions template.*
