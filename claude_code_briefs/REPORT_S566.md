# REPORT_S566 — S566_SCANAPP_LAST_FIXES (built, walked, rehearsed; not installed, not published)

**For Dr Manoj (plain English):**
- **Restore on the sorting desk now checks first** that the paper is not a second copy of one already counted ("This looks like
  B-xxxx — open it instead."). A restored paper waits on the desk as "restored — sort it" until it is saved.
- **No paper hides any more:** B-0009 (the Construction challan stuck at "Waiting") will show in the desk's Waiting list, and
  Bills awaited will show both of its challans, so its count matches its rows.
- **Home's "Spend this month" will equal The month's total.** A half-read bill date like "14/10" is never saved again (B-0163's
  stays as it is, now flagged "date looks misread"). The Machines list shows a blank instead of "None". `/desk?open=B162` works.
- The old challan buttons now refuse a patient's challan, and refuse your Personal papers to Shavez, on the server itself.
- Tested on copies only — all green. **Nothing is on the live app yet:** the Scan App chat checks the kit, then you publish and
  paste the server line.

---

For the chat. Kit `deploy_kits/S566_SCANAPP_LAST_FIXES/` (23 files + `SUMS.md5`). Brief `claude_code_briefs/S566_SCANAPP_LAST_FIXES.md`
v2, read whole with `S566_BRIEF_R1.md` (its replacement wording applied as the brief binds it), S563's brief / report / K1 review,
S560's brief / report, REPORT_S559, REPORT_S557 and BUILD_NORM_v1. Run in Claude Code under `run_build.py` (log
`S566_SCANAPP_LAST_FIXES_20261016_0536.log`).

## 1 · FROM pins, as read on the box (05:37:24 IST, 16-Oct-2026, the box's own `date`)

| File | read | brief's FROM |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | `062ac43cf71b52faa16d0feee25126c5` | same |
| `/root/assetapp/clinic_papers.py` | `9a59f977226f901e06d91c312cd116b7` | same |
| `/root/assetapp/asset_register.py` | `0828fbc307d400feff2fbc0872fef686` | same |
| `/root/assetapp/asset_machine.py` | `7d4fdffce01a28fd7e5cc2c4f2aeeb74` | same — **not edited** (see call 1) |
| read only: `scanner_widget.js` · `/root/finance/packs.py` · `claude_reader.py` · `claude_reread.py` | `10a8bb29…` · `048d2ad8…` · `3894dc23…` · `d9b75e78…` | same — never edited |

## 2 · The real cause of each item (confirmed in the FROM code; R1's § Causes hold)

1. **N5** — `_s563_restore` (sd:2858) writes the lane's fresh status with no duplicate check; on the clinic lane The month counts a
   draft at once (`CP._live`), Construction counts draft/approved/captured on three lanes; and `waiting()` lists a restored paper
   with a section only if scanned after `desk.floor` and never saved before — so it vanished. `_dup_by_triple` alone is empty for
   the blank fix (the row has no supplier/amount; Claude's reading does).
2. **N6** — `challan_close`, `challan_delete`, `join_page` POST and `unjoin` (cp:1331, 1347, 463, 535) read the id and write with
   no patient / Personal test; only the GET lists were filtered (S563).
3. **B-0009** — `waiting()`'s SQL (sd:536-541) admits a live paper only if clinic/other_doc with no subgroup, or scanned on/after
   `desk.floor`; a Construction challan draft scanned 11-Sep is never selected (and the heal never accepts a non-final challan).
   The live row was not read (rule); the walk seeds both possible shapes. On a database copy the new reason lists exactly 1 live
   paper (counts only).
4. **Bills awaited 2 vs 1** — the menu = `len(awaiting_challans(...))` (ar:4517); the page `awaited()` skipped a challan whose
   supplier key is empty (`if not key: continue`, sd:1136). On the copy: 2 open challans, 1 with no supplier read.
5. **"14/10"** — `AR._norm_date` returns any unreadable input unchanged (ar:497) at the four `bill_date` writers: the reading's fill
   `_bg_extract` (ar:2861, Sarvam's header), `bill_new` (ar:2590), `bill_edit` (ar:3633), the intake prefill (ar:3456). `MONTH_OF`
   (cp:995) took `substr(bill_date,1,7)` with no shape test → a month called "14/10". "Approved by system" on a draft: the old bill
   page printed `approved_by` for any non-rejected status (ar:2709); `_doc_kind`'s reopen (sd:884-895) keeps `approved_by`.
6. **Home ≠ The month** — home summed `status='approved'` by `substr(bill_date,1,7)` over every lane (ar:1269-1274); The month sums
   sections from `month_data` (drafts and approved, `MONTH_OF`, finals). No grand-total function existed.
7. **"None"** — the stored word: `contract_type TEXT NOT NULL DEFAULT 'None'` (ar:118), the form's first choice, printed raw
   (ar:1404, ar:1956). No other cell on the two pages prints a Python None (category, status, contract_type are NOT NULL; the rest
   already use `or '—'`).
8. **`?open=`** — `_s559_open` (sd:1715): digits = record id, else `_by_stamp`, which needs "B-0162"/"B-162"; "B162" failed; the
   grey line was always "That paper can't be opened here".

## 3 · The counted edits (`make_s566.py`; every anchor matched exactly once on the live bytes — on the PC and again on the box)

- **sorting_desk.py — 19:** SD1 mark `LAST = "S566"` · SD2 `_marks` reads `desk_restored`/`desk_blank_restored` · SD3 ×2 `waiting()`:
  the SQL also selects drafts and restored papers; the reasons `restored` / `waiting` · SD4 the two hints · SD5 ×7 `awaited_open`,
  the card (`noread`), the loop (no skip), its foot, the sort, the template's two lines · SD6 ×2 `month_data` uses
  `_s566_paid_rows` / `_s566_total` · SD7 ×2 `_s559_open` and the desk's grey line `{{cant}}` · SD8 `fix_answer` returns a
  `DeskError` as a plain 400 · SD9 `_s563_restore` runs `_s566_restore_dup` first · SD10 the S566 block (`_s566_restore_dup`,
  `_s566_restored`, `_s566_waits`, `_s566_stamp_form`, `_s566_lanes`, `_s566_paid_rows`, `_s566_total`, `month_total`).
- **clinic_papers.py — 9:** mark; `MONTH_OF`'s GLOB shape test; `_s566_door`; its calls in `challan_close`, `challan_delete`,
  `join_page` POST (head + every page + the typed paper), `unjoin`, `set_warranty`, `set_pe_who` (R1 note 18 as the brief binds it).
- **asset_register.py — 11:** home card → `month_total`; Contract cell and Contract line `|s566_contract`; the approved / rejected
  line; the bill page's misread flag; `_bg_extract`'s date (pharmacy unchanged); `bill_new` and `bill_edit` refusals; the intake
  prefill; `_s559_awaited_n` → `awaited_open`; the S566 block (`LAST_S566`, `_s566_full_date`, `_s566_typed_date`, `_s566_pharm`,
  `_s566_bad_date`, `_s566_contract`, the filter and the global).

## 4 · TO pins (built on the PC, rebuilt on the box from the live bytes — identical)

`sorting_desk.py 255a27edde3b3fc9e6e1632eb7b41527` · `clinic_papers.py 024464cc3d3ab5e1ead1526540904d61` · `asset_register.py
19ebade7aaa76b04ba9529ea0de064ef`. `asset_machine.py` stays `7d4fdffc…`. All three compile on `/usr/bin/python3` and
`/root/wa/venv/bin/python3` (the installer's step, run in the rehearsal).

## 5 · The walk and the control (on the box, `/tmp`, a backup-API copy; made-up rows Z-2031-S…, one unused B-09nn found by key; made-up logins; today 15-Jun-2031)

- `walk_s566.py` on the TO files: **11 checks, 11 GREEN** — W1 W2 · I1 (3 doubles refused: triple on a Personal-expense Construction
  paper, Claude's reading on a blank-fix paper, the same capture; 2 unique restores → captured / draft, listed "restored — sort it",
  gone after the Save) · I2 (7 doors refused, nothing written; a plain challan still closes, the owner's warranty saves) · I3
  (B-0009's two shapes listed with their hints; supplier-read challan not; equipment / Personal owner-only; patient never; menu
  count = list; rows unchanged — 4 of 6 made-up papers added) · I4 (owner menu 8 = page rows 8, manager 6 = 6; the "Supplier not
  read" card) · I5 (fill None / full date written / pharmacy "14/10" kept; edit and new-bill refused; stored "14/10" → scan month,
  flag, 7 pages 200; approved / rejected lines) · I6 (Others with no date ₹850 + estimate draft ₹640 + procedure ₹1,000: home =
  month_total = the page's sections) · I7 · I8 (5 of 5 stamp forms; "No paper B-99999"; the manager's refusal reason; a bare number
  stays an id) · Z1.
- **Negative control** (`--expect-red`, the live S563 files, a separate process): **11 checks, 9 RED — every name in MUST_RED red**
  (W2, I1–I8).

## 6 · The earlier walks on the new files (each in its own process, on the box, inside the installer)

S563 **17/17** and its tidy fetch (S563's item-3-only `clinic_papers.py` rebuilt from S563's own `.bak_S563_*`, S566's 9 edits on it
= `c6f126aa`, against the TO: **102 answers, 0 differing**) · S560 **37/37** · S560 pack **9/9** · S548 **8/8** · S559 **43/43** ·
S557 **41/41** · S555 **19/19** · S551 **87/87**. **Adapted lines** (`lines_s566.py`, written to `/tmp` copies only; no frozen kit
edited): **S563 F4** — the blank fix's Restore of a paper matching an accepted one is now refused before anything is written
(item 1 itself), so F4 expects 400 + "open it instead", the paper still set aside, and still never two accepted copies; **S559
O3 / O4** — the grey line now names the reason (item 8): a pharmacy paper's `_visible` line, "No paper 999999999", the
manager's "Personal papers are the owner's alone." S563's own adapted lines (S560 K2, S559 J1 / J3) are applied as S563 did.
**Browser** (headless Chrome on the PC, 06:05:01–06:05:10 IST by its clock): S560's frozen desk-layout walk **7/7** on the final
build's desk pages (made-up rows only) — `walk/walk_results_s566.txt`.

## 7 · The rehearsal (`rehearse_s566.sh`, made-up root `/tmp/s566dev/root`, 06:02:11–06:04:40 IST by the box's `date`) — GREEN

1 fresh install green (every walk above inside it; backups; database shape unchanged; `asset_machine.py` untouched; lock
released) · 2 ALREADY INSTALLED · 3 forced red after placing → restored to the FROM pins · 4 `/desk` 404 → restored · 5 `/desk`
200 → restored (302 only) · 6 `clinic_papers.py` moved → REFUSED before any backup · 7 `asset_machine.py` (read only) moved →
REFUSED before any backup. The service was a stand-in, the restart `true`; every `S566_*` path outside `/root` (the earlier kits
read from `/root/deploy/repo/deploy_kits`, never written); the live scan-app folder read back unchanged.

After all runs the live box read back (06:05:31 IST): the four files at their FROM pins, no `.bak_S566_*`, `assetapp` last started
19:08:56 IST 15-Oct (S563's install), `127.0.0.1:8030/healthz` 200, public `/scanapp/healthz` 200, `/finance/healthz` 200, no build
lock. My `/tmp/s566dev` and `/tmp/s566count` were removed.

## 8 · Calls made where the brief left room (each with its reason)

1. **`asset_machine.py` is not edited.** The word "None" is printed by `asset_register.py`'s two templates; the machine module
   already treats it as no contract. Fewer files moved; it stays pinned read-only and the installer refuses if it moves.
2. **The restore's duplicate check refuses on an exact match only:** (a) `_dup_by_triple`'s exact; (b) the exact triple from
   Claude's reading, only when the reading has supplier, number and amount; (c) the same capture (fine distance ≤ `DUP_EXACT`).
   A "near" match (no number) does not refuse — the same standard as the app's own accept (`CP._accept`).
3. **`waiting` is added only when no other reason lists the paper**, so every existing hint and reason list is unchanged;
   `restored` is added beside other reasons, and its hint comes right after the fix line's.
4. **The intake prefill keeps the pharmacy lane as before** (as the reading's fill does) — the Sanjeevni side reads that lane.
5. **The new-bill / edit refusal** returns to the (empty) form with one line, checked before a stamp number is taken.
6. **The old bill page's flag** tests the shape only (not yyyy-mm-dd) with the desk's own words "date looks misread — check"; the
   desk keeps its wider rule.
7. **Home** reads `sorting_desk._today()`'s month; if the desk is not mounted, or `month_total` raises (logged), the old query runs.
8. **`/desk?open=`**: digits = record id; `[Bb]-?0*nnn` = a B-stamp; anything else goes to `_by_stamp` as typed (other series).
9. **`set_pe_who`** keeps its own 403 for a Personal paper (F-891) and calls the helper after it.
10. Wording stays English: the desk and the old papers pages are owner / manager pages already in English (S551–S563).
11. The health probe is S563's (`127.0.0.1:8030/healthz`); the brief's `/scanapp/healthz` is the same route through the proxy
    (both read 200).
12. The server build lock was not taken: no install step (the rehearsal used a made-up lock).

## 9 · For the owner to decide (reported, not changed — R1 notes 13, 14)

- **What leaves the home card:** an accepted Personal, résumé or miscellaneous paper on the clinic lane and an accepted paper
  with no section (home counted every approved paper); **what joins it:** drafts in a section (an estimate slip, a held double, a
  Clinic-equipment paper awaiting your Save) and papers whose month comes from the set month or the scan day.
- **A D710-held double** (same supplier, number and amount as an accepted paper, kept as a draft on purpose) is counted in its
  section of The month — and so now on home — until it is answered on the desk. Receipts, statements, awaiting challans, patient
  and pharmacy papers are not counted (checked).

## 10 · Not done, and why

- **Not installed, not published, no live row written, nothing restarted** — the brief overrides CLAUDE.md for this run.
- B-0163's stored "14/10" left as it is (no data step, D664); B-0009 not moved (only made reachable).
- DUTY_MAP and the staff-eye walk: not applicable — no staff duty is added, moved or removed (and the brief forbids DUTY_MAP).
- R1 note 17: the old `/papers/challans` header already counts with S563's filters (pharmacy challans included by design) —
  unchanged.

## 11 · Seen outside the brief (not touched)

- A restored paper filed from the old papers pages (not the desk) keeps the `restored` reason until a desk Save, since only the desk
  writes `desk_saved`.
- S557-K2-N3 (from S563) still stands: SQLite may give a new paper a deleted paper's id; it then carries the old audit rows.
- The earlier walks now need, as *before* files on the box: `scanner_widget.js.bak_S559_1143c77b`, `packs.py.bak_S560_d86d351a`
  and S563's five `.bak_S563_*`. If any is removed, a later kit re-running them needs another source.

## 12 · Gates and cost

- `.gitignore` (last match wins): `git check-ignore` over the kit's files and this report — **none ignored**.
- Contact-number gate (`deploy_kits\NO_PHONE_NUMBERS.py --files-from`, `SANJ_CONFIG_STORE` as before: the default store) over the
  24 kit files (with `SUMS.md5`) and this report: `NO_PHONE_NUMBERS: clean -- 25 staged file(s) checked (numbers and credentials).`
  `_scratch\` (the live copies of the four files, the built files, the saved pages) is git-ignored and stays on the PC.
- No `__pycache__` / `.pyc` in the kit (every python run with `-B`; nothing imported from `deploy_kits\`).
- **Cost:** the runner's log writes its cost line only when the run ends ("DONE · cost $…", as S563's log shows); at the time this
  report was written the log (`S566_SCANAPP_LAST_FIXES_20261016_0536.log`) held no cost line yet. The session's own meter read
  about **US$8.4** at that moment — the log's closing line is the figure to quote.

**Nothing installed, nothing published.**
