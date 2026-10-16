# S569_PROOF_REACH_AND_TWO_LINES — brief for Claude Code (v1)

*Written 16-Oct-2026 by the Sanjeevni chat (session 316) at the owner's word (09:33 IST: "check and report, and put these 2 for amir as well"). Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` (v1.1), `CLAUDE.md` and `deploy_kits/KB_canon_all/BUILD_NORM_v1.md` first. **Part A is a diagnosis: read only, and a repair only by the spine's own documented commands — no code is changed by this kit.** Part B is data only: two rows. Times IST.*

## 0 · For the owner
1. **Amir entered all 30 stage-C vouchers of the 6-Sep count on 15-10 (09:14–10:00).** The chat compared Marg's closing of 15-10 (22:30) with the night before: 168 of 170 medicines moved as the vouchers say; **KT ROS DT** (Amir's voucher 9, Marg no. 14: issue 6 patte + 11 goli) and **VINBACTUM DS** (voucher 18, Marg no. 22: issue 25 nag) did not move at all — the other lines of those two vouchers did.
2. **The system's own verdict is stuck.** `/finance/stock/api/pad/hub/1` reads, at 09:30 on 16-Oct, `proof.C` state `wait`, all three lots `export / why: no_figure`, closing `15-10 10:11` — although the 15-10 sale report was taken at 05:11 and certified (*Sahi hai*, 13 bills) and the 15-10 closing at 05:17. `stock_app._s524_tryable` says a closing is tried only when the spine's reach (`last_sale`, `sale_stamp`, `last_pur`, `pur_stamp`) covers it; `no_figure` with a closing in hand means the **sale** side is short (`why = 'pur_behind'` would name the purchases).
3. **After this kit:** the cause is named in plain words; if it is something the spine's own runbook fixes (a build that did not run or failed its gate, a file not yet read, a stale state file), it is fixed by that runbook and the verdict is read; the two missing lines are on Amir's card as one-time Marg jobs.

## 1 · Numbers and pins
- Kit **S569_PROOF_REACH_AND_TWO_LINES** (board `_numbers` v451 → v452, with its PLANNED line). No D; an F number only if the build finds a fault — write it in the report as "F-new" and the chat takes the number. Project: **Sanjeevni**.
- **No `.py` changes.** Read only: `/root/finance/stock_app.py` (md5 at the open), `/root/finance/spine/*` (`spine_read.py status`, the build's state file, `spine_build.py`'s log), `/root/finance/amir_day.py` (`S494_DDL`, `_s494_lines` — the `tap` kind, `text_hi`, `sub_hi`, `show_from`, the "Kar diya" form; `amir.job_wait_days`).
- Writes: (B) two `amir_job` rows in `/root/finance/finance.db` (backup first by the backup API, `finance.db.bak_S569_<stamp>`); (A) only what the spine's runbook command itself writes. No service restart unless the runbook names one.
- The build lock. F-185: no phone number, no patient name in any output.

## 2 · Part A — why the proof has no figure (read only first)
1. `/root/wa/venv/bin/python3 -B /root/finance/spine/spine_read.py status` — print it whole (it carries no numbers of a person). Then the spine's reach as `stock_app` reads it (`_s524_reach(_s524_spine())` in a read-only Python on a copy, or the same queries on the spine db read-only): `last_sale`, `sale_stamp`, `last_pur`, `pur_stamp`; the closings after 15-10 10:00:49 with `end_day` and `stamp`.
2. The last runs of `spine_build.py` (cron 08–23 every 10 min): their log lines since 05:00 16-Oct, the gate result (14/14?), any failure. Does the spine hold the 15-10 SALE_BILLWISE file (md5 from `mi_file`, received 05:11 16-Oct)? If not, why not (not read, read and refused by a gate, a lock, a cap)?
3. **Decide by this rule:** if the cause is (a) a build that has not run, or ran and failed a gate on something transient, or (b) a file the spine's own documented command will read now — run that command once, exactly as the runbook / the file's own docstring states, and read the reach again. If the cause needs any code change, or a gate is red for a real data reason — **change nothing**, write the cause and the smallest repair in the report, and stop Part A.
4. **Then the verdict:** read `/finance/stock/api/pad/hub/1`'s `proof.C` on the box (the owner's session is not used; a local read-only call of the same function on a copy of finance.db is fine): each lot's state; for a `wrong` lot, its rows (item, need, moved, marg, closing day). Expected: KT ROS DT and VINBACTUM DS wrong, the other 168 proven. Say exactly what it found.

## 3 · Part B — the two lines on Amir's card (amir_job, kind 'tap', data only)
Insert, in one transaction after the backup, audited as `job_added` by `system` with `{"kit": "S569", "owner_word": "16-Oct 09:33"}` (amir_day's own `_audit` if importable, else the same row shape it writes):

| key | kind | subject | text_hi | sub_hi |
|---|---|---|---|---|
| `fix:S569:KT ROS DT` | tap | KT ROS DT | `KT ROS DT — Marg mein STOCK ISSUE kijiye: 6 patte + 11 goli` | `6 Sep ki stock ginti · voucher 9 ki line` |
| `fix:S569:VINBACTUM DS` | tap | VINBACTUM DS | `VINBACTUM DS — Marg mein STOCK ISSUE kijiye: 25 nag` | `6 Sep ki stock ginti · voucher 18 ki line` |

`created_at` = now (amir_day's `_stamp()` shape), `created_by` = `S569`, `show_from` = now, everything else NULL. Only "do this" words (D708): no verdict, no "check", no "chhoot gaya". The quantities are the voucher cards' own words (`qty_hi`, read from `/api/pad/amir/1` lines — assert they still read so before inserting).
**Check:** render `/finance/amir` as `amir` on a scratch copy (a walk-only session, as the S444 staff-eye walk): both lines under *Ek baar ke kaam* with a *Kar diya* button; nothing else on his card changed (diff the rendered card before/after, minus the two lines). The DUTY_MAP is not changed (the "Ek baar ke kaam" duty already exists — name its id in the report).
**Note for the report:** when Amir enters them today, Marg's closing of 16-10 will carry them; the stage-C proof judges on the first closing after his vouchers (15-10), so it will keep naming these two as wrong on that closing — that is true and is the owner's line only.

## 4 · Report
`claude_code_briefs/REPORT_S569.md` — 3–6 plain lines on top (the cause; whether it was fixed and how; the system's verdict; the two lines on Amir's card); then the evidence (status output, reach before/after, the commands run and their output, the rows inserted with ids, the backup). Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (the brief and the report; no kit code beyond a tiny `add_jobs_s569.py` if used).
