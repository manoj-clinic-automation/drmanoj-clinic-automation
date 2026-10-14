# S557_MACHINE_PAGES — the machine pages, and the scan app's leftovers (D646 claim, S315 — the scan app's final kit)

**What it does.** The owner's D719: *"an asset's parts, cover history and spends, each with its scanned bill."*

1. **The machine page** (`/scanapp/assets/<id>`) now opens with:
   - **One cover line** — *"Covered: AMC by <provider> till dd-mm-yyyy"*, *"Under warranty till dd-mm-yyyy"* or *"No cover"*.
     It uses the live cover with the latest end date. The line turns amber in its last 30 days and red once the cover has
     lapsed.
   - **One line of totals** — *Bought for ₹X (dd-mm-yyyy) · Spent since ₹Y on N repairs/services · Cover paid ₹Z*. A
     manager sees no ₹ figure on a machine whose price is hidden (the app's existing `hide_price` rule).
2. **Three folds below the existing details**, the first one open:
   - **Parts.** Each part shows its make, model, serial, fitted-on date, warranty date and its paper. *Add a part* adds
     one. *Replaced / removed* marks a part with the date and who did it; the part moves into a folded *Removed parts* list
     and is never deleted.
   - **Cover history.** Every warranty, AMC, CMC, insurance or other period, newest first, with its cost and paper. A
     renewal is simply the next period. A mistake is voided, struck through and never deleted. The machine's old single
     contract fields are shown once, read-only, as *"From the old record: …"*. No data is moved.
   - **Spends.** Repairs, service visits and spare purchases come from the existing service log, with the totals per year.
     The old *Add service* form keeps working. A spend can carry its paper, or have one linked afterwards.
3. **Renewal reminders.** Every live cover and every live part's warranty puts **one** reminder on `/renewals`
   (`expiries`; label *"AMC — <provider>"* / *"Part warranty — <part>"*).
   - The reminder is created once, kept in `expiry_id` and updated, never duplicated.
   - A renewal resolves the older period's reminder. A voided cover or a removed part resolves its own.
   - A heal runs at every start and when Renewals opens. It re-links a lost link to the same reminder.
4. **"Its paper"** is a *B-____* box on every form.
   - It refuses a pharmacy paper and a patient's paper, and, for a manager, a Personal paper.
   - The paper's own page reads *"Linked to <machine> as purchase / part / cover / spend"*, and so does the desk's
     *Clinic equipment* note.
   - A Clinic-equipment paper offers **+ asset record** (on its page and on *The month*). This opens a new machine form,
     pre-filled from the paper: supplier, date and amount, plus the item, make, model and serial from Claude's reading when
     there is one.
   - The new machine keeps the paper as its purchase bill (`assets.bill_id`, the A-D20 item bridge, the A-D24 backfill).
     This part is the owner's only.
5. **Who.** The same gate as the asset pages: the owner and managers can add and change. Reception never can.
   - The switch **`machine.on`** is installed **absent = OFF**. While it is off, a manager sees the machine page exactly as
     before (byte for byte, walk K1) and every new route refuses him. The owner has it at once.
   - The Switches card gains a fourth line, *Machine pages for Shavez*, through S551's `POST /desk/switch`.
6. **Leftovers.**
   - **B1:** each lane is one word (*Clinic · Pharmacy · NK Pathology · Personal expense · Other document*, S555's
     `LANE_WORD`) on the owner's and managers' bill page, lanes page, papers pages, the desk and Bills awaited.
     Reception's intake and slip are unchanged (intake HTML byte for byte, walk K2).
   - **B2:** a Claude amount or quantity that is NaN, inf or text is ignored. The paper still opens, and its JSON stays
     strict.
   - **B3:** a stored date with a time part is the same day, so no spurious *Claude read* date line appears (S555 review
     N2). The undo line uses `\cp -p` (review C1).

7. **Fix round 1 (S557_FIX1, the independent review's BL1 / C1), in `asset_machine.py` only.** No table uses
   AUTOINCREMENT, so SQLite gives a deleted newest machine's, paper's or reminder's id to the next new one.
   - A link is trusted only with its fingerprint. `asset_part` and `asset_cover` carry `asset_created_at` (the machine's
     `assets.created_at`) and `bill_created_at` (the paper's `bills.created_at`); `service_logs` carries `bill_created_at`
     beside `bill_id`. All are written in the request that makes the link.
   - A row whose machine or paper no longer matches is not shown on that machine or as that paper. The heal (at every start
     and when Renewals opens) **detaches** it: `asset_id = -asset_id` (its reminder link cleared), or `bill_id = NULL`.
     Each one is audited in `desk_audit` (`machine_detached` / `machine_paper_detached`). Nothing is deleted.
   - A reminder is S557's own only if its id is the row's `expiry_id`, it is `entity='asset'` for that machine, and its
     label starts with one of `OWN_PREFIXES` (*AMC — · CMC — · Warranty — · Insurance — · Other — · Cover — · Part warranty —*).
     Any other row is never updated or resolved: the link is let go (`machine_reminder_let_go`) and a fresh reminder made.
     The adoption step keeps the same three tests.

**Files.**

| File | FROM → TO |
|---|---|
| `/root/assetapp/asset_register.py` | `7ac38664` → `9e94b11c` (10 counted edits) |
| `/root/assetapp/sorting_desk.py` | `7e16fd80` → `91a04674` (15 counted edits; `VERSION` S551.2 and `CORRECTIONS` S555 kept, `MACHINE = "S557"` added) |
| `/root/assetapp/asset_machine.py` | NEW → `66c37197` (fix round 1; was `ec874720`) |

- **Read only, pinned:** `clinic_papers.py` `058c9bcb`, `claude_reader.py` `3894dc23`, `claude_reread.py` `d9b75e78`.
- **Not touched:** `scanner_widget.js` (`1143c77b`), `packs.py`, the finance and Sanjeevni side, the portal, and the
  DUTY_MAP.
- **Database (additive, by `asset_machine.ensure()` after the backup):**
  - `asset_part` and `asset_cover`, as the brief, each with the two fingerprint columns `asset_created_at`,
    `bill_created_at` at the end (fix round 1).
  - `service_logs.bill_id` and `service_logs.bill_created_at`.
  - No existing row or field is moved or changed; `machine.on` is not written.
- Only `assetapp` is restarted.

**Install (server), after the publish:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S557_MACHINE_PAGES/install_s557.sh
```

`DRY=1` before `bash` stops after the walks, before anything is placed. The installer needs the S555 and S551 kits beside it
(their walks are the regression).

**Undo (server):**

```
\cp -p /root/assetapp/sorting_desk.py.bak_S557_7e16fd80 /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/asset_register.py.bak_S557_7ac38664 /root/assetapp/asset_register.py && mv /root/assetapp/asset_machine.py /root/assetapp/asset_machine.py.undone_S557 && systemctl restart assetapp
```

The two new tables and the column stay (additive, unused once undone). The database backup `assets.db.bak_S557_<time>` stays.

**Proof (14-Oct-2026, on the box, in /tmp only; fix round 1 re-run 11:19–11:22 IST).**
- **`walk_s557.py`: 41 checks, all green.** It runs on a backup-API copy of the live database with made-up rows only and a
  made-up today of 15-Jun-2031. It covers A1–A7, B1–B3, K1/K2 (byte-for-byte against the live files' pages), F1a–F1c
  (ids re-issued after a delete), sizes and isolation.
- **The control on the live (S555) files: 34 RED.** Every named check is red: W2, A1a–f, A2a–b, A3a–c, A4a–b, A5a–b,
  A6a–e, A7b–c, B1a–d, B2, B3 and F1a–c.
- **Control 2 (fix round 1): the new app files with the previous `asset_machine.py` (`ec874720`)** are red on exactly
  F1a, F1b and F1c (and W3, the schema): the deleted machine's AMC shows on the new machine and the app's own *Warranty*
  reminder is rewritten; the new paper reads *Linked to … as part; … as cover*; the app's *Part warranty:* reminder is
  rewritten. This run is a dev step on the box; the installer runs the walk and the first control as before.
- **Regression on the new files:**
  - S555's walk: 19 of 19 green.
  - S551's walk: 87 of 87 green, with its one date line in S555's agreed dd-mm-yyyy form.
- **`rehearse_s557.sh` on a made-up root: five outcomes.**
  - Green.
  - ALREADY INSTALLED.
  - A forced red after placing restores.
  - `/desk` 404 restores.
  - `/desk` 200 restores (302 only).
