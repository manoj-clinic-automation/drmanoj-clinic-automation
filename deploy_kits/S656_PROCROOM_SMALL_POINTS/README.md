# S656_PROCROOM_SMALL_POINTS — the reviews' small points on the Procedure room file

**Why.** The independent reviews of S635, S637 and S643 left small points on `procroom.py`, carried since the S346 close
(Runbook v270 §2C item 3; START_HERE_SESSION_355 B1). Board `_numbers` v709 → v710 (kit S656, PLANNED line on this project's own
file). Built in the Scan App chat, session 355, 26-Oct-2026.

**What changes — and what does not.**
- **A retired procedure in the ILI rule** (`ili_kit()`): already right in the live file — its query takes only `active=1` procedures
  from his rate page. No edit; the walk proves it (P1, green on both sides).
- **A column for an old table:** `proc_use.lkey` (S637's per-side key) is added at mount to a `proc_use` table made before the column
  existed — once; a second mount or worker changes nothing; the rows are kept (`ADD_COLS`, in `ensure()`). On the live box the table
  was made with the column, so nothing changes there; the installer prints whether the column is present.
- **One pre-match rule at the month end (`photo_lines_for`).** A photo's lines compared with a scan are pre-matched by the desk's own
  rule: products in use or rarely used, and a retired product only where that scan already holds it. Before, the match and his Save
  used every product while the month's table and the editor used only the ones in use — so a slip whose product was retired after
  Shavez sorted it read "photo 5, not on the scan", lost the photo's rate on that line, and **a second photo of the same slip was
  counted again in the month's total**; and where a retired and an in-use product share the same words, his Save kept wrong quantity
  words and a second photo was called "not scanned". Now the match, `fits()`, the quantities, the rates beside the lines and the
  month table's "up/down" rate words agree.
- **One narrow case reads differently (named, not a fault):** a photo line whose words tie between a retired product the scan does
  NOT hold and an in-use product now pre-matches the in-use one (before: no pre-match, its name). If that scan's line was saved as
  *Not on your list yet* with exactly the photo's words, it now reads "not on the scan" until he picks the product.
- **The month end keeps typed rates across *Its scan*.** Changing the scan reloads the lines; the rates he typed (only those) come back
  on the lines of the same product (two lines of one product each keep their own), with a line saying so — only on the page that
  change opened, within two minutes, once. Kept in the browser only; nothing is saved by the change.
  (Cosmetic, named by the review: where the old page had two lines of one product and he typed only the second, that rate lands on
  the first line of that product on the new scan; the note shows and nothing is saved until his Save.)
- Nothing on any staff screen; no rate on a staff screen; the parent's `finance.db` read only, as before.

**Files and pins (FROM → TO).** `/root/assetapp/procroom.py` `f6578535` (S648's, confirmed by the 26-Oct bundle) → `e51c00a1`,
13 counted edits (`edits_s656.py`; `make_s656.py` applies them to the live bytes on the box and refuses unless the result is the
kit's whole file). No other file; no data step. Read only, pinned: `sorting_desk.py bb206e5d`, `asset_register.py 63a8b15b`,
`clinic_papers.py 89a3cd0a`, `claude_reader.py 1277e80d`, `claude_reread.py ed7023d2`, `asset_machine.py 7dbd5e0c`,
`stationery.py b6ce217a`, `batteries.py bb082b4c`, `xray_costs.py 5823bae2`.

**Kit.** `edits_s656.py` · `make_s656.py` · `procroom.py` · `walk_s656_app.py` (every S648, S643 and S637 check, plus P1–P9 and, in
the chat, B1–B4 in a real browser; made-up slips, products and photos only; `--expect-red` on S648's file: A0, P2, P4–P9 and B1 red,
every other green; the browser checks proven able to fail by breaking the page's script on purpose) · `install_s656.sh` · `rehearse_s656.sh` (R1–R7) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S656_PROCROOM_SMALL_POINTS/install_s656.sh`

**UNDO (one line):** `\cp -p /root/assetapp/procroom.py.bak_S656_f6578535 /root/assetapp/procroom.py && systemctl restart assetapp`
