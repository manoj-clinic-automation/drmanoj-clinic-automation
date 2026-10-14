# S557_MACHINE_PAGES — the scan app's FINAL kit (brief for the build runner, Agent SDK, the API credits)

*Written 14-Oct-2026 by the Scan App project (session 315). Kit **S557** claimed on the board `_numbers` (v417 → v418)
with its PLANNED line (D646). The owner, 09:15 IST: "seems like a perpetual build now, make a final build now." This is
the final plan's step 3 (D719 kit c) plus every leftover, in one kit. This file is the whole scope. Run by
`D:\Downloads\_kbtools\agent_build\run_build.py S557_MACHINE_PAGES`.*

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** It places the kit in
`deploy_kits\S557_MACHINE_PAGES\`, writes `claude_code_briefs\REPORT_S557.md`, and stops. The Scan App chat checks it;
the owner publishes and pastes one server line. Nothing live is placed or restarted; no live row is written.

## 0 · Read first
- `claude_code_briefs\S551_SORTING_DESK.md` (v4), `REPORT_S551.md`, `S555_DESK_CORRECTIONS.md`, `REPORT_S555.md` — every
  rule and NEVER there still binds (D664 never guess; D710 sorted = accepted; pharmacy one-way; Personal owner-only;
  patient's papers out of every total; one commit per action; audits).
- `deploy_kits\S555_DESK_CORRECTIONS\` — **copy its kit shape exactly**: env-overridable installer (`S557_*`), the
  rehearsal's refusals (`/root/`, `systemctl`, port 8030) and its five outcomes, the walk isolated before import
  (`ASSETS_DB`, `ASSETS_UPLOADS`, `SCANAPP_ANTHROPIC_KEY_FILE`, `SCANAPP_ANTHROPIC_URL`, `CLINIC_PORTAL_DIR`,
  `FINANCE_LOCAL_URL`, `SHARED_LIB_DIR`; `SARVAM_API_KEY`, `ANTHROPIC_API_KEY` unset), walk and control in separate
  processes, made-up rows dated relative to an injected `today`, made-up suppliers differing in their first two words.
- `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S315\S555_KIT_REVIEW.md` (its notes, item B3).
- `deploy_kits\KB_canon_all\BUILD_NORM_v1.md`.

## 1 · Pins — FROM bytes, read on the box first; a different byte = STOP that file and report
- `/root/assetapp/asset_register.py` **`7ac386641095cacbac79594356e7ec6d`** (S555's TO).
- `/root/assetapp/sorting_desk.py` **`7e16fd80d6bd2bfe0a6e5366848d8569`** (S555's TO).
- NEW `/root/assetapp/asset_machine.py`.
- Read only, hashed in the report: `clinic_papers.py` `058c9bcb5a4973f8a15984b645ff57d7`, `claude_reread.py`
  `d9b75e784c4a806e941f3d1a243990e1`, `claude_reader.py` `3894dc2358abd875ee61ced7619e1e1b`, `scanner_widget.js`
  `1143c77b13ae62652d4d961a92b9a9ab` (**never edited**).
- *(These are S555's installed pins: if the live bytes differ, S555 is not installed — STOP and say so.)*

## 2 · A — the machine pages (the owner's D719: "an asset's parts, cover history and spends, each with its scanned bill")

All new behaviour in **NEW `asset_machine.py`**, mounted like `sorting_desk.py` (one guarded `init(ar)`; a failure leaves
the app running). Counted, anchored edits in `asset_register.py` only for: the mount; one hook on the machine page
`/assets/<id>` (AR `asset_view`, about AR:1878 in the old bundle — find it by text) that renders the new sections below
the existing details; and the renewals hook (A5). Routes registered without the `/scanapp` prefix. English. Pages for the
owner are **short and collapsible** (each section a fold, closed except the first).

**A1 · The cover line** at the top of the machine page: *"Covered: AMC by <provider> till dd-mm-yyyy"* / *"Under
warranty till dd-mm-yyyy"* / *"No cover"* — the live cover with the latest end date; amber within 30 days of its end, red
once lapsed. Then one line of totals: *Bought for ₹X (dd-mm-yyyy) · Spent since ₹Y on N repairs/services · Cover paid ₹Z*
— prices hidden from a manager when the machine's `hide_price` is set (the app's existing rule).

**A2 · Parts** (a fold): each part — name, make, model, serial, fitted on, warranty till, its paper. *Add a part*;
*Replaced / removed* marks it (date, who) and keeps it in a folded *Removed parts* list — never deleted.
NEW `asset_part(id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL, name TEXT NOT NULL, make TEXT, model TEXT, serial TEXT,
fitted_on TEXT, warranty_till TEXT, bill_id INTEGER, removed_on TEXT, removed_by TEXT, expiry_id INTEGER, by_whom TEXT,
at TEXT)`.

**A3 · Cover history** (a fold): every warranty / AMC / CMC / insurance / other period, newest first — kind, provider,
from, till, cost, its paper; *Add cover* (a renewal is simply the next period; earlier periods stay as history; a mistake
is voided, never deleted). The machine's old single fields (`contract_type`, `provider`, `contract_cost`) are shown once,
read-only, as *"From the old record: …"* when set — **no data is moved**.
NEW `asset_cover(id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL, kind TEXT NOT NULL CHECK(kind IN
('warranty','amc','cmc','insurance','other')), provider TEXT, from_day TEXT, till_day TEXT NOT NULL, cost REAL, bill_id
INTEGER, remind_days INTEGER NOT NULL DEFAULT 30, expiry_id INTEGER, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT
NULL DEFAULT '', by_whom TEXT, at TEXT)`.

**A4 · Spends** (a fold): repairs, service visits and spare purchases — date, what was done, amount, by whom, its paper —
from the existing `service_logs` (the existing *Add service* form keeps working) with one NEW column
`service_logs.bill_id INTEGER` (additive, guarded for the two-worker race). Totals per year.

**A5 · Renewal reminders:** each live cover and each part's warranty puts **one** reminder on the existing renewals list
(`/renewals`, the `expiries` table: `entity='asset'`, `entity_id` = the machine, `label` e.g. *"AMC — <provider>"* /
*"Part warranty — <part>"*, `due_date` = till, `threshold_days` = remind_days) — the row id kept in `expiry_id`, so it is
created once and updated, never duplicated. A newer cover of the same kind resolves the older one's reminder
(`resolved=1`); a voided cover or a removed part resolves its own. Idempotent: an `ensure`/heal at start re-links any
cover or part whose reminder is missing.

**A6 · "Its paper" — linking a scanned bill.** Every *its paper* field is a box *"B-____"* that accepts a stamp the person
may see — never a pharmacy paper, never a Personal paper to a manager, never a patient's paper — and shows a link to the
paper (`/bills/<id>`). On the paper's own page (and the desk's *Clinic equipment* destination note), a line *"Linked to
<machine> as purchase / part / cover / spend"* when it is. **A paper filed as Clinic equipment** can be turned into a new
machine record from the existing *"+ asset record"* link, pre-filled from the paper (supplier, date, amount; the item's
make/model/serial from Claude's reading when present — `claude_reading` rows with `ok=1`, tolerate absence), and the new
machine keeps the paper as its purchase bill (`assets` already links by `bill_id` / the existing backfill — read how and
use that).

**A7 · Who:** the same gate as the asset pages today. Adding or changing parts, covers and spends: owner and manager.
**Switch `machine.on`** (absent = OFF): while OFF a manager sees the machine page exactly as today; the owner sees the new
sections at once. The Switches card (S551's, on the front page) gets a fourth line *Machine pages for Shavez*, through
S551's `POST /desk/switch` (add the key to its allowed list — a counted edit in `sorting_desk.py`).

## 3 · B — the leftovers

- **B1 · One word per lane** on the owner's and managers' pages that still show the long forms ("Clinic bill — asset or
  consumable", "Pharmacy purchase — Sanjeevni" …): the bills list for managers, the bill page, the lanes page, the
  papers pages — *Clinic · Pharmacy · NK Pathology · Personal expense · Other document*, from the one helper S555 made.
  **Reception's intake and slip are NOT changed** (staff wording, Roman Hinglish, by design).
- **B2 · The desk's guard on an unreadable amount:** a Claude amount that is not a number (NaN, inf, text) is ignored, not
  shown, and never breaks a paper's JSON (S555 review: `sorting_desk.py` near line 683).
- **B3 · The S555 review's notes** that are defects on the desk: fix each that is a real defect, say for each one fixed or
  left and why, in one line each.

## 4 · Never
Everything in S551 v4 §5 and S555 §3, and: delete any row or file (mark: `removed_on`, `voided_at`, `resolved`); move or
change an existing asset's own fields by a data step; change reception's intake; touch `packs.py`, `scanner_widget.js`, any
finance or Sanjeevni file, the DUTY_MAP; write a real row; place a file; restart; publish; push; print a name of a person,
a phone number, a key or a token.

## 5 · Walk, control, installer, rehearsal, kit, report (BUILD_NORM_v1 — S555's shape)
- **Walk** (isolated, made-up rows only): A1 the cover line in its three states (none / live / within 30 days / lapsed) and
  the totals, price hidden for a manager on a `hide_price` machine; A2 add / remove a part, removed list, its reminder;
  A3 add cover, renew (older reminder resolved), void, the old-record line shown and nothing moved; A4 a spend with a
  paper, the old *Add service* form still working, `bill_id` column present; A5 exactly one `expiries` row per live
  cover/part after two restarts (re-import), updated not duplicated; A6 a stamp box refusing pharmacy, a patient's paper and
  (for a manager) a Personal paper, the paper page's "Linked to" line, a machine created from a clinic-equipment paper
  pre-filled; A7 switch OFF (manager sees today's page), ON, the owner always; B1 every owner/manager page shows the short
  lane word and **reception's intake HTML byte-for-byte the same words as before**; B2 a NaN amount; **the S555 walk and the
  S551 walk (with S555's agreed date form) still green on the new files**.
- **Control:** the walk on the live (S555) files is red, with named checks for A1–A7, B1, B2 red.
- **Installer** `install_s557.sh`: S555's order and safety, plus the additive tables / column by `asset_machine.ensure()`
  after the database backup; `/healthz` 200 and `/desk` 302; ALREADY INSTALLED; restore on any failure after placing;
  `machine.on` left absent; the undo line uses `\cp -p` (a printf format writes it as `'\\cp -p'`).
- **Rehearsal** `rehearse_s557.sh`: S555's five outcomes on a made-up root.
- **Kit** `deploy_kits\S557_MACHINE_PAGES\`: `KIT_ID.txt`, `README.md`, `install_s557.sh`, `make_s557.py`,
  `asset_machine.py`, `walk_s557.py`, `rehearse_s557.sh`, `PIN_FROM_*.txt`, `PIN_TO_*.txt`, `SUMS.md5`; SUMS checked,
  `.gitignore` last-match-wins, the contact-number gate as `PUBLISH_ALL.bat` runs it — clean.
- **Server line** (README): `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S557_MACHINE_PAGES/install_s557.sh`
- **Report** `claude_code_briefs\REPORT_S557.md`: 3–5 plain lines for the owner on top (what his machine page now shows;
  OFF for Shavez until he switches it on; how to add a cover and a part); then pins, counted edits, walk and control counts
  printed in the log, the S555/S551 walk re-runs, the rehearsal's outcomes, the gates, each B3 decision, the cost. Last
  line: **nothing installed, nothing published.**

**If anything cannot be done as written, stop at that point, write what was done and why, and end.**
