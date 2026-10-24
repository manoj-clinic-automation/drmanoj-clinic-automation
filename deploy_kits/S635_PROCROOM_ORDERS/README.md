# S635_PROCROOM_ORDERS — his order, the slip joined to it, the month end of Yuvika's WhatsApp (D773 Kit 2)

**Why.** The owner's rulings D773 (S342, 04:39–06:32 IST 23-Oct-2026; the plan's C 3–4): his signed duplicate-book page scanned as an
*order*; Yuvika's slip joined to it — the system fills the lines, he corrects; an order with no delivery after a few days *awaiting*, a
delivery with no order *no order*; at month end his upload of Yuvika's WhatsApp photos, each read and matched to its scan and order —
not scanned · quantity differs · rate up or down · the month's total — the photo kept as the month's bill; no rupee on any staff screen.
The mock-up (`https://claude.ai/artifact/3Doc4wew9qUonpFxZtDD7W`, artboard 4) accepted "okay to start" 08:31 IST 23-Oct-2026; his
"start" for Kit 2, 20:55 IST 24-Oct-2026. Board `_numbers` v639 → v640 (kit S635). Built in the Scan App chat, session 346.

**What changes.**
1. **The sorting desk** (him and Shavez) — with *Procedure room* chosen, the Procedure room box starts with **A slip or a bill (it
   counts)** / **Dr Manoj's order (it counts nothing)**. His order keeps its lines (product, quantity) and a book page number; it adds
   nothing to what was bought. A slip has **Against order** — pre-chosen: the newest order of his at most 14 days before it with no slip
   against it yet — and **Fill the lines from this order** (one tap; the lines become the order's, as suggestions; nothing is saved
   until Save). A slip nothing could be read from is filled from its pre-chosen order by itself. No rupee and no rate anywhere in it.
   A paper re-sorted out of Procedure room loses its role with its lines (kept, voided).
2. **His page — Procedure room** — **Orders and deliveries**: each order of the period (and any still awaiting): its lines, the slips
   against it, *ordered n days ago* · **awaiting — n days** (no slip after his days; 3 to start, his to change under *Your list and
   allowances*) · **part came** with the differences (*Roller bandage 6": ordered 12, came 10*) · *delivered*; and **no order** for a
   slip of Yuvika's (or with no supplier read) **scanned from the install on** — older slips are never called "no order". *Worth a look*
   names both. A link **Month end — Yuvika's WhatsApp**.
3. **The month end** (his only) — `https://followup.dr-manoj.in/scanapp/procroom/month`: **Add photos** (JPG, PNG, WEBP or PDF; the
   same photo twice is refused); each kept in the uploads folder (`procroom_month/`, never deleted) as the month's bill and read in the
   background by the scan app's own reader (`claude_reader.read`, unchanged — no paper's reading is touched). The table: the slip's
   day · its **scan** (or *not scanned*, or *scanned later as B-xxxx*) · that scan's **order** (or *no order*) · **quantities** (*same*,
   or each that differs: *photo 12, scan 10*) · **rates** against the last one for that product and brand (*as before*, or *down: ₹x
   (was ₹y)*) · the amount; **To pay Yuvika for the month**; the scanned slips of the month no photo shows. Opening a slip shows its
   scan's own lines with the photo's rates (the photo's quantity beside a line that differs); **Save** puts his rates on those lines, or,
   when he changed a line, his lines with their rates replace the scan's (the old ones kept). *Not scanned*: Save keeps it as a photo
   slip; if the paper is scanned later and he chooses it, the photo slip is voided — counted once (his page warns while a photo slip and a
   scan of the same day both stand). Two photos of one scan count it once. A photo taken off the month stays on the server, struck through.
4. Not in this kit: Shavez's next-morning screen, use and stock, *Order now* (Kit 3).

**Files and pins (FROM → TO).** `/root/assetapp/sorting_desk.py` `43658394` → `ca9fda74` (9 counted edits: the kit's
mark; the Save hands its body to procroom; the panel's role, order and fill) · `/root/assetapp/procroom.py` `a641f640` → `1ccd1e03`, the kit's whole
file (`PIN_TO_procroom.txt`). Read only, pinned: `asset_register.py 068440f7`, `clinic_papers.py 89a3cd0a`, `claude_reader.py 10118909`,
`claude_reread.py ed7023d2`, `asset_machine.py 7dbd5e0c`, `stationery.py b6ce217a`, `batteries.py bb082b4c`, `xray_costs.py 5823bae2`.
`scanner_widget.js` is not touched; no file of the parent's or of the Sanjeevni chat's is touched. **Data step** (after the database
backup): the two tables `proc_paper` and `proc_photo` (additive, also made by the part's own `ensure()` at mount) and one setting,
`procroom.orders_from` = the install moment (UTC, as the papers' scan times), once — a second run writes nothing. No rate, phone,
account or vendor figure is in the kit (F-185).

**Kit.** `make_s635.py` · `procroom.py` · `walk_s635_app.py` (A0–A1, O1–O10, M1–M17, K1–K2, R1–R3; `--expect-red` = the control on the
live files: every new check red, the no-rate checks and the old pages green) · `walk/browser_desk_s635.py` (headless Chromium: the desk's
panel end to end as a manager — his order marked, a slip pre-joined and filled, the fill link; the month end at 390 px and 1280 px with
a made-up photo added through its form; not run on the box) · `install_s635.sh` · `rehearse_s635.sh` (R1–R8) · `PIN_*.txt` ·
`KIT_ID.txt` · `SUMS.md5`.

**Independent cold review (K1):** round 1 NOT SAFE — one blocker (two photos of one scan counted it twice in the month's total) and seven
corrections (an unread photo could not be matched; the scan choice apart from Save; a stopped reading; Read again during a reading; the
reader's state in plain words; a "not on your list" line refused on a rebuild; the later scan listed twice) — all fixed in place, with
walk checks M12–M15; round 2 NOT SAFE — one blocker its own fix made (a DIFFERENT slip of the same day folded into a scan
another photo was checked onto, its amount left out) and two corrections (a photo asked to read again shown as stopped; the later photos
of a large batch shown as stopped) — fixed: a scan another photo was checked onto is matched only when the photo shares a product with
it; a waiting photo is stopped only when nothing of its month was read for 10 minutes; walk check M16; round 3 NOT SAFE — sharing one product was not proof of the same slip (a second delivery of the same day
still folded in) — fixed: a photo folds into a scan another photo was checked onto only when it FITS inside it (every product on the
scan, none in a greater quantity), and a photo that does not fit is always counted; walk check M17; round 4 below.

**Proof (24-Oct-2026, in the Scan App chat, on the 24-Oct bundle's code with a fresh made-up database):** the walk 33 green / 0 red;
the control on the FROM files 26 red, AS IT MUST BE (the no-rate checks, K1–K2 and R1–R3 green on both sides); Kit 1's own walk on the
new files 29 green, its A0 alone red (it expects the version S634); the browser walk 7 green (its control 6 red, as it must be); the
rehearsal 8 green. On the box the installer runs the walk and the control again on a COPY of the live database before placing.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S635_PROCROOM_ORDERS/install_s635.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/sorting_desk.py.bak_S635_43658394 /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/procroom.py.bak_S635_a641f640 /root/assetapp/procroom.py && systemctl restart assetapp`
— then `/healthz` 200 and the md5s back at the FROM pins. The two new tables, the setting and any photos stay (unread by the old
files); the database backup `assets.db.bak_S635_<stamp>` is needed only if their rows must be removed — say so before using it.
