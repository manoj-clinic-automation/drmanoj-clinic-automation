# REPORT_S563 — S563_SCANAPP_TIDY (built, walked, rehearsed; not installed, not published)

**For Dr Manoj (plain English):**
- On the sorting desk, a paper that was set aside (like B-0162) now shows **"Already set aside on dd-mm-yyyy — Restore?"** with
  one Restore button. Restore puts it back to be sorted; it is never accepted again without your normal Save.
- The old *Bills awaited* page no longer shows a patient's challan to anyone, or your Personal challans to Shavez.
- Deleting a receipt now makes the bill it paid read unpaid again. A statement pays the invoices that have an amount first.
- Smaller fixes on the machine pages and the scanner's Adjust step. Reception's scanning is the same as before.
- Everything was tested on copies only and passed. **Nothing is on the live app yet**: the Scan App chat checks the kit, then
  you publish and paste the server line.

---

For the chat. Kit `deploy_kits/S563_SCANAPP_TIDY/` (28 files, `SUMS.md5`). Brief `claude_code_briefs/S563_SCANAPP_TIDY.md` v2.
Read first, as the brief says: `S563_OPEN_NOTES.md` (md5 `444097bf…`, matches) and `S563_BRIEF_R1.md` (md5 `e05fbfa4…`, matches),
the S560 / S559 / S557 briefs and reports, and S560's and S559's kit shapes. This run was done in Claude Code on the owner's PC
(not by `run_build.py`).

## 1 · FROM pins, as read on the box (17:49:51 IST, 15-Oct-2026, the box's own `date`)

| File | read | brief's FROM |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | `a4623438f068d8e691b797482bd942ab` | same |
| `/root/assetapp/clinic_papers.py` | `88963eacee217e051ae07091648a46d7` | same (read whole) |
| `/root/assetapp/asset_register.py` | `9daed9ea4f2a87e40b43711e472e701f` | same |
| `/root/assetapp/asset_machine.py` | `0caec41e655cfd51c2eaf9176ee33365` | same |
| `/root/assetapp/scanner_widget.js` | `1128ac975ba2543e1fe9edf7c721d4f8` | same |
| read only: `/root/finance/packs.py` · `claude_reader.py` · `claude_reread.py` | `048d2ad8…` · `3894dc23…` · `d9b75e78…` | same — never edited |

## 2 · The counted edits (`make_s563.py`; every anchor matched exactly once on the live bytes — on the PC and again on the box)

- **sorting_desk.py — 19:** SD1 mark `TIDY = "S563"` · SD2 ×3 the three "append-only" comments (:117, :1980, :2621) · SD3 ×4
  `_s563_words_text` added and used by `_s560_claude_kind`, `_s560_looks_receipt`, `_s560_looks_statement` · SD4 ×2 the statement
  order + its message · SD5 ×2 `paper_json`'s `aside` + the Save's refusal text · SD6 `fix_answer`'s restore → `_s563_restore` (no
  `status_from` read) · SD7 ×3 the S563 block (`_s563_aside_day`, `_s563_aside`, `_s563_restore`, `_s563_nototal_line`,
  `restore_answer`), the route `/desk/api/restore`, the desk's `C.restore` · SD8 ×3 the desk's script (the line, Save held, the button).
- **clinic_papers.py — 11:** item 3 (5): mark; `_s563_who_sees` + `challans_awaiting(db, owner=None)`; `challans_page`'s `sees`,
  its candidates and its closed list. Tidy (6): the header docstring (2), `_tail` (1), `_live` / `_live_sort` / `_live_sections` (3).
- **asset_register.py — 3:** mark; `bill_delete`; `_s559_pm`'s fallback.
- **asset_machine.py — 5:** mark; `paper_from_box`; `cover_line`; `old_renewal`; `from_paper`'s re-check under `BEGIN IMMEDIATE`.
- **scanner_widget.js — 1:** `dropSrc` only.

## 3 · TO pins (built on the PC, rebuilt on the box from the live bytes — identical)

`sorting_desk.py 062ac43cf71b52faa16d0feee25126c5` · `clinic_papers.py 9a59f977226f901e06d91c312cd116b7` (item 3 only:
`717043418fd39ba2b4574a4bd28efdc6`) · `asset_register.py 0828fbc307d400feff2fbc0872fef686` · `asset_machine.py
7d4fdffce01a28fd7e5cc2c4f2aeeb74` · `scanner_widget.js 10a8bb296944542278a06827c4d09c18`. All four `.py` compile on `/usr/bin/python3`
and `/root/wa/venv/bin/python3` (the installer's step, run in the rehearsal).

## 4 · The walk and the control (on the box, `/tmp`, a backup-API copy; made-up rows Z-2031-…, made-up logins, today 15-Jun-2031)

- `walk_s563.py` on the TO files: **17 checks, 17 GREEN** — W1 W2 · F1 (the line; not on a page / double scan; one line on a blank
  fix) · F2 (Restore: draft / captured, everything else kept, audited, `desk_fix_answered` neither read nor written, then the normal
  Save accepts) · F3 (manager 403 on Personal; page / double scan 400; pharmacy refused; owner ok) · F4 (blank fix never back to
  approved; the duplicate check holds it) · N1 (item 3) · D1 D2 (item 4) · S1 (item 5) · M1 M2 M3 (items 6–8) · P1 (item 9) · J1
  (item 10's bytes) · T1 (item 12) · Z1.
- **Negative control** (`--expect-red`, the live S560 files): **16 checks, 14 RED — every name in MUST_RED red** (W2, F1–F4, N1, D1, D2,
  S1, M1, M2, M3, P1, J1). Walk and control ran in separate `python3` processes.
- Item 11 (comments) has no check, as the brief allows; item 12 is proven by T1, below.

## 5 · Item 12 — the tidy's byte-identical proof

With the other four files at TO, `fetch_s563.py` ran twice in its own processes — once with `clinic_papers.py` item-3-only
(`71704341`), once with TO (`9a59f977`) — on the same made-up rows, the same day: 27 GET routes (every `clinic_papers` page:
`/papers`, `/papers/month` with every group, every made-up `/papers/<id>`, three `/join` pages, `/papers/challans`, plus `/renewals`
and three bill pages that call its helpers) and 14 POSTs (subgroup ×4, join ×2, unjoin, warranty ×2, pe_who ×2, challan close ×2,
challan delete), each POST on a fresh copy, as owner and as manager = **102 answers, 0 differing** (GET body md5 and length; POST
status, Location, flash, the made-up rows after, times masked).
**The pages item 3 changes** (against the live FROM file, by design): `/papers/challans` (the list, its candidates and its closed
list), the *"The bill for a challan?"* card on `/papers/<id>` and the challan hint on the `/papers` cards, the Bills-awaited count
on `/papers` (shown only when the desk is not mounted) and the owner's *Where each paper stands* challans row — each now without a
patient's challan, and for a manager without a Personal one.

## 6 · The browser walks (headless Chrome on the PC; log files ended 18:10:16, 18:11:40, 18:11:49 IST by their file times)

`walk/walk_results_s563.txt` holds all three outputs.
- **S563's own walk: 15/15** — V (the widget compiles in V8); **G**: page 1 deleted while page 2's Adjust picture loads 700 ms late
  → NEW ignores the late picture, Save gives one paper of page 2 + page 3; **G' control** on the live widget: the late picture
  opens on page 3's slot, Theek hai puts page 2 there, page 3 is lost; **H**: after the delete the stage button reads "page 2"
  (was "page 3"); **H' control**: the live widget still says "page 3"; **the seven surfaces** (five finance, the asset page, the
  intake) load the same DOM and the six non-intake ones save the same upload byte for byte as with the live widget; **A ×3** the
  desk with F-902's line at 1366 × 768, 1366 × 620 and 1920 × 1080 (one line, one Restore, the destinations on screen — at 1366 ×
  620 only Documents / Not here under the visible "more" cue — Save held "Restore it first (above)").
- **S559's frozen widget walk: 20/20** with NEW = the S563 widget (OLD 1143c77b, PREV 552effcd, fit pages from the S563 build).
- **S560's frozen desk-layout walk: 7/7** on the S563 build's desk pages.

## 7 · The earlier walks on the new files (each in its own process, on the box)

S560 **37/37** (its K2 line in S563's form) · S560 pack **9/9** · S548 **8/8** · S559 **43/43** (its J1 / J3 lines in S563's form) ·
S557 **41/41** · S555 **19/19** · S551 **87/87** (S559's three agreed lines). The adapted lines are written by `lines_s563.py` into
`/tmp` copies; no frozen kit was edited. S560 K2 is item 9 itself (a "Money receipt" item line no longer pre-chooses Receipt);
S559 J1 / J3 compare the widget's text line by line (now also S563's `dropSrc`). The S560 pack walk is given the pre-S560
`packs.py.bak_S560_d86d351a` as its *before* (its P8 measures S560's own change; `packs.py` is unchanged here).

## 8 · The rehearsal (`rehearse_s563.sh`, made-up root `/tmp/s563dev/root`, ended 18:17:59 IST by the box's `date`) — GREEN

1 fresh install green (all walks inside it as above; backups; database shape unchanged; lock released) and item 13 on a made-up
scratch folder: six names removed, `s560fix1b` holding a made-up `x.db` **left and named** · 2 ALREADY INSTALLED · 3 forced red
after placing → restored to the FROM pins · 4 `/desk` 404 → restored · 5 `/desk` 200 → restored (302 only) · 6 a live file moved
(`asset_machine.py`) → REFUSED before any backup or placing. The service was a stand-in; the restart `true`; every `S563_*` path
checked to be outside `/root`; the real `/tmp` list read before and after, unchanged.

After all runs the live box read back: the five files at their FROM pins, no `.bak_S563_*`, `assetapp` last started 12:55:26 IST
(S560's install), `/healthz` 200 and `/finance/healthz` 200. The builders' own `/tmp/s563dev` and `/tmp/s563probe` were removed.

## 9 · Calls made where the brief left room (each with its reason)

1. **Delete refused whenever the desk module is not loaded** (the brief's words), not only when the paper proves a payment (R1's
   variant). Safer for money; the desk module is always loaded unless `sorting_desk.py` fails to import.
2. **F-902's Restore is its own route** `POST /desk/api/restore` (an API address, not a page), so it can neither read nor write
   `desk_fix_answered`; the blank fix keeps `/desk/api/fix`. Both call `_s563_restore`. Audit actions: `desk_restored` (F-902),
   `desk_blank_restored` kept for the blank fix (earlier walks and records read that name).
3. A paper with **any `dup_of`** is refused by Restore and shows no line (the brief: "not an S441 double scan (dup_of)").
4. The set-aside day falls back to `created_at` **converted to IST** (it is stored in UTC).
5. Wording: the Save on a set-aside paper says *"B-xxxx is set aside. Press Restore on it first, then Save."*; the blank fix's
   message drops "as it was" (no longer true): *"… is back on its lane (draft). Sort it now — its Save accepts it as usual."*;
   item 5: *"B-xxxx has no total: only what was left after the invoices with a total went to it (₹N)."* (or "nothing was left").
6. Item 8: the renewal date is `MAX(due_date)` of the machine's *Contract renewal* rows; `_s559_pm` reads it through
   `asset_machine.old_renewal` (if that module is absent, it behaves as today).
7. Item 13 runs only after a successful install (not on ALREADY INSTALLED, a refusal or a restore); a symlink is never followed
   and is left, named.
8. The desk pages saved for the browser walk keep **only the made-up papers** in `list.json` (the live waiting list never left the
   box) — S560 had saved the whole list.
9. Marks for the walks: `TIDY = "S563"` in the desk, clinic_papers and asset_machine; `TIDY_S563` in asset_register. The widget's
   `S559.1` mark is kept (S559's walks read it).
10. The S557 walk's unchanged-pages baseline is taken from the built files without `asset_machine.py`, as S560 did.

## 10 · Not done, and why

- **Not installed, not published, no live row written, nothing restarted** — the brief overrides CLAUDE.md for this run.
- The server build lock was not taken: there was no install step (the rehearsal used a made-up lock).
- DUTY_MAP and the staff-eye walk: not applicable — no staff duty is added, moved or removed (and the brief forbids touching DUTY_MAP).
- `s554kit` and `s554probe` are already absent from the box's `/tmp`; the installer will print "not there" for them.

## 11 · Seen outside the brief (not touched)

- R1 note 22 stands: `d664_challan_close`, `d664_challan_delete` and `d664_join` still accept a Personal or patient challan id that a
  manager POSTs directly (the page no longer shows them).
- R1 note 21: a restored paper on a *captured* lane counts again at once (a Construction bill back into the parent's packs 8.2 /
  8.4; a Personal expense back into Personal expenses) — those lanes have no duplicate check; a restored paper older than
  `desk.floor` with a section does not reappear in Waiting (it is opened by its number).
- R1 note 23: a direct payment (no proof) on a deleted bill stays live but unread; receipts linked to a deleted statement keep their
  voided payments; pages / duplicates pointing at a deleted id are untouched.
- **S557-K2-N3 seen live in the walk:** after a Delete, SQLite gave the very next paper the deleted paper's id, and that paper then
  carries the deleted one's audit rows (`paper_deleted` among them). Pre-existing; a real fix needs AUTOINCREMENT on `bills`.
- `_s560_state` still calls an invoice with no total "Paid" for any amount it received (R1 note 20).
- `/tmp/s560dev` on the box is a builders' folder not on item 13's list; left.
- The S560 pack walk needs `/root/finance/packs.py.bak_S560_d86d351a` as its *before*; if that backup is ever removed, a later kit
  that re-runs S560's pack walk needs another *before*.

## 12 · Gates and cost

- `.gitignore` (last match wins): `git check-ignore` over the kit's files — **none ignored**.
- Contact-number gate, as PUBLISH_ALL runs it (`SANJ_CONFIG_STORE` as before: the default store), over the 29 kit files (with
  `SUMS.md5`) and this report: `NO_PHONE_NUMBERS: clean -- 30 staged file(s) checked (numbers and credentials).`
- No `__pycache__` / `.pyc` in the kit (every python run with `-B`; nothing imported from `deploy_kits\`).
- **Cost:** about **US$9.5** of API credit for this run, read from this session's budget meter when this report was written (the
  `run_build.py` runner's own log does not exist for this run — it was done in Claude Code directly).

**Nothing installed, nothing published.**
