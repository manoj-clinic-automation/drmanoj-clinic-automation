# S555_DESK_CORRECTIONS — the sorting desk's corrections (D646 claim, S315)

**What it does.** These are corrections to the sorting desk (S551) at `https://followup.dr-manoj.in/scanapp/desk`, and to two
scan app parts around it:

1. **Save is always on screen.** On the 1366 × 768 laptop, the right-hand panel's fields scroll inside the panel. *Save —
   next paper*, the line under it, and the *A page of another paper / Blank — discard* row sit in a footer of that panel
   that never scrolls away. The left list keeps its own scroll, and nothing else on the layout changes.
2. **Dates read dd-mm-yyyy** on the desk and its three pages (Bills awaited, Implant stock ledger, The month).
   - A date can be typed as `dd-mm-yyyy`, `d-m-yy`, `dd/mm/yyyy` or `yyyy-mm-dd`. It is stored as before, as ISO
     `yyyy-mm-dd` (`bills.bill_date`, `bills.paid_on`, `implant_payment.day`).
   - A date that cannot be understood is refused with one plain line, and nothing is saved.
3. **The misread-date flag** now fires only for a date before 2015-01-01, more than 7 days after the scan day, or more than
   400 days before it. A year-old bill scanned late (Shri Ram B-0001) is no longer flagged.
4. **The owner's own name read as the supplier** (B-0010, B-0011, B-0012). The Supplier box shows a grey line: *"This is
   your own name — the reader took the buyer. Type the supplier, or choose Miscellaneous if it is the clinic's own
   paper."*
   - If Claude read a different supplier, the line offers it: *"Claude read: <name> — use it"*.
   - The own-name words are the same list `clinic_papers.suggest()` uses (`_words(db, "own_name")`). There is no second list.
5. **Claude's reading beside each box.** Under Supplier, Bill no, Date and Amount there is a small grey line, *"Claude read:
   <value> — use it"*, but only when Claude's value differs from the stored one.
   - How a difference is judged: supplier by its first two words; number with spaces and case ignored; date as in item 2;
     amount to the rupee.
   - One tap fills the box. Nothing is saved until Save.
   - Never shown for a pharmacy paper, or for a Personal paper to a manager. Who the paper is made out to is never shown.
6. **The Purchases list's Lane column** shows one word per lane: *Clinic · Pharmacy · NK Pathology · Personal expense ·
   Other document*. It used to show "Clinic" on a rejected row and "Clinic bill" on a live one, because one branch cut the
   label at the first space and the other at the dash. An old row with no lane is named by its kind.
7. **The installer's /desk probe accepts 302 only**, the login gate (S551 review K2 note N1).
8. **Claude never reads a patient's paper.** Both the scan app's own reader (`_s550_claude`) and the re-read of older scans
   (`claude_reread.py`) skip `subgroup='patient_paper'`.

**Files.**

| File | FROM → TO |
|---|---|
| `/root/assetapp/sorting_desk.py` | `bb28d8c8` → `7e16fd80` (18 counted edits; `VERSION` stays `S551.2`, `CORRECTIONS = "S555"` added) |
| `/root/assetapp/asset_register.py` | `c107c6bb` → `7ac38664` (5 counted edits) |
| `/root/assetapp/claude_reread.py` | `47548ab9` → `d9b75e78` (3 counted edits) |

- **Not changed:** `clinic_papers.py`, `claude_reader.py`, `scanner_widget.js`, `packs.py`, the finance side, the portal and
  the DUTY_MAP.
- **No database change.** The installer still takes `assets.db.bak_S555_<time>` by the backup API before placing.
- Only `assetapp` is restarted.

**Install (server), after the publish:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S555_DESK_CORRECTIONS/install_s555.sh
```

`DRY=1` before `bash` stops after the walk and the control, before anything is placed.

**Undo (server):**

```
\cp -p /root/assetapp/sorting_desk.py.bak_S555_bb28d8c8 /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/claude_reread.py.bak_S555_47548ab9 /root/assetapp/claude_reread.py && \cp -p /root/assetapp/asset_register.py.bak_S555_c107c6bb /root/assetapp/asset_register.py && systemctl restart assetapp
```

**Proof (14-Oct-2026, on the box, in /tmp only).**
- **`walk_s555.py`: 19 checks, all green.** It runs on a backup-API copy of the live database with made-up rows only and a
  made-up today of 15-Jun-2031.
  - Item 1: the served desk's element structure and its CSS.
  - Item 2: the dates on all four pages, each accepted form stored as ISO, and a bad date refused with nothing written.
  - Item 3: the 358 / 400 / 401-day edges, 7 and 8 days after, and 2014.
  - Item 4: the own-name line, Claude's offer, nothing changed until Save.
  - Item 5: lines only where values differ; never `made_out_to`; never a Personal paper to a manager; never pharmacy.
  - Item 6: live, rejected and old rows of every lane.
  - Item 8: both readers, with a counting stub; no network.
- **The control: the same walk on the live (S551) files goes red.** 13 of 19 checks are red, including every named check:
  W2, I1, I2a, I2b, I2d, I3, I4, I5, I6, I8a, I8b.
- **S551's own walk on the new files:** 86 of 87 green. L4 is red only because it looks for the old date form
  "checked up to 15-Jun-2031" (item 2 makes it 15-06-2031). A /tmp copy with that one string written dd-mm-yyyy gives 87 of
  87.
- **`rehearse_s555.sh` on a made-up root: five outcomes.**
  - Green.
  - ALREADY INSTALLED.
  - A forced red after placing restores.
  - `/desk` 404 restores.
  - `/desk` 200 restores (302 only).
