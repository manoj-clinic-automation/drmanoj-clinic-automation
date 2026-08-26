# AUDIT RUN — 2026-08-24 · Slice 1: THE CASH TRAIL (calibration run)

**Auditor, run 1 (weekly, unattended). Seed: `AUDITOR_SEED_v1.md`. Read-only throughout — nothing live was touched; no VPS or live database was reached (unattended rule). Findings are AF-numbered candidates for the owner's triage; NO F-numbers minted (the F-series fork rule).**

**Calibration verdict up front:** slice 1 produced **2 high, 2 medium, 2 low candidates**, each with primary evidence generated this run (two by executing the real code, one by an empirical reproduction of the failure). The auditor is not returning a bare "clean" on the slice that yielded five faults in S195 — the calibration criterion is met.

---

## 0 · Phase 0 (auditor variant) — integrity of what was audited

- Fresh anonymous clone of `drmanoj-clinic-automation` (main).
- `deploy_kits/KB_canon_S198close/`: `md5sum -c SUMS.md5` → **12/12 OK, exit 0**.
- All five Tier-0 pins recomputed and matched the manifest exactly: Register v5.43 `cc4aefba…` · Archive v1.45 `5ca770d3…` · Fault Register v2.35 `8670b952…` · Runbook v132 `b888067d…` · START_HERE_199 `e53f22fe…`.
- **Live-pin recoverability (45 VPS pins in `live_pins_S198close.txt`):** an md5 index of every file in the repo + inside every kit tarball (LF-normalised variants included) recovers **44 of 45 pins byte-exact**. The one absentee is AF-6 below.
- The audited bytes are therefore the LIVE bytes, recovered by hash (D188), not the stale working trees: `finance_app.py` from `S198_H2`, `finance_ingest.py` from `S194_TRIPLE`, `marg_report.py` from `S193_DISC`, `staff_ledger.py` from `S193_F6`, `finance_daily.html` from `S195_NCSCAN`, `finance_entry.html` reconstructed (AF-6), PC kit from `deploy_kits/S195_MARG`.

Map built from code first; docs read afterwards as a diff (seed's inverted order). Expected S193–S196 standalone-doc manifest gaps treated as expected, not incidents.

---

## AF-1 · HIGH — the Marg sender can report "ACCEPTED" for a report that never left the PC, then permanently refuse to resend it

**Class:** silent drop + partial-state masquerading as complete. **Where:** `SEND_TO_CLINIC.bat` (kit `S187_M1a`, unchanged since; the file GUARD_AND_SEND.bat calls on GREEN).

**Mechanism.** The sender writes the server's reply to a shared file `last_response.txt` via `curl -o`, then decides success by `findstr "ACCEPTED-FOR-REVIEW" last_response.txt`. **curl does not touch the output file when the connection fails** — so on any network failure the file still holds the PREVIOUS run's reply. If that previous reply was an ACCEPTED, the batch: prints "ACCEPTED for Dr. Manoj's review", logs ACCEPTED to `send_log.txt`, and **appends the file's md5 to `sent_hashes.txt`** — after which every future run skips this exact report as "ALREADY SENT". The day's report is never staged on the server, reception is told it succeeded, and the retry path is booby-trapped by the sender's own dedupe.

**Primary evidence (reproduced this run, curl 8.5.0):** seeded `last_response.txt` with `ACCEPTED-FOR-REVIEW …`, ran the batch's exact curl invocation against an unreachable host → curl exit 56, `last_http.txt` = `000` (shell redirect always truncates), **`last_response.txt` unchanged** — the findstr match would fire. The HTTP code is captured but never consulted before the ACCEPTED check.

**Reproduction on the real machine:** one successful send (populates `last_response.txt`), then one send during a network outage.

**How would we know today:** the server-side S198_H1 health door ("Marg report — last arrived …") goes warn at 26h / bad at 36h, IF the owner opens the portal. So the absence surfaces within ~a day — but nothing anywhere explains that the cure is deleting the hash line from `sent_hashes.txt` on the medical PC; re-running GUARD_AND_SEND resends nothing (same bytes → local skip), and reception's screen keeps saying the report went.

**Severity = money × silence:** a full day's pharmacy staging (₹20–30k typical) delayed indefinitely, behind a success message; the health door caps the silent window at ~1–1.5 days but the recovery is undocumented and counter-intuitive. **Fix shape (builder's, not mine):** `del last_response.txt` before each curl, and gate the ACCEPTED branch on `HTTP == 200`.

---

## AF-2 · HIGH — the save-time "does your total match Marg?" check has never fired: it reads keys the payload has never carried (born dead at S195)

**Class:** monitoring that cannot see + vacuous test. **Where:** `finance_app.py` `_marg_total_for_date()` (~line 3843) vs `api_marg_push`'s `days_payload` (~line 2869).

**Mechanism.** The A1 feature (S195) warns the maker at save time when the typed total disagrees with the pushed Marg report, and writes the **high-severity `TOTAL_VS_MARG` data_flag** the checker's approval surface renders. Its reader scans `marg_push_staging.parsed_json` for days keyed `business_date` / `net_p`. The only writer of `parsed_json` stores days keyed `date` / `expect` / `lines_csv` / `items_csv` — no `business_date`, no `net_p`. **The reader can never match a real staged push.**

**Primary evidence (executed this run):** staged a payload through the app's own `_marg_staging` DDL with the writer's exact key shape, called the real `_marg_total_for_date` → `(None, None)`. Re-wrote the same row with the reader's expected keys → `(40000, 'the Marg report received')`. **Born-dead check:** the S195_A123 kit (the build that introduced A1) already carries the same `date=` writer — the mismatch has existed since the feature shipped.

**Corroborating absence:** no selftest references `TOTAL_VS_MARG` or `_marg_total_for_date`; the push-path test stub fabricates the reader's key shape (`{"business_date":…, "net_p":…}`, line ~8691) — the fixture mirrors the reader, not the writer. The S195 lesson ("an invented test fixture") recurring inside the machinery built to encode it.

**What still works (why this is not catastrophic):** the checker's Day Page variance (`marg_net_sql`, threshold ₹2,000) and the UPI misclass worklist read `sale_item` and are live — the checker still sees Marg-vs-entered when he opens a day. What is dead: the maker's early warning, and the high-severity flag in the queue.

**How would we know today:** `SELECT COUNT(*) FROM data_flag WHERE code='TOTAL_VS_MARG';` on the live box — predicted **0** since S195 despite real variances existing in that window.

**Severity:** medium money (the checker's later net still catches it) × high silence (zero coverage, wrong-shaped fixture, never fired once — indistinguishable from "all days matched"). One-line fix (`business_date`→`date` won't suffice — `net_p` isn't in the payload at all; the payload must carry the day's net, or the reader must use `survey_json`'s figures).

---

## AF-3 · MEDIUM — a failed approval can leave a posted Staff-Ledger advance behind, and the retry posts it again

**Class:** partial-state across two stores. **Where:** `api_approve()` (finance_app.py ~2043–2091) + `staff_ledger.make_entry()` → `append_ledger()`.

**Mechanism.** On approval, each pending salary advance is posted to the ledger via `make_entry` (which **appends to `ledger.jsonl` immediately and durably**), then `ledger_posted=1` is stamped in finance — but the stamp is only committed at the end. If a later step in the same approval fails — the second advance has a paise fraction (reachable: `to_paise` accepts "500.50"; the whole-rupee check raises AFTER earlier advances already posted), a missing staff_ref name, or a crash before `con.commit()` — the code path does `con.rollback()`: the finance stamps vanish, **the JSONL rows do not**. The idempotency guard is exactly the stamp that was rolled back, so the retried approval posts the same advance a second time — two APPROVED `ADVANCE_ISSUE` rows, both recovered from the staff member's salary at the close. The comment in the code ("a crash … leaves a VISIBLE ledger row … recoverable") is true of the crash but not of the loop failure + retry, which is silent and automatic.

**Primary evidence:** code-path reading of the live bytes: `append_ledger` writes and returns before any finance commit; no dedupe key ties a ledger row to its finance expense id (the reference lives only in narration text); `decide`/`make_entry` check nothing about prior postings.

**Reproduction (offline):** a day with two salary-advance rows, the second ₹x.50; approve; observe advance 1 in `ledger.jsonl` with `ledger_posted` still 0; fix and re-approve; observe the duplicate.

**How would we know today:** read-only duplicate scan of `ledger.jsonl` (command in §Commands). Also: no automatic reconciliation compares `day_expense (category_fixed='salary_advance', ledger_posted=1)` rows against ledger `ADVANCE_ISSUE` rows — the two books are never held to each other.

**Severity:** real money (a duplicated ₹15,000 advance is a duplicated salary deduction) × medium silence (a duplicate shows on the staff statement if someone reads it; nothing machine-checks it). Fix shape: stamp-and-commit per advance before posting the next, or give the ledger a dedupe key on the finance expense ref.

---

## AF-4 · MEDIUM — five checker-grade reads never got the F-127 rule: any medical-unit login can pull month totals, day-wise closings, drawings, and patient names

**Class:** authz drift (the F-84/F-127/F-132 family, recurring on sibling routes). **Where:** `finance_app.py` routes with **no `require()` and no internal role scoping**, behind only the unit-role gate (any role — maker or viewer — passes):

- `GET /finance/api/month/<ym>` — per-day revenue, **closing balances**, **the owner's personal drawings**, month totals (revenue/cash/upi/expenses/deposited/adjustments).
- `GET /finance/api/days` — per-day revenue/cash/upi/closing, 60 days.
- `GET /finance/api/day/<date>/lines` — every bill with **patient name + clinic id** + amount.
- `GET /finance/api/parked` — parked-cash months, every bank deposit with amounts.
- `GET /finance/api/month/<ym>/close-check` — month revenue total, residual cash, statement variance.

**The contradiction is the finding:** the same file scopes the maker deliberately elsewhere — `api_exceptions` filters to missing-day rows citing F-127; the day GET/save pops opening/closing for non-checkers citing F-132; `where-is-the-cash` is maker-safe by design. The rule "what a maker may see" is copied per-route, and these five never received it. Neither maker page calls any of them (verified against `finance_entry.html`/`finance_daily.html` fetch lists), so scoping them breaks nothing.

**Reproduction (the owner's own F-132 method):** incognito, logged in as the maker, open `/finance/api/month/2026-08` — figures appear.

**Severity:** modest money-at-risk today (one maker, trusted; the harm class is the one the owner already ruled out at F-127 — the whole unit position visible to a non-checker) × high silence (nothing tests route-by-route scoping; a future `viewer` role widens it quietly).

---

## AF-5 · LOW — the medical-PC guard runs a different parser than the server, while claiming "its judgment is identical to the server's"

**Class:** two-copies-of-a-rule + doc-vs-reality drift. **Evidence:** `deploy_kits/S195_MARG/marg_report.py` (and the project-knowledge copy) = **`28b47d44…` — the S180 parser**; the server runs **`6411a57d…` (S193_DISC)**. Diff: the PC copy lacks the S183 `.xlsx` support (content-sniffing `_XlsxSheet`) and the S193 gross/disc handling. The guard's docstring and GUARD_AND_SEND.bat both claim it runs "the SAME read_report() the clinic server uses".

**Failure direction is closed, not open** — e.g. a report saved through Excel as .xlsx passes the server but is REFUSED by the guard with a misleading "file poori/theek nahi hai" message; reception re-exports fruitlessly. Blocked money reaches a human loudly, so LOW — but the premise justifying a local guard at all ("identical judgment") is currently false, and the copies will keep drifting: every future server parser change silently widens the gap.

---

## AF-6 · LOW — one live pin's bytes exist nowhere off the box as a file: the maker's money-entry page

**Class:** recovery-story gap (slice-4 material, surfaced here because it is the cash-entry page). **Evidence:** of the 45 live pins, only `finance_entry.html 92477b06…` matches **no file in the repo or inside any kit tarball** (26,745-file-scale hash sweep of the clone, stored + LF-normalised). Cause: `S193_UX` was an **in-place patch kit** — it shipped `patch_pages.py`, not the resulting page; the S197 F-169 correction fixed the *record* to match the box but harvested no copy of the *bytes*.

**Reproduced the recovery this run (this is the demotion evidence):** `S190_F3`'s `finance_entry.html` + `deploy_kits/S193_UX/patch_pages.py` → output hashes **exactly `92477b068c67e28661b049b7f3385708`**. So the bytes are derivable — but only via a two-step recipe documented nowhere as the recovery path. The general condition (repo `finance/`/`portal/` working trees S180/S182-stale) is already a named backlog item; this pin is the one case where no kit holds the bytes either. One-line remedy at the next close: file the current on-box `finance_entry.html` into a kit or refresh the working tree.

---

## Re-tests of prior findings (seed rule: re-execute, demote what no longer reproduces)

First run — no prior AF findings. S195's slice-1 fixes were re-verified present in the live bytes: the signed-net one-expression rule (`marg_net_sql`, F-165-family) — present, with the ₹2,000 threshold named once; the guard chain (F-166-family) — installed as designed; the S198_H2 fixes (F-171 worst-first sort, F-172 Sunday-blind age) — both present in `_health_state`.

## Surface B — the system of work (aging, single-person gates)

- **Token rotation (`FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`), exposed in chat 21-Aug — day 3 open**, still listed "highest severity" at the S198 close. The push token is also sitting in clear text in `SEND_TO_CLINIC.bat` on the medical PC by design (scoped, stage-only) — rotation is one config line there too.
- **Darpan's SPECIAL `0cc0b26b38c5` approval — deadline is the August close, ~1 week away**; the ₹8,000 shifts if missed (S192 record).
- **August month-end is the first full run of SL5–SL7 + F6 + the new doors** — the runbook already says "watch, don't assume"; AF-3 above is specifically a close-adjacent risk.
- Cold kit **1 of 3–5** (not yet due). **F-173** (April-2025 advice file) still open, owner-side.
- Single-person gates unchanged: one man applies everything; manojz is still publisher+puller+mirror+offsite in one box (slice 4's subject).

## Commands for Dr Manoj to run (read-only; paste outputs into the next audit run or the builder chat)

1. **AF-2 live confirmation (VPS):**
   `sqlite3 /root/finance/finance.db "SELECT COUNT(*) FROM data_flag WHERE code='TOTAL_VS_MARG';"`
   Predicted **0**. Any non-zero number falsifies AF-2 and I will demote it.
2. **AF-3 duplicate scan (VPS):**
   `/root/wa/venv/bin/python3 -c "import json,collections; r=[json.loads(l) for l in open('/root/staff_ledger/ledger.jsonl')]; c=collections.Counter((x['staff'],x['amount'],x['date_from']) for x in r if x.get('category')=='ADVANCE_ISSUE' and x.get('status')=='APPROVED'); print([k for k,v in c.items() if v>1] or 'no duplicates')"`
3. **AF-1 history check (medical PC, cmd):**
   `type D:\SendToClinic\send_log.txt` — any ACCEPTED line for a day whose report never appeared on the workbench is a past firing of AF-1.
4. **AF-4 live confirmation (any browser, incognito, logged in as Darpan):** open `https://followup.dr-manoj.in/finance/api/month/2026-08` — if figures render, the leak is live.

## Coverage statement (never a bare "clean")

**Exercised this run:** the PC-side send chain (guard, sender, batch logic — all live bytes, one failure empirically reproduced); the server push/apply/auto-replay chain; `api_save_day` end to end; `api_approve` incl. the F6 ledger bridge; custody / cash-position / cash-count; month close-check + finalise; route-level authz across all 100+ routes (mechanical sweep); the parser pair; pin recoverability for all 45 live pins. **NOT exercised (unreachable unattended):** the live `finance.db` and `ledger.jsonl` (four read-only commands supplied above); the medical-PC watcher + manojz 10-min pull (record-only review); `finance_backup.sh` restores (slice 4); the Yes Bank/ICICI witness chain (slice 2, next run); the D322 holiday classifier's data behaviour; the ~7,000 selftest-block lines were sampled, not read exhaustively. Call it **roughly 70% of the cash trail's code surface exercised, 0% of its live data** — the four commands above are the bridge.

**Next run: slice 2 — the UPI/bank witness chain** (and re-execution of AF-1…AF-6 evidence first).

---

## Plain-language summary for Dr Manoj

Doctor sahab, the first audit of the cash trail found the pipes mostly sound but three things worth fixing this week. **First**, the "send to clinic" button on the medical PC can lie: if the internet hiccups at the wrong moment it shows reception "ACCEPTED" while nothing was sent, and it then refuses to ever resend that day's report — your health tile will show the gap within a day, but the cure (deleting one line in `sent_hashes.txt`) is written nowhere; ask the builder for the two-line fix. **Second**, the warning that compares the typed daily total against the Marg report has been silently broken since the day it was built — it has never fired once (run command 1 above to confirm: the answer should be 0) — so until it is fixed, your own eye on the Day Page is the only check that the typed total matches Marg. **Third**, before the August close — your first month-end on the new machinery — run command 2 above: it takes ten seconds and confirms no salary advance was ever accidentally posted twice into the staff ledger, a gap the audit found is possible when an approval fails halfway. Everything else found (a privacy gap where Darpan's login could read your month totals by URL, and two smaller record-keeping gaps) is written up above for the builder session, none of it urgent before the close.

*Audit run 1 · slice 1 · 2026-08-24 · read-only · next slice: 2 (UPI/bank witness chain).*
