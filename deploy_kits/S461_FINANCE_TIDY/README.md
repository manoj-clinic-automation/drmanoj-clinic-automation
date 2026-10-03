# S461_FINANCE_TIDY — finance app tidy-up (session 292, 03-Oct-2026)

At the owner's word of 03-Oct-2026: "you can proceed with these two … 2. Finance app tidy-up".
Source: the S291 whole read of `finance_app.py` (`FINANCE_APP_WHOLE_READ_S291.md`, leads 1, 6, 7 and the unguarded parses).

**One file changes:** `/root/finance/finance_app.py` `40aef4df` → `26a532a6`. No figure, row, gate, role or route changes.

| # | what | before | after |
|---|---|---|---|
| 1 | `/finance/health` | a row's label, words and hint went into the page unescaped; a hint naming `<the medical address>` was swallowed as a tag | everything escaped; a hint may still carry a whole link to a page of this site |
| 2 | `--selftest` | fake scans written into the live scan folder; an abort left a full copy of the database and the smoke folders in temp | scans go to a throwaway folder; everything the run made in temp is removed at exit, aborted or not |
| 3 | the *mounts* health row | an `init()` failure in the 14 print-only mounts was invisible; the stored reason was never shown | all 27 mounts record their failure; the row shows the reason |
| 4 | `?days=` on `/finance/api/days`, `/finance/clinic/api/days`, `/finance/api/orthotics` | `abc` or a huge number was a 500 | the default window |

**Deliberately not in this kit** — each changes what money or staff screens do and gets its own walked kit:
role checks on the open routes (lead 2) · the Staff-Ledger post inside `api_approve`'s loop (lead 3) ·
the negative-cash guard (lead 4) · the apply-abort rollbacks and the refused-file re-send (lead 5).

## Files
- `apply_s461.py` — the edits: 14 exact anchors (one found twice) and the 14 print-only mounts; refuses unless the file is `40aef4df` and every anchor is found the stated number of times.
- `walk_s461.py` — 61 checks. Copies the app's code to a scratch folder as *old* and *new*, makes an empty database from the app's own schema, and shows each fault on the old file and gone on the new one. Opens no live database and no live scan folder.
- `install_S461_FINANCE_TIDY.sh` — gates → build lock → pin → apply on scratch → walk → backup `.bak_S461_40aef4df` → rename into place → restart `clinic-finance` → door and journal checks → restore on red. `DRY=1` places nothing. Its last step only counts what earlier test runs left behind; it removes nothing.

## The owner's line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S461_FINANCE_TIDY/install_S461_FINANCE_TIDY.sh
```

If Sanjeevni's S454 changes `finance_app.py` first, this installer refuses at step 2 and the kit is rebuilt on the new bytes.
