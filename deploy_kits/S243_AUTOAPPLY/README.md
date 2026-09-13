# S243_AUTOAPPLY -- a pushed sale report applies itself the moment it arrives

Built 13-Sep-2026 (S243). Owner's ruling: **"Apply must be automatic -- we have been tracking
this report for long."** Last night's 12-Sep `SALE_BILLWISE_DETAIL` (pushed 23:01) sat PENDING
"(day not filed)" until it was applied by hand in the morning, beside two pushes of 11-Sep of
which the newer was applied and the older removed by hand. This kit makes both acts automatic.

## Why it sat (read before build -- the S219 kit, the base, the S210/S211 patches)

* **S219_MARG_AUTOAPPLY (live since 02-Sep, pin a57980c2)** auto-applies on arrival **only a day
  that is ALREADY filed** (`patch_marg_autoapply_s219.py` D_NEW: `if _d["date"] in not_filed: continue`,
  then `_replay_pending_marg_for_day(con, date, by="auto-push")`). The other order -- day filed
  later -- is the S194 replay inside `api_save_day`, which fires only when someone SAVES the day.
* Since **S210 TRUTHFLOW (D354)** the medical day is no longer saved by hand: the checker's Apply
  **creates** the day from Marg + bank. So for a not-filed day neither trigger fires: S219 skips it,
  nobody saves the day -> PENDING until the owner presses Apply. That is exactly 12-Sep.
* Duplicates today: same day, different file -> both rows stage (md5 index only blocks identical
  bytes). Apply the second time: `ingest_day` deletes the earlier batch's `sale_item` rows, marks that
  `ingest_batch` `superseded`, inserts a new batch (finance_ingest.py L355-365); the apply route
  deletes the day's `sale_line_item` and `load_lines` re-inserts (`INSERT OR REPLACE`, UNIQUE
  (unit,bill_no,seq)). So the day is **replaced, never duplicated** -- but nothing ranks the two
  files, and the S194 replay applies pending pushes **oldest first**, so an older pending export
  could later be dragged back over a newer applied one. This kit closes that too.

## The rule (decision taken, S243)

When a VERIFIED `SALE_BILLWISE_DETAIL` push arrives for day D, the server applies it **at once,
filed day or not**, through the checker's own Apply (same guards: expect-count match, item lines
load, D354 autofile when the day is absent, S219 summary + continuity), provided it is the
**newest** export for D:

| situation | what happens | staging row | audit_log (by `auto`) |
|---|---|---|---|
| nothing applied for D yet | applied | `applied`, `applied_by='auto'`, facts in `apply_result_json.s243` | `auto-apply` + the core's `apply` |
| D already applied from an earlier file, this one has MORE non-zero bills **or** a LATER `A` bill number **or** (same bill set) a DIFFERENT net than the S243-recorded apply -- a corrected re-export | applied (day replaced) | as above; the earlier row stays `applied` (history) | `auto-apply` |
| D already applied, this one brings nothing more | put aside | `superseded`, rule **"older than applied"** | `auto-dismiss` |
| an OLDER push for D is still pending when the newer applies | the older is put aside | `superseded`, rule **"superseded by <md5-8>"**, payload cleared | `auto-dismiss` |
| the apply cannot complete (e.g. autofile refuses: net<=0 / UPI>net / `marg.autofile=0`; expect mismatch) | stays pending, as today; the push message says why | `pending` | `auto-apply-held` |
| `/root/finance/AUTOAPPLY_OFF` exists | **exactly as today** (S219 second order, PENDING otherwise) | -- | -- |

`superseded` is used, not `dismissed`: the live table's CHECK admits only pending / applied /
rejected / superseded (S211 REMOVEFIX proved `dismissed` raises IntegrityError). The
`MARG_DAY_NOT_FILED` flag written at push time is cleared once the day is filed and applied.
The owner's **Apply** and **Remove** buttons work unchanged (walked); a hand apply still reads
"loaded"; the sender on the owner's PC (`marg_gate.py`, af2c3ca5) classifies every S243 answer
as accepted because each carries `"ok": true` -- no re-send loop.

## The changes (both files patched ON THE BOX; neither live file is in the repository)

`patch_marg_autoapply_s243.py` -- four anchors in `/root/finance/finance_app.py`, each exactly once:

| | where | change |
|---|---|---|
| **H** | before `api_marg_push()` | the S243 helpers (`_marg_autoapply_s243`, `_marg_applied_state_s243`, `_marg_put_aside_s243`, ...) |
| **P** | prelude of `api_marg_push_apply()` | the route keeps `require("checker")` + the request body and calls **`_marg_apply_core_s243(u, pid)`**, which is the ORIGINAL body unchanged (S210 autofile and S219 summary inside it ride along). One rule for button and machine (D349). |
| **L** | `api_marg_push_list()` | each row also carries `auto` (the S243 rule / time) |
| **D** | `api_marg_push()` after `con.commit()` | calls the auto-apply and answers `APPLIED` / `SUPERSEDED` / `ACCEPTED-FOR-REVIEW`; when it stands aside (OFF file, modules absent, internal error) the pre-S243 block runs untouched. **Both shapes handled**: S219 present (anchor = S219's own first three lines) or absent (the base block). |

Every anchor exists in the S204_C2 base and is untouched by every later patcher: all 102
`deploy_kits/S2*/patch_*.py` were grepped for the anchor lines (EVIDENCE); only S219 touches
the D region, and both of its outcomes are handled. `assert count==1` on each; refuses otherwise.

`patch_hub_autoapply_s243.py` -- two lines in `/root/finance/finance_ui/finance_approvals.html`
(`loadPushes()`): an applied row with `applied_by === "auto"` reads **"✓ applied automatically
<time>"**; a superseded row shows its rule ("superseded — superseded by 1a2b3c4d" / "— older than
applied"). The live hub pin **e1652297** was rebuilt byte-for-byte here from S218 FINAL through the
five S219/S220 hub patches, and the patcher applies to it: predicted **cc349dd00d0a2f861ec54242c9551557**.
No new card, no new button (S218 FINAL contract).

## Install (one line, on the VPS, after the publish)

```
bash /root/deploy/repo/deploy_kits/S243_AUTOAPPLY/install_S243_AUTOAPPLY.sh
```

SUMS + KIT_ID gate -> refuses unless `/root/finance/finance_app.py` starts **81db4854** (live_pins_S242close.txt)
or **72bc8323** (the S241-close manifest) -- or carries the sibling S243_SCREEN_FIXES mark with its
`.bak_S243_<one of those pins>` beside it (lineage proven by the backup) -- and
`/root/finance/finance_ui/finance_approvals.html` is **e1652297...** -> both patched to `.new` on the box ->
`py_compile` -> `.bak_S243_<pin8>` of both -> placed -> `import finance_app` under the unit's own environment
(the S243 functions asserted callable) -> restart `clinic-finance` only if the smoke passes -> healthz within 20 s.
Any RED after placing restores both files and restarts. Re-run: ALREADY INSTALLED. `finance_app.py` is patched in
place, so its pin is known only at install -- the installer prints it; **record it**.

## OFF switch (no restart, takes effect on the next push)

```
touch /root/finance/AUTOAPPLY_OFF
```
ON again: `rm /root/finance/AUTOAPPLY_OFF`

## Rollback (one line; `<pin8>` printed by the installer, e.g. 81db4854 or 72bc8323)

```
\cp -f /root/finance/finance_app.py.bak_S243_<pin8> /root/finance/finance_app.py && \cp -f /root/finance/finance_ui/finance_approvals.html.bak_S243_e1652297 /root/finance/finance_ui/finance_approvals.html && systemctl restart clinic-finance.service
```

## Proof (EVIDENCE_S243.txt)

* patcher selftest 24/24 on the S204_C2 base and on a live-shaped copy (S204_C2 + S208 pend + S210 x4 +
  S211 + S219 M1, i.e. every patch that touches the marg-push path); hub patcher 7/7 on the rebuilt live pin.
* **`walk_autoapply_s243.py` -- 66/66**: real Flask app, real sqlite from `finance_schema.sql` + `finance_returns.sql`,
  real `finance_ingest` / `finance_returns` / `marg_report`; every push a REAL Marg-shaped `.xls` (xlwt -> xlrd)
  sent as `marg_gate.py`'s multipart. Not-filed day -> APPLIED at once, day autofiled by `auto`, 3 bills / 6 lines,
  audit by auto, flag cleared, hub text "✓ applied automatically"; fewer bills -> SUPERSEDED "older than applied";
  fuller (4 bills) -> APPLIED, day replaced 4/8, first stays applied; same count with a later A-number -> applied,
  without -> put aside; a corrected same-set re-export (net differs) -> applied; OFF file -> PENDING with today's words, no auto audit, then the checker's Apply works and
  reads "loaded"; older pending -> "superseded by <md5-8>"; Remove works (S211 `rejected`); filed-by-hand day ->
  APPLIED with the S219 summary; two-day report with one day already held -> APPLIED; identical bytes ->
  ALREADY-RECEIVED; no phone-shaped number in any auto audit row; py_compile.
* The same walk on the UNPATCHED copy reproduces the symptom (7/7): PENDING, no day, nothing in the books.
* Installer mock-tested (ROOT=, fake systemctl/curl): fresh install, ALREADY INSTALLED on rerun, wrong pin
  refused with nothing changed, healthz failure -> both files restored and service restarted, sibling lineage
  accepted, sibling mark without its backup refused.
* On the box after install (touches nothing live; builds its own temp db):
  `FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_AUTOAPPLY/walk_autoapply_s243.py`
  (needs `xlwt` in that venv for the fixture: `/root/wa/venv/bin/pip install xlwt`).

## Doubts, stated

1. The live `finance_app.py` is not in the repository; the anchors are proven on the S204_C2 base plus every
   later patcher's text, not on the live bytes. The patcher's four `count==1` asserts are the real guard.
2. "Bills" compares **non-zero bill counts** (what the ingest reads) and the **highest `A`-series number**; credit
   notes are not counted for "later". For the SAME bill set the day's net is compared against the net an earlier
   S243 apply recorded, so a corrected re-export (one bill edited in Marg) applies; when the two differ, arrival
   order is the tie-break (newest by arrival wins) -- the owner's PC sends its outbox in order, so that is the
   chronological one. A same-set re-export whose net equals the recorded one is put aside (nothing new).
5. The `MARG_DAY_NOT_FILED` flag is cleared only by the automatic path; the owner's hand Apply leaves it as today.
3. The first-ever S243 comparison for a day applied by hand before this kit reads the day's `ingest_batch.rows_read`
   and `sale_item` refs (review-queue bills carry no ref there), so "last bill" is a lower bound: a re-push can only
   err towards re-applying identical data, never towards refusing a fuller one.
4. Kit S243_SCREEN_FIXES also patches `finance_app.py`; install order does not matter (either pin path is accepted).

## Files
KIT_ID.txt · README.md · SUMS.md5 · EVIDENCE_S243.txt · install_S243_AUTOAPPLY.sh · patch_marg_autoapply_s243.py ·
patch_hub_autoapply_s243.py · walk_autoapply_s243.py
