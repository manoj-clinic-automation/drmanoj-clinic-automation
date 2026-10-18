# S586_PORTAL_TILE_GROUPS — the portal home regrouped: group tiles with submenus, eight tiles retired, Dr Bhawna's seven

**Why.** The owner, 15:24–15:48 IST 18-Oct-2026 (**D739**): *"rearrange my portal tiles other than the Sanjeevni tiles … the old
Google Apps Script related tiles … can be retired … others like doctors can be grouped together … when I click on one tile, a submenu
opens"*; then *"Dr Bhavna's PWA is also too much cluttered … she should also have the minimal apps which she actually is required to
use"*; his edits: *"patient records, check karein both to be removed, staff tile needed, mine ok"*. The approved mock-up:
`https://claude.ai/artifact/QFFLTy41cekN5udgvYVyhR` (v2). Board `_numbers` v492 → v493: kit S586, D739, PLANNED line on
`/root/portal/portal.py` 963911cc and `/root/portal/tile_grants.json`.

**What changes — display only.** No role, grant or page gate changes in code; Dr Bhawna's narrowing is in the grants file, where
every per-login display rule already lives (S222). Nothing granted, nothing withdrawn from anybody's login.

1. **Ten groups** replace the six sections: Patients · Surgery · Calls & WhatsApp · Docterz & clinic day · Accounts & month-end ·
   Staff · Assets & papers · Sanjeevni Medicos · Personal · System. `GROUP_META` gives each its face (icon, one line).
   **The fourteen Sanjeevni tiles are not edited** — their dicts are byte-identical; only their group label moves, so they sit together
   behind one tile (the walk proves it, W2).
2. **Folders.** `tile_grants.json` may carry per login `"folders": ["*"]` (every group) or a list of group labels. A folded group is
   drawn as ONE tile on the home grid with a count chip; tapping it opens the group's tiles as a full-screen sheet (`#g-<slug>` in the
   address — the browser's Back closes it, so does *‹ Home*). A folded group with a single visible tile is drawn flat (no sheet for
   one). When every group is folded the group grid IS the home (the owner); when some are, the flat tiles come first and the folders
   after them under *More* (Dr Bhawna's Staff) — the work someone does most sits highest (his ruling of 03-Sep). No folders = flat,
   exactly as today (every staff and manager login).
3. **"only".** `"only": [tile names]` hides every other tile for that login. Display only: a hidden tile's page keeps its own gate.
   Dr Bhawna: Kal ka hisaab · Physiotherapy · Petty book · Clinic · Report baaki · OPD & X-ray/Proc Slips · the Staff folder
   (Attendance · Staff Register · Salary — approve & lock · Staff Ledger); *Patient records* and *Check karein* also masked (his word).
   From 45 tiles to 7.
4. **Eight tiles retired** (removed from `TILES`, their two config reads with them): UPI Sheet · Monthly Accounting · Vehicle Tracking ·
   CC Statement Saver · Inbox Janitor · Revenue Reconciler · Case Pack · PC fallback · CC Statements → Tally. The *Clinic PC tools*
   chip row goes with them; **Follow-up Tracker** stays `pc_only` under Calls & WhatsApp (shown on the clinic PC alone, as before).
5. **Renewals** opens the server's renewals page (`/scanapp/renewals`, the asset register's) instead of the Google sheet.
6. The staff section order in the grants' `defaults.groups_by_role.staff` is renamed to the new labels (work first, attendance last).

**Files and pins (FROM → TO).** `/root/portal/portal.py` `963911cc` → **`25cb73e7`** (18 counted edits, every anchor found exactly
once in the live bytes; `make_s586.py`). `/root/portal/tile_grants.json` merged in place by `merge_grants_s586.py` (additive,
idempotent; version + 1). The FROM is the S579 TO, reproduced at the S326 open byte-exact from the 18-Oct bundle's `f8b059f6` +
`make_s579.py` (F-472: no pin predicted). No database step. **Restarts clinic-portal only.**

**Kit.** `make_s586.py` (the patcher) · `merge_grants_s586.py` (the grants edit) · `walk_s586.py` (93 checks: W1 every login sees the
same tiles before and after less the retired ones; W2 the retired eight gone, Renewals repointed, the ten groups, the Sanjeevni dicts
unchanged; W3 the owner's home = 10 group tiles, each sheet = its tiles, the live-count hooks still in the page, Follow-up Tracker on
the clinic PC only; W4 Dr Bhawna's seven with Staff last and its sheet of four; W5 every staff / manager login flat, no sheet;
W6 the grants additive, version + 1; Z1 the FROM renders; `--expect-red` = the control on the live file) ·
`install_S586_PORTAL_TILE_GROUPS.sh` · `walk/walk_results_s586.txt` · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Proof (18-Oct-2026, on the PC, offline — Flask 3.1 in the device shell):** the walk **93 of 93 green**; the control **18 of 18
MUST_RED red, 0 wrongly green**; the merge idempotent (second run: nothing changed). The rendered pages for manoj and bhawna were
looked at in headless Chromium at 390 × 844 and 1200 × 900 (the sub-agent's read, `walk/walk_results_s586.txt`). The installer
re-runs the same walk on the box against the live grants before placing anything.

**Install (the owner, after publishing):**
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s586kit && cp -rp /root/deploy/repo/deploy_kits/S586_PORTAL_TILE_GROUPS /tmp/s586kit && bash /tmp/s586kit/install_S586_PORTAL_TILE_GROUPS.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/portal/portal.py.bak_S586_963911cc /root/portal/portal.py && \cp -p "$(ls -t /root/portal/tile_grants.json.bak_S586_* | head -1)" /root/portal/tile_grants.json && systemctl restart clinic-portal`
— then `/portal/login` 200 and `portal.py` back at `963911cc`. Nothing else was touched.

**Later, by his word only:** a different grouping or a tile moved is one line in `_TILE_GROUP`; a login folded or narrowed is one
line in the grants file (no code).
