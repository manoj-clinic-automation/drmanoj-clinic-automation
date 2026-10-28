# START HERE — SESSION 361 — written at the S359 close (the Sanjeevni chat), 28-Oct-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). In the device VM, `day_open.py` needs its paths: `--tools $HOME/mnt/Downloads/_kbtools --repo $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation --kb $HOME/mnt/Downloads/ClaudeCowork --ssd $HOME/mnt/ClinicBackup/DrManojClinic_Automation --roots $HOME/mnt/Downloads $HOME/mnt/dr-manoj-git $HOME/mnt/ClinicBackup` (the defaults are Windows paths).
2. The rulebook for every build is **the charter v1.1 — `claude/S307_BUILD_CHARTER_v1_1.md`** beside the parent's `BUILD_NORM_v1.md` (D704). The plan of work is `claude/S327_SANJEEVNI_RESTRUCTURING_PLAN.md`. **The close is `CLOSE_ROUTINE_v1`** — this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S359\close_parts\` (copy it, change what changed).
3. The brief of this close is `S359_BUILD_BRIEF.md`; the Book is `SANJEEVNI_SYSTEM_BOOK_v1_37_S359.md` (§15AB is S359); the kits `deploy_kits\S662_SMALL_LIST\`, `S664_PAY_AND_NAMES\`, `S665_EXPIRY_DAYTIME\`, `S668_EXPIRY_START_OF_DAY\`, `S669_DUMP_SECTIONS\`, `S671_CREPE_MEDICINES\` (all frozen).

No incident is open. **Six kits are live** (S662, S664 — 26-Oct; S665, S668 — 27-Oct; S669, S671 — 28-Oct dawn). **S644 is live** (the levels model, in shadow; `order.source = marg_sheet`).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **361 is RESERVED for the Sanjeevni chat at this close.** The parent's 360, the Scan App chat's 355 and the NK Pathology chat's 356 were open at this close. Take what the board says and say so in your first line.
- Kit numbers are claimed before the scratch folder is named (F-515); D and F numbers the moment they are minted (F-920). Read every PLANNED line on the board before touching a file it names (D646).

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* Never `git` there (F-511). **Build road: in the chat itself.** **What S339–S359 learnt about building offline (keep it):** the live code = the newest bundle + the pending kits' `make_*.py` in order; a walk's "old = new" runs the old and new bytes on the same database copy; **a walk's controls stand on its OWN rows (F-998)**; **a walk on a live page asserts what the page always shows (F-1020)**; **read a captured Marg text's title before printing any row of it (F-1010)**; **the pin list is newest-first — a kit superseded by another kit is recorded in prose, never as a row (S353, S359)**; **the built-in browser on manojz is signed in as Shavez — the owner's view is read in his Chrome (Claude in Chrome), read only**; **a walk that needs the spine runs its live-shape checks only on the box (no spine copy leaves it) — the installer stops before placing if they are not green (S665, S668)**; **a kit writes to the database through python — the box has no `sqlite3` command (F-1036)**; **a refused kit is a NEW folder (`_R2`), never an edit of the published one (F-512, F-1036)**; **read the owner's screen after every install — S665 was right and VOM L stayed (F-1034)**; **Marg prints one item at different widths in different reports — key nothing on one report's spelling (F-1035)**.

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)**

1. **The board** — every message `read:false`, every note; say in one line how many are this project's (at this close: none; the growth chat's two are its own; the Scan App chat has this chat's `sanjeevni_S359_1`).
2. **The day's checks** — `day_open.py --read` (run it if the page is not today's).
3. **The pin pass on the 29-Oct bundle** with `live_pins_S359close.txt`: this project's DECLARED-PENDING — S669's `/root/finance/expiry_watch.py` 23e0a5bf. State match · declared-pending · unexplained.
4. **The expiry watch's first mornings on S665:** in the newest database copy, `stock_expiry_run` should hold one daytime run a morning (the `--if-newer` line, `sales_to` = the previous day) beside the 23:57 one; `near_expiry.log` quiet otherwise. If it holds more than two a day, read why before anything else.
5. **Amir:** Vinbactum DS (25 inj, batch 6347, 02/2025) — gone from the closing after his next visit? The two September payment messages (A.A. Pharmaceuticals, Deepam Pharma — `supplier_msg` 52, 54) — sent by *Bhejo* yet?
6. **1-Nov (Sunday) 05:30:** the monthly reseed moves Deepam, Janta and L.K. Drug House to a 2-day lead (three orders each, median 2 days); nobody else. Read it on 2-Nov.

**B · THE WORK**

1. **The shadow weeks of Kit II** — read, not built. **The first levels week scores on the night of 1-Nov** (`order_score_latest.json` `by_model`, on the box; his fold's score line). D673's bar (three weeks at 85 % / 80 % / no more stock-outs) decides when the switch (`order.source = system`) is brought to him — never before, never by itself.
2. **After the 1-Nov score, one kit:** F-1028 (the fold: the *last list stood on* line from `relist.inputs` / `made_through`; the relist line in words, not JSON; carried lines say `carried`) on S644's pins (`porders_s454.py`, `finance_approvals.html` — the parent's template, PLANNED line first), and F-1025 (`spine_build.py`: a finding equal to an entered voucher's change classed VOUCHER; vouchers never into `sp_move`). Walk with a control; the shadow score must not move.
3. **The section kit (F-1035's residue):** the S268 word lists in `section_map.py` and `stock_app.py` still class CREPE and CAST SHOE as consumables for a name the table does not hold; and names Marg added since 18-Sep have no row. Bring their rows in by his rulings (D795 and the twins), with a walk over every name in the database — old = new except the named ones.
4. **Parked until the buying switch (D796):** F-984's stock readers onto `order_track`, one `newest_stamps()` door, `_s577_record`'s writable Ctx on a GET — all under the shelf figure the shadow score reads.
5. **Darpan's tab header line** (B.2a) — with the kit that moves `order.source`, after its mock and his yes; not before.
6. **PARKED by his word — do not start unasked:** F-802's permanent fix.
7. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER INSTALL:** `deploy_kits\S638_EXPIRY_WATCH\` (frozen; S642 → S668 → S669 are its live line). **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690). **NEVER WRITE `order.source` FROM A KIT** (D673, D785). **NEVER CHANGE THE EXPIRY PAGE ITSELF** without his word (D780, D793) — S665/S668/S669 changed how its list is made, not the page.

**A STAFF SCREEN CARRIES ONLY "DO THIS" LINES (D708) — AND A LINE ON IT RESTS ON A FACT NOBODY CAN TAP WRONGLY (D712) — THE ONE RULED EXCEPTION: RECEPTION'S YUVIKA CARD WAITS ON DARPAN'S हाँ (D749).** **NO FIGURE TO TYPE, EVER (charter rule 8).** **THE STOCK PROOF'S VERDICT IS THE OWNER'S LINE ONLY.** **A VOUCHER NEVER TAKES MARG BELOW ZERO OR PAST THE SHELF FIGURE; A SETTLED ITEM IS NEVER RAISED AGAIN (D715).** **A LINE LEAVES THE ORDER LIST ONLY WHEN MARG CLOSES IT (D716) — A MEDICINE THAT DID NOT COME GOES ON THE DEALER'S NEXT ORDER BY ITSELF (D757) — A SUBSTITUTE NEVER CLOSES A LINE BY ITSELF (D760).** **A RESCAN KEEPS ITS OWN NEW NUMBER (D759).** **ONLY THE OWNER CHANGES A DEALER'S NUMBER (D731).** **A CLOSING (OR A BATCH STOCK) TAKEN BEFORE THE DAY'S FIRST SALE IS THE START OF THAT DAY (D740).** **CLAUDE READS THE PHARMACY BILLS; SARVAM IS OFF BY HIS SETTING (D747).** **DARPAN'S TAB CARRIES THE PURCHASE CUT-OFF LINE, NO STOCK-DAY LINE (D746).** **ONE WHATSAPP PER ORDER, FROM THE ONE ORDER LIST (S605, S662). ONE ORDER LIST FOR FOUR PEOPLE (D757).** **EVERY PHARMACY SCAN UPRIGHT (D758).** **AMIR'S MONTH PACK STAYS UNTIL THE NEXT IS READY (S626).** **A MARG PACK CHANGE IS A NEW ITEM (D763).** **THE BATCH STOCK EXPORT IS NEVER THE CLOSING STOCK; THE EXPIRY WATCH IS READ-ONLY (D771, D780) — ORTHOTICS APART IN THE DUMP (D777).** **THE MORNING REPORTS: SHAVEZ, AND SHIVANI WHEN HE IS AWAY (D778).** **THE BUYING MODEL IS SCORED IN SHADOW; THE SWITCH IS HIS WORD ON D673'S BAR (D678, D785).** **HIS HOME: FOLDERS OPEN IN PLACE, THE EXPIRY WATCH BOX, TWO SANJEEVNI FOLDERS (D793).** **CREPE BANDAGES, EVERY SIZE, AND LEUKOBAND ARE MEDICINES — SOLD, NOT CONSUMED (D795).**

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the pack-change build (F-1000); the rescan's number (D759); the orthotic names as Amir typed them (D709); the learnt names (D685); Kedar's July balance; the four appliances' category; the staff's *Aaj ka kaam* lists — the parent's; the bill line's design (D712); NORTIMER TAB in the 6-Sep count (D715 b); the GST composition flow — the parent's; older purchase bills for the name list (D762); a reader for the bank's alert e-mails (D779); the expiry watch's screens (D780, D793); the shape of Kit II (D785); the S335 small list (D796 — settled; its parked three wait for the switch).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat (03-Sep).** **ALL-CAPS = urgent.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first. Never a step that is not his.**
6. **His board carries only what needs him and what he should know — every close answers what he typed there.**
7. **His own items are deferred** — name only what has become urgent, and say why. **His approvals are few and arrive together.**
8. **Never put a technical choice to him** (03-Sep) — decide, say it in one line, carry on. **A screen for staff: the mock first (03-Oct).**
