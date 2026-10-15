# S563_SCANAPP_TIDY — the scan app's last tidy round (D646 PLANNED line, board v438)

**Why.** The leftovers of the five kits S551 · S555 · S557 · S559 · S560, one fault the owner saw (F-902: B-0162 set aside with
no way back on the desk), two defects found while reading the code (NEW1, NEW2) and `clinic_papers.py` consolidated (drift 6).
The brief: `claude_code_briefs/S563_SCANAPP_TIDY.md` (v2, with the independent read `S563_BRIEF_R1.md` taken in). The owner,
16:30 IST 15-Oct-2026: *"go ahead, but use the claude api"*. **No new feature, no new page, no new switch, no new column, no
data step.**

**What changes (owner / manager pages; reception's intake only in item 10's Adjust stage).**
1. **F-902 — Restore a set-aside paper.** On the sorting desk a paper with status *rejected* that is not a joined page and not an
   S441 double scan shows ONE line *"Already set aside on dd-mm-yyyy — Restore?"* (the day = `approved_at`, which every set-aside
   path writes; else the scan day in IST) and a **Restore** button; Save is held ("Restore it first (above)") until then.
   Restore (`POST /desk/api/restore`) puts it back to the status a fresh paper on its lane has (`AR._lane_kind_status`: clinic
   *draft*, the other lanes *captured*), clears the reason, `approved_by` and `approved_at`, keeps lane, section, kind, doc kind,
   Dr MK / Dr Bhawna and challan state (D664), audits who / when / from what (`desk_restored`), checks `_visible` (a Personal
   paper: the owner only), refuses a page or a double scan, and never reads or writes `desk_fix_answered`. **One shared
   `_s563_restore`** also serves the blank fix (`/desk/api/fix`, audit `desk_blank_restored`): it no longer reads `status_from`;
   a blank-fix paper shows its one line, never two.
2. **S560-N3** — no restore returns a paper straight to *accepted*: the next Save runs the normal accept with its
   same-vendor-number-amount check.
3. **NEW1** — the old *Bills awaited* page (`/papers/challans`), its join candidates and closed list, the bill page's *"The bill
   for a challan?"* and the challan count: never a patient's paper; a Personal one for the owner only. Filtered in place inside
   `clinic_papers.py` (`challans_awaiting(db, owner=None)`, `_s563_who_sees`); the desk's helper is not called; pharmacy
   challans stay listed.
4. **NEW2 (+ S557-K2-N2)** — the owner's **Delete** of a paper, in one transaction: every live payment the paper proves voided
   with its allocations (the desk's `_s560_void_own`, `_s560_void_allocs`), so the bill a deleted receipt paid reads unpaid
   again; `assets.bill_id` cleared where it pointed at the paper; one `paper_deleted` audit row. Refused, nothing changed, when
   the desk module is not loaded.
5. **S560-N4** — a statement pays the invoices that have a total first (oldest first); an invoice with no total takes only what
   is left, and the Save's message says so ("B-xxxx has no total: only what was left after the invoices with a total went to it").
6. **S557-K1-N9** — *+ asset record from a paper*: "already a machine's purchase bill" is checked again inside the POST under
   `BEGIN IMMEDIATE`; a second tap gets the existing machine.
7. **S557-K1-N6** — the stamp box (`asset_machine.paper_from_box`) refuses a copy or a page: *"This paper is a copy / a page of
   B-xxxx — open B-xxxx instead."* `refusal()` unchanged.
8. **S559-K1-N6(i)** — with no S557 cover row, an old record whose own latest *Contract renewal* date is past reads *"Covered (old
   record): AMC — lapsed on dd-mm-yyyy"* (red), and the PM sentence (`asset_register._s559_pm`) is not shown.
9. **S560-N2** — the receipt / statement words are matched on the vendor, the bill number and Claude's supplier / number only
   (`_s563_words_text`), never on item names; `_s560_text` (and so `_s560_prefill`) unchanged.
10. **S559-K2-N7 + the stage label** — `scanner_widget.js`, inside `dropSrc` only (called only in the intake's `cvScanOn`
    branch): a late Adjust picture of a deleted page is ignored (`adjGenS559++`); after a delete shifts the page under
    adjustment, the stage button names that page. The finance app's five surfaces and the asset page never reach it.
11. **S560-N13** — the three "append-only" comments in `sorting_desk.py` say what the code does now.
12. **CP-TIDY** — `clinic_papers.py`: a current header docstring; one shared tail `_tail` for `_live`, `_live_sort` (still the
    challan alone), `_live_sections`; `_inr`, `_stamp`, `_who`, `VERSION` kept. Proven to change no served byte.
13. **The box's scratch** — after its own run the installer removes `s560fix1a s560fix1b s560fix1probe s560fix2a
    s560fix2_pins.sh s554kit s554probe` under `${S563_SCRATCH_ROOT:-/tmp}`, each only if it holds no `*.db`, `*.sqlite`,
    `*.db-wal`, `*.db-shm` or `*.json` file and no symlink (never followed); else it is left and named in the log.

**Files.**

| File | FROM → TO | counted edits (each anchor exactly once) |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | `a4623438` → `062ac43c` | 19 |
| `/root/assetapp/clinic_papers.py` | `88963eac` → `9a59f977` | 11 (item 3: 5 → `71704341`; the tidy: 6) |
| `/root/assetapp/asset_register.py` | `9daed9ea` → `0828fbc3` | 3 |
| `/root/assetapp/asset_machine.py` | `0caec41e` → `7d4fdffc` | 5 |
| `/root/assetapp/scanner_widget.js` | `1128ac97` → `10a8bb29` | 1 |

- **Read only, pinned:** `claude_reader.py` `3894dc23`, `claude_reread.py` `d9b75e78`, the parent's `/root/finance/packs.py`
  `048d2ad8` (never edited; the S560 / S548 pack walks read it), `packs.py.bak_S560_d86d351a` and
  `scanner_widget.js.bak_S559_1143c77b` (the earlier walks compare against them).
- **No database change.** A safety backup `assets.db.bak_S563_<time>` is still taken (backup API). **Only `assetapp` restarts**;
  `clinic-finance` is not touched (no finance file changes; the widget is a static file, cache-busted by its own file time).
- **Not touched:** the LEAVE items of the open notes, `packs.py`, every finance and Sanjeevni file, the portal, DUTY_MAP
  (no staff duty is added, moved or removed).

**Kit files.** `make_s563.py` (the anchored patcher; `--cp-item3-only` builds the tidy's comparison file) · `walk_s563.py` (17
checks; `--expect-red` the control) · `fetch_s563.py` (item 12's byte-identical fetch, run by the walk in its own processes) ·
`lines_s563.py` (the lines S563's pins force in /tmp copies of the frozen S560 / S559 walks) · `install_s563.sh` ·
`rehearse_s563.sh` · `walk/` (the PC's headless-Chrome walk and its results) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Install (server), after the publish:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S563_SCANAPP_TIDY/install_s563.sh
```

`DRY=1` before `bash` stops after the walks. The installer needs the S560, S559, S557, S555, S551 and S548 kits beside it (their
walks are the regression). It ends with `/healthz` 200, `/desk` 302 (302 only) and the served widget carrying S563's correction;
any red after placing restores the five files and restarts assetapp.

**Undo (server):**

```
\cp -p /root/assetapp/sorting_desk.py.bak_S563_a4623438 /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/clinic_papers.py.bak_S563_88963eac /root/assetapp/clinic_papers.py && \cp -p /root/assetapp/asset_machine.py.bak_S563_0caec41e /root/assetapp/asset_machine.py && \cp -p /root/assetapp/scanner_widget.js.bak_S563_1128ac97 /root/assetapp/scanner_widget.js && \cp -p /root/assetapp/asset_register.py.bak_S563_9daed9ea /root/assetapp/asset_register.py && systemctl restart assetapp
```

**Proof (15-Oct-2026, on the box in /tmp only, and in headless Chrome on the PC).**
- `walk_s563.py`: **17 checks, all green** on the built files (made-up rows, made-up logins, made-up today 15-Jun-2031).
- The control on the live (S560) files: **14 RED, every named check** (W2, F1–F4, N1, D1, D2, S1, M1–M3, P1, J1).
- Item 12: 102 answers (every clinic_papers GET body; every POST's status, Location, flash and rows, each POST on a fresh copy),
  owner and manager, item-3-only vs TO — **identical**.
- Earlier walks on the new files: S560 37/37 (K2 in S563's form, `lines_s563.py`), S560 pack 9/9, S548 8/8, S559 43/43 (J1 / J3
  in S563's form), S557 41/41, S555 19/19, S551 87/87 (S559's three agreed lines).
- Browser (`walk/walk_results_s563.txt`): S563's own walk **15/15** (V; item 10's scenes G and H, each red on the live widget as
  the control; the seven surfaces byte-identical in load and save; F-902's line on the desk at 1366 × 768, 1366 × 620 and
  1920 × 1080); S559's frozen walk **20/20**; S560's desk layout **7/7**.
- `rehearse_s563.sh`: **green** — fresh install (and item 13 on made-up scratch), ALREADY INSTALLED, forced red restored, /desk
  404 restored, /desk 200 restored (302 only), a moved file refused before placing.
