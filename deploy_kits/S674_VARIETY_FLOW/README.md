# S674_VARIETY_FLOW — the Variety flow on the owner's Stationery page (D797)

**Why.** Variety Stationers supplies stationery to the clinic AND to NK Pathology on jumbled challans, billed about once a year; a
challan scanned on the NK lane (B-0235) never reached the sorting desk, and the Stationery page could not tell a lab line from a
clinic line. The owner ruled the flow on the mock-up `S355_STATIONERY_FLOW_MOCKUP` (28-Oct-2026, his "build" 09:31 IST). Board
`_numbers` v762 → v763 (D797, kit S674). Built in the Scan App chat, session 355.

**What changes — his Stationery page, in five sections.**
1. **To sort.** Every **challan** of a *listed supplier* (a card at the top: Variety Stationers, added by the installer once; more by
   name) scanned from the day the supplier was listed lands here, whatever lane was chosen; the sorting desk's list leaves it alone,
   and the desk refuses to save its lines (the page sorts them). Their bills and estimates are never here: they are joined to a
   statement (section 5). A challan a person sorted into another clinic group on the desk is not offered, and the page refuses to
   overwrite that group. *Leave as it is* takes a paper off the list for good, its lane and group untouched. Each read line is a product box
   (type to search the list, pick, or type a new name — added on Save), the quantity, the unit, and **For Clinic / NK**; the owner's
   screen carries the rate. One Save per paper. A line with neither side chosen waits. Then the paper is placed by its lines: any
   clinic line → the clinic lane, Stationery & packaging (marked *mixed* when NK lines too); only NK lines → the NK Pathology lane.
   Audited as the desk audits (relane / subgroup / desk_saved), so the desk's list and the supplier-history rule see a person's sorting.
2. **NK Pathology.** NK lines in their own table, kept apart: never the clinic's stock or received (`stationery_line.side`).
3. **Clinic stock** — the page as before (received · issued · in stock · counts · the item list). Clinic lines feed it as before.
4. **The supplier account.** Every line supplied, with its state — *unbilled* / *on statement* / *billed* / *paid*; the clinic / NK split;
   unpaid by side with the lines still without a rate; paid this year; filters by month, product, state.
5. **Monthly statement.** One tap makes it from the unbilled lines up to the month's end (older ones come too, named): **challan-wise,
   in the supplier's own challan numbers**, each *bill to: Clinic* or *bill to: NK Pathology*; a mixed challan says *MIXED — bill as
   marked* and names each product's side; `rate ____` on every line; the closing line asks for separate bills. Copy the text · Send on
   WhatsApp (the supplier's phone from the Vendors page, read only) · Print · Mark sent · Withdraw (lines back to unbilled; never a
   billed one). **Join their bill or estimate** (scanned already; a challan is refused): the rates typed onto the lines, the lines go
   to *billed*; **Mark paid** (how it was paid) → *paid*. A line is on one statement and paid once, ever; a paper whose lines are on a
   statement is never re-sorted from the page or the desk, and the desk can never void its lines (a re-save to another group is refused).
- **Shavez** sorts on `/scanapp/stationery/sort` (Roman Hinglish, his refusals in his words, no rate anywhere; a rate in his form is
  ignored) while his desk switch is ON; his menu reads *Stationery sort (N)*. The owner's page is the owner's.
- NOT here: the NK share into NK's accounts (the finance app, later); a lab stock book (the NK Pathology project); the payment itself
  (recorded on the finance side as today — here it is marked).

**Files and pins (FROM → TO).** `/root/assetapp/stationery.py` `b6ce217a` (S585's) → the kit's whole file (17 counted edits +
`s674_block.py`, `edits_s674.py`); `/root/assetapp/sorting_desk.py` `bb206e5d` (S651's) → the kit's whole file (4 counted edits:
the desk's list leaves a listed supplier's paper to the page; the desk refuses a listed challan's lines and a void of lines on a
statement). `make_s674.py` rebuilds both on the box from the live bytes and refuses
unless each equals the kit's file. Additive at mount: table `stationery_stmt`; columns `side`, `stmt_id` on `stationery_line`
(added once to a table made before them). One data step: the table and columns made whether or not the mount got them (a locked database), then the first listed supplier and
the floor day, once. Read only, pinned: `clinic_papers.py
89a3cd0a`, `asset_register.py 63a8b15b`, `procroom.py e51c00a1` (S670's, live since 05:32 IST 28-Oct), `asset_machine.py 7dbd5e0c`, `batteries.py bb082b4c`,
`xray_costs.py 5823bae2`, `claude_reader.py 1277e80d`, `claude_reread.py ed7023d2`. The parent's `vendors` table read only.

**Kit.** `edits_s674.py` · `s674_block.py` · `make_s674.py` · `stationery.py` · `sorting_desk.py` · `walk_s674_app.py` (V1–V23, K1–K2
on the REAL app with made-up supplier, papers and products; `--expect-red` on the live files: A0 and V1–V23 red, K1–K2 green; the
independent review's first round found three ways a line could be counted twice or a person's group overwritten — each closed and
walked, V19–V22; its second round SAFE, its four small points folded in: no start day = nothing offered, an empty desk save never
erases the page's lines, the start day in IST, V23) ·
`install_s674.sh` · `rehearse_s674.sh` (R1–R7) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`. The pages were also rendered in a real
Chromium at 1366 and 390 px (the chat's own look): no overflow, no console error, no rate on Shavez's screen.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S674_VARIETY_FLOW/install_s674.sh`

**UNDO (one line):** `\cp -p /root/assetapp/stationery.py.bak_S674_b6ce217a /root/assetapp/stationery.py && \cp -p /root/assetapp/sorting_desk.py.bak_S674_bb206e5d /root/assetapp/sorting_desk.py && systemctl restart assetapp`
