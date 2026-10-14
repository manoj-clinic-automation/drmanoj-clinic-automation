# S551_SORTING_DESK — the sorting desk (D722, S315)

**What it does.** Dr Manoj and Shavez get one sorting desk on the laptop, at
`https://followup.dr-manoj.in/scanapp/desk`:

- the waiting papers on the left (newest first, folds away);
- the scan large in the middle (the browser's own viewer: every page and zoom; *Turn ↻* turns the view only);
- on the right, what was read (correct anything), *What kind of paper* (Bill · Estimate slip · Challan) and one list,
  *Where does it go?*, in the board's six groups;
- one **Save — next paper**. One Save is one transaction: it files the paper, accepts it (a challan waits for its bill) and
  opens the next paper without reloading the page.

Beside it are three pages:

- **Bills awaited**: challans by supplier. Each supplier is set once to Monthly bill, A bill now and then, or Paid on challan.
- **Implant stock ledger**: owed, paid and balance per supplier. Payments are noted here and voided, never deleted. There is
  also *Checked against their statement up to today*.
- **The month**: section by section — Procedure room · X-ray films · Others · Implant stock · Construction work · Clinic
  equipment. It also shows *Kept apart* and *Not in the totals*. It replaces the two old history pages in the menus; both
  old pages stay reachable, with a banner.

A patient's paper is set aside on the desk (*A patient's paper — surgical case pack*). It is left out of every total and is
never read again. Nothing is guessed. A suggestion is shown, never saved. Yuvika is never pre-selected. A section, or whose
expense a paper is, is set only by a person's Save. A paper already accepted can be changed on the desk by a person, and
the change is audited (the owner's widening, D722).

**The tidy-up.**
- The header reads *Scan app & assets*.
- The front page carries a **Switches** card (owner only): Smart scanner · Reception buttons · Sorting desk for Shavez ·
  Claude reading →.
- The instant lane drop-down is gone from the bills list; each row links to its paper.
- The edit page reads *Edit bill* and keeps a Lab / Expense / Document / Pharmacy / Challan paper's kind.
- A paper's month can be set back to 2015 on its own page. The intake keeps its four months.
- The re-read refuses a patient's paper.

**Switched off for Shavez.** The kit installs with `desk.on` absent (OFF). Until Dr Manoj switches it on from the Switches
card, Shavez sees one line: *"The sorting desk opens when Dr Manoj switches it on."* Dr Manoj can use the desk at once. The
old papers pages keep working either way.

**Files.**

| File | Status |
|---|---|
| `/root/assetapp/asset_register.py` | `3d5a36e3` → `c107c6bb` (19 counted edits) |
| `/root/assetapp/clinic_papers.py` | `5b197fb5` → `058c9bcb` (12 counted edits) |
| `/root/assetapp/sorting_desk.py` | new, `bb28d8c8` (fix round 1; the first round's was `3daa1e3a`) |

The database gets four new tables (`challan_supplier`, `implant_payment`, `implant_check`, `desk_audit`) and two new
columns (`bills.paid_on`, `bills.paid_amount`). It also gets the setting `desk.floor` (the install day): scans older than
that are not flagged on the desk.

These are not touched: `scanner_widget.js`, `claude_reader.py`, `claude_reread.py`, `packs.py`, the finance side and the
portal. Only `assetapp` is restarted.

**Install (server), after the publish:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S551_SORTING_DESK/install_s551.sh
```

`DRY=1` before `bash` stops after the walk and the control, before anything is placed.

**Undo (server):**

```
cp -p /root/assetapp/asset_register.py.bak_S551_3d5a36e3 /root/assetapp/asset_register.py && cp -p /root/assetapp/clinic_papers.py.bak_S551_5b197fb5 /root/assetapp/clinic_papers.py && rm -f /root/assetapp/sorting_desk.py && systemctl restart assetapp
```

The new tables stay; nothing reads them after the undo. The database backup `assets.db.bak_S551_<time>` is needed only if
data written by the desk must be reversed.

**Fix round 1 (S551_FIX1, 14-Oct-2026)** — the kit was revised in place before any install:
- C1: after the restart the installer also needs `/desk` to answer the login redirect (302); anything else restores.
- C2: a paper set aside as *A patient's paper* is left off Bills awaited, the desk's "covers these challans" box, the
  Waiting list and every count on The month. It is counted only in *Kept apart*.
- C3: an accepted paper saved as *Challan* goes back to draft (or its lane's status) and waits, audited as
  `desk_challan_reopened`, so it can be joined to its bill.
- C4: a Personal challan never reaches a manager: it is not in his covers box, his supplier note, his Waiting reasons or
  Bills awaited, and the join refuses it on the server.
- N2–N6: H2 seeds its own made-up row. The control names the checks that must be red. A locked database at mount is retried,
  then ignored. A closed challan is never owed. "Rate before" reads only the consumables groups or the row's own section.

**Proof (14-Oct-2026, on the box, in /tmp only).**
- The walk has 87 checks, all green. It runs on a backup-API copy of the live database, with made-up rows only (suppliers
  WALKA–WALKY, a made-up today of 15-Jun-2031). It covers:
  - every destination and *Blank — discard*;
  - the challan modes and their amber rules;
  - the ledger;
  - the D710 hold and the S441 set-aside, each answered both ways;
  - Personal hidden from the manager;
  - the switch OFF and ON;
  - a fresh import that moves nothing a person placed;
  - The month equal to `/papers/month`;
  - reception refused on every new route;
  - the fix round's checks FC2, FC3, FC4, FN4, FN5, FN6.
- The same walk on the live (old) files goes red: 80 of 87 checks red. All 12 checks the control names are red (W2, S3, W3,
  C2, R2, V1, H2, FC2, FC3, FC4, FN5, FN6).
- `rehearse_s551.sh` rehearsed the installer on a made-up root, with four outcomes:
  - green;
  - ALREADY INSTALLED;
  - a forced red after placing, which restored the files to the FROM pins;
  - health 200 while `/desk` does not answer, which also restored (C1).
