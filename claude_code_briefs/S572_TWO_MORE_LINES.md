# S572_TWO_MORE_LINES — brief for Claude Code (v1)

*Written 16-Oct-2026 by the Sanjeevni chat (session 316) at the owner's word (13:47 IST: "Add these two to Amir's work"). Data only — exactly as S569 Part B did (read `claude_code_briefs/REPORT_S569.md` §B and its `add_jobs_s569.py` if kept, and follow the same steps). No code change. Times IST.*

## 0 · For the owner
The stock check of the 6-Sep count gave its verdict at about 13:2x today: 4 of 170 medicines in Amir's 30 stage-C vouchers do not agree with Marg's closing of 15-10. Two (KT ROS DT, VINBACTUM DS) are already on Amir's card (S569). This kit puts the other two there, under *Ek baar ke kaam*, with a *Kar diya* button:
- **FOLITRAX 15 MG TAB** — his voucher 8 (Marg no. 13) said issue 6; Marg moved 0.
- **OSTOVAXL DM** — his receive voucher 6 (Marg no. 6) said receive 21; Marg moved +25, so 4 too many went in.

## 1 · Numbers and pins
Kit **S572_TWO_MORE_LINES** (board `_numbers` v456 → v457, PLANNED line). Project: Sanjeevni. Writes: two `amir_job` rows in `/root/finance/finance.db` (backup first by the backup API, `finance.db.bak_S572_<stamp>`). Read only: `amir_day.py`, `stock_app.py`. No restart. The build lock.

## 2 · The rows (kind `tap`, created_by `S572`, show_from = now, the rest NULL; audited `job_added` by `system`, `{"kit": "S572", "owner_word": "16-Oct 13:47"}`)

| key | subject | text_hi | sub_hi |
|---|---|---|---|
| `fix:S572:FOLITRAX 15 MG TAB` | FOLITRAX 15 MG TAB | `FOLITRAX 15 MG TAB — Marg mein STOCK ISSUE kijiye: 1 patte + 1 goli` | `6 Sep ki stock ginti · voucher 8 ki line` |
| `fix:S572:OSTOVAXL DM` | OSTOVAXL DM | `OSTOVAXL DM — Marg mein STOCK ISSUE kijiye: 4 goli` | `6 Sep ki stock ginti · receive voucher 6 ki line` |

**Before inserting, assert on the live box (read only):** `/api/pad/hub/1` `proof.C.wrong` names FOLITRAX 15 MG TAB with need −6, moved 0, and OSTOVAXL DM with need +21, moved +25 (packing 1*5 and 1*10); the quantity words are `qty_words` for 6 units of 1*5 (`1 patte + 1 goli`) and 4 units of 1*10 (`4 goli`) — print what `qty_words` returns and use it if it differs. If either line is no longer wrong (Amir already corrected it), do not add that row; say so.
Only "do this" words (D708). The S569 rows stay untouched.

## 3 · Check and report
Render `/finance/amir` as `amir` on a scratch copy (walk-only session): the four lines under *Ek baar ke kaam* (S569's two + these two), nothing else on his card changed. `claude_code_briefs/REPORT_S572.md`: 3 plain lines on top; the rows with ids; the backup. Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
