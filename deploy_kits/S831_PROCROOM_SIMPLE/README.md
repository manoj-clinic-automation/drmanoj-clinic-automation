# S831_PROCROOM_SIMPLE — his Procedure room page, simplified to the mock-up he called final

**Why.** D982: the owner's "Final" (14:40 IST 14-Nov-2026) on the mock-up "Procedure Room — simplified page (mock-up)" v4
(`https://claude.ai/artifact/WFkBPm1Twt7NVM6gTuiUoM`); the written spec `S410_PROCROOM_SPEC.md` (canon). Board `_numbers` v1476 → v1477
(kit S831, this project's own file — no PLANNED line needed). Built in the Scan App chat, session 461, 14-Nov-2026.

**What his page becomes (top to bottom)** — `GET /scanapp/procroom`, the owner's only:
1. The title and the month picker.
2. Six tiles, each a link: Spent (dealer challans counted) · Procedure revenue (ILI and others apart) · Procedures done (casts / slabs ·
   ILI · other) · Fibrecast in stock today (5" 4" 3" 2", red under the reorder level; "after your first count" until a count) ·
   Waiting for you (dealer challans on the desk with no lines saved + Yuvika's photos not checked) · Morning screen (patient slips
   still to fill).
3. Start here, three steps with their state: opening count · purchases (the waiting dealer challans and photos, "Open on the desk",
   "Yuvika's month photo") · used (the morning screen on/off, "Open Kal ke procedures", its switch).
4. Expenses and revenue — the financial year month by month, the X-ray page's way: Bought ₹ · Procedures · ILI revenue ₹ · Other
   procedures ₹ · Revenue less bought ₹; Year so far. NO per-procedure column. Each month opens to (a) what was bought — each
   dealer challan's lines with qty, rate, amount, and the ones waiting on the desk — and (b) the procedures done, ONE ROW PER PATIENT
   SLIP: date, slip no., patient, procedure, fee, its items — correct, add, or fill a "not filled yet" slip, then one Save for the
   month (only the slips he touched are sent — a saved slip's own hidden tick is set by the page when a field in its row changes; the
   cold review's catch, S831), which goes THROUGH THE MORNING SCREEN'S OWN SAVE (`save_morning`, day by day): a slip's earlier record voided and kept, an
   unchanged slip not written. Revenue = the fees on those patient slips from the parent's slip book (read only): `price_p` less
   `discount_p`, a rejected discount not taken off (the parent's day check's rule); "nahi hua" and an approved cancellation left out.
   Procedures and revenue are counted from the morning screen's floor (1-Oct-2026).
5. Stock now: Product · Your count · + Bought since · − Used since · Stock now · Order when below · Day of the count — his count and
   his reorder levels in ONE Save. GLOVES IN WHOLE PAIRS, never a decimal (a box = `proc.gloves_box` pairs, 50 live): "2 boxes + 14
   pairs"; a count of 7.5 pairs is refused. The gloves line: pairs a cast or slab · an ILI · the box, with "change".
6. More, folded: Month-end match · Dealer challans and their rates · Your orders and deliveries · + Add a dealer challan from a photo
   by hand · Your product list and allowances.
7. A fixed "↑ Top".
Wording: Yuvika's papers are "dealer challans" everywhere on this page; "slip" alone means the patient slip.

**What does not change.** Every staff screen: Kal ke procedures' template and code are byte for byte S656's (walk G1). The month end,
the desk, the count door. The parent's `finance.db` is only read (walk G2).

**Files and pins (FROM → TO).** `/root/assetapp/procroom.py` `e51c00a1` (S656's TO) → `38c5bbaa`, by 8 counted edits and 3 counted
blocks (`edits_s831.py`; `make_s831.py` applies them to the live bytes on the box and refuses unless the result is the kit's whole
file). No other file; no data step. Read only, pinned: `asset_register.py 63eba920` (S826), `sorting_desk.py baa7c6aa`,
`clinic_papers.py 89a3cd0a`, `claude_reader.py 1c9e952e`, `claude_reread.py ed7023d2`, `asset_machine.py 7dbd5e0c`,
`stationery.py cfb3d8b5`, `batteries.py bb082b4c`, `xray_costs.py 5823bae2`.

**Kit.** `edits_s831.py` · `make_s831.py` · `procroom.py` · `walk_s831_app.py` (S0–S20 and G1–G3 on the REAL app, a made-up slip
book in the live table shapes, made-up papers and logins; on a copy of a database its own procedure-room rows are set aside IN THE
COPY; `--expect-red` on S656's file: every S check red except S2, and G1–G3 green) · `install_s831.sh` · `rehearse_s831.sh` (R1–R7) ·
`PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S831_PROCROOM_SIMPLE/install_s831.sh`

**UNDO (one line):** `\cp -p /root/assetapp/procroom.py.bak_S831_e51c00a1 /root/assetapp/procroom.py && systemctl restart assetapp`
(every count, reorder level and patient-slip entry he saved stays; the old page reads them as before).
