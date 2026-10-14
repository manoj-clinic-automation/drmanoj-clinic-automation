# S555_DESK_CORRECTIONS — brief for the build runner (Agent SDK, the API credits)

*Written 14-Oct-2026 by the Scan App project (session 315). Kit **S555** claimed on the board `_numbers` (v414 → v415)
with its PLANNED line (D646). The owner, 08:15 IST: "first prioritize what all corrections you need to do in the scan app
… execute that through the Claude API first." This file is the whole scope. Run by
`D:\Downloads\_kbtools\agent_build\run_build.py S555_DESK_CORRECTIONS`.*

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** It places the finished kit in
`deploy_kits\S555_DESK_CORRECTIONS\`, writes `claude_code_briefs\REPORT_S555.md`, and stops. The Scan App chat checks it;
then the owner publishes and pastes one server line. Nothing live is placed or restarted, no live row is written.

## 0 · Read first
- `claude_code_briefs\S551_SORTING_DESK.md` (v4) and `claude_code_briefs\REPORT_S551.md` — the desk these corrections
  are made on; **every rule and every NEVER of S551 v4 still binds** (D664, D710, D722; pharmacy one-way; Personal
  owner-only; challans filed not accepted; audit names `relane` / `subgroup` / `desk_saved`; one commit per Save).
- `deploy_kits\S551_SORTING_DESK\` — **its isolation, walk, control, installer and rehearsal are the model: copy their
  shape exactly** (the env-overridable installer `S5xx_*` variables, the rehearsal's refusals, separate processes for walk
  and control, the isolation variables set before import incl. `CLINIC_PORTAL_DIR`, `FINANCE_LOCAL_URL`,
  `SHARED_LIB_DIR`, the made-up suppliers differing in their first two words, the injected `today`).
- `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S315\S551_KIT_REVIEW_K2.md` (its two notes are items 6 and 7 below).
- `deploy_kits\KB_canon_all\BUILD_NORM_v1.md`.

## 1 · Pins — FROM bytes, read on the box first; a different byte = STOP that file and report
- `/root/assetapp/sorting_desk.py` **`bb28d8c8d95435b4a566d2929f473587`** (S551).
- `/root/assetapp/asset_register.py` **`c107c6bbb3e6c0c0d0535c5ed094b6e4`** (S551; read whole at S551 — drift 1).
- `/root/assetapp/claude_reread.py` **`47548ab97c55a1f4fb8d5d1a608a1681`** (S550).
- Read only: `/root/assetapp/clinic_papers.py` `058c9bcb5a4973f8a15984b645ff57d7` (edit only if item 4 truly needs its
  own-name list exported — then counted, and pinned), `/root/assetapp/claude_reader.py` `3894dc2358abd875ee61ced7619e1e1b`,
  `/root/assetapp/scanner_widget.js` `1143c77b13ae62652d4d961a92b9a9ab` (**never edited**).

## 2 · The corrections (all of them; nothing else)

1. **Save always on screen.** On a 1366 × 768 laptop the desk's *Save — next paper* button sits about 170 px below the
   screen. The right-hand panel's fields scroll inside the panel; **the Save button, its line under it, and the
   "A page of another paper / Blank — discard" row sit in a footer of that panel that never scrolls away** (CSS: the panel
   a column flex box, the fields area `overflow:auto; flex:1`, the footer `flex:none`). The left list keeps its own scroll.
   Nothing else on the layout changes.
2. **Dates as dd-mm-yyyy.** Every date the desk and its three pages show reads `dd-mm-yyyy` (today the desk's Date box
   shows `2025-08-21` under a `dd-mm-yyyy` placeholder). Typing accepts `dd-mm-yyyy`, `d-m-yy`, `dd/mm/yyyy` and
   `yyyy-mm-dd`; it is stored as today (ISO `yyyy-mm-dd` in `bills.bill_date`, `paid_on`, `implant_payment.day`). A date
   that cannot be understood is refused with one plain line, nothing saved.
3. **The misread-date flag on a genuinely older bill.** Shri Ram B-0001 (bill 21-Aug-2025, scanned 14-Aug-2026) is flagged
   "date looks misread" though its date is right. New rule in `misread_date`: flagged when the date is before
   2015-01-01, **after the scan day + 7 days**, or **more than 400 days before the scan day**; still takes `today`.
4. **A supplier read as the buyer.** B-0010, B-0011, B-0012 carry the owner's / clinic's own name as their supplier (the
   reader took the "bill to" name). Use the **same own-name words `clinic_papers` already uses** for its *the clinic's own
   name → Miscellaneous* suggestion (read `suggest()`; reuse its list, never a second list). When the stored supplier
   matches them: the desk's Supplier box shows it with a grey line *"This is your own name — the reader took the buyer.
   Type the supplier, or choose Miscellaneous if it is the clinic's own paper."*; and if Claude's reading has a different
   supplier, that line offers it (*"Claude read: <name> — use it"*, one tap fills the box; nothing saved until Save).
5. **Show Claude's reading beside each field.** `reading()` returns, besides `doc_kind`, `made_out_to` and `items`,
   Claude's **supplier, number, date and amount** from `claude_reading.data` (read `claude_reader.py` for the key names;
   rows with `ok=1`; tolerate the table being absent). Under each of the four boxes, when Claude's value **differs** from
   the stored one (compared as in item 2 for dates, to the rupee for amounts, first two words for supplier, spaces/case
   ignored for numbers), a small grey line *"Claude read: <value> — use it"*; one tap fills the box. Never shown for a
   pharmacy paper (never on the desk) or a Personal paper to a manager. `made_out_to` is never shown.
6. **The bills list's lane words.** `https://followup.dr-manoj.in/scanapp/bills` shows one lane in two wordings
   ("Clinic" beside "Clinic bill", "Pharmacy" beside "Pharmacy purchase"). Find why (read the list's code) and show
   **one short word per lane** everywhere in that column: *Clinic · Pharmacy · NK Pathology · Personal expense · Other
   document* (`AR.LANES` labels cut at " — " or a small map — your call, one place). Counted edit in `asset_register.py`.
7. **The installer's /desk probe accepts 302 only** (K2 note N1) — in S555's own installer; the rehearsal's stand-in
   answers 302.
8. **No Claude read of a patient's paper.** `_s550_claude` (in `asset_register.py`) and `claude_reread.py` skip a paper
   with `subgroup='patient_paper'` (belt and braces: such a paper sits on `other_doc`, which is already never sent).
   Counted edits.

## 3 · Never
Everything in S551 v4 §5, and: edit `scanner_widget.js`, `packs.py`, `finance_app.py`, `portal.py`, `tile_grants.json`, the
DUTY_MAP or any `/root/finance/` file; save anything on a paper from the reading's "use it" lines without a person's Save;
print a person's name, a phone number, a key or a token; write a real row; place a file; restart; publish; push.

## 4 · Walk, control, installer, rehearsal, kit, report (BUILD_NORM_v1 — the S551 kit's shape)
- **Walk** (isolated as S551's, made-up rows, made-up today): item 1 — the Save button and its row are inside the
  panel's non-scrolling footer in the served HTML/CSS (assert the structure and the CSS rules); item 2 — every date on the
  four desk pages renders `dd-mm-yyyy`; each accepted input form saves ISO; a bad date refused and nothing written;
  item 3 — a bill 358 days before its scan not flagged, 401 days flagged, a date 8 days after the scan flagged, 2014
  flagged; item 4 — a made-up paper whose supplier is one of the own-name words shows the line, and the offered Claude
  supplier, and nothing changes until Save; item 5 — "Claude read" lines appear only where values differ, never for
  `made_out_to`, never to a manager on a Personal paper; item 6 — the bills list shows one word per lane for rows made
  with each old and new kind/lane combination; item 8 — `_s550_claude` and `claude_reread`'s selection skip a
  `patient_paper` row (no network: the made-up key and URL). **Every S551 walk check still green** (run S551's walk
  against the new files too, and say so).
- **Control:** the same walk on the live (S551) files is red, with the named checks for items 1–6 and 8 red.
- **Installer** `install_s555.sh` (S551's shape; `S555_*` variables; FROM pins → `make_s555.py` → TO pins → compile →
  walk + control on a scratch copy (`DRY=1` stops here) → `.bak_S555_<from8>` → place → restart `assetapp` only →
  `/healthz` 200 **and `/desk` 302** → plain-English line → undo line; ALREADY INSTALLED on a second run; any failure
  after placing restores and restarts). No database change (none is needed; if you find one is, stop and report).
- **Rehearsal** `rehearse_s555.sh` on a made-up root: green · ALREADY INSTALLED · forced red restores · desk not answering
  restores. Refuses `/root/`, `systemctl`, port 8030.
- **Kit** `deploy_kits\S555_DESK_CORRECTIONS\`: `KIT_ID.txt`, `README.md`, `install_s555.sh`, `make_s555.py`,
  `walk_s555.py`, `rehearse_s555.sh`, `PIN_FROM_*.txt`, `PIN_TO_*.txt`, `SUMS.md5`. Then SUMS checked, `.gitignore`
  last-match-wins, the contact-number gate as `PUBLISH_ALL.bat` runs it — clean.
- **Server line** (README): `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S555_DESK_CORRECTIONS/install_s555.sh`
- **Report** `claude_code_briefs\REPORT_S555.md`: 3–5 plain lines for the owner on top; then FROM/TO pins, each counted
  edit, the walk and control counts **printed into the log**, the S551 walk re-run result, the rehearsal's four outcomes,
  the gates, the cost. Last line: **nothing installed, nothing published.**

**If anything cannot be done as written, stop at that point, write what was done and why in the report, and end.**
