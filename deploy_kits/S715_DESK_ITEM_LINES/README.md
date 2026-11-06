# S715_DESK_ITEM_LINES — the sorting desk: supplier list, calendar, workable item lines, Read it again

**Why.** The owner, 06-Nov-2026 08:57 IST, on a Variety Stationers challan scanned the day before: it was reported "nothing could be read"; the
supplier box was free text with no list; the date had no calendar; the stationery lines could not be worked — one line only, no way
to add a line, picking an item did nothing visible, and adding a new item from the line did not work. The cause, read in the live
code (`sorting_desk.py` 35fdd6c5): the supplier and date were plain text boxes; a paper with no items read got ONE hand line and no
"add a line" control (the procedure room panel had one, the stationery panel never did); "+ Add to the list" was a hidden option at
the foot of the item drop-down that only worked once the name was typed in a separate small box, and it never asked unit or rate; and
a listed supplier's challan (Variety Stationers, S674) was refused on the desk altogether — its lines were sorted only on the Stationery
page — so typing the supplier's full name would have made the desk refuse the lines ("Nothing was saved"). Typing a short name
("Variety") instead files the paper under a second supplier, outside Variety's monthly statement. The owner approved the mock-up
https://claude.ai/artifact/XpbAyqQAyCimRnv3dz1ECm and said "build" (10:09 IST). Board `_numbers` v944 -> v945 (kit S715). Built in
the Scan App chat, session 363.

**What changes — the sorting desk (the owner's login and Shavez's).**
1. **Supplier** — type two letters, pick from the list of known suppliers (`/desk/api/suppliers`: one per supplier key, named as most
   often written, most used first, from SORTED papers only (accepted, filed, or put in a section by a person — a challan waiting for its bill) — a paper still waiting to be sorted may carry a patient's name read as the vendor; a listed stationery supplier always; never
   the pharmacy lane, Other documents, a set-aside or second scan, a person's papers — Personal, Resumes, a patient's — the owner's
   expense lane for anyone but the owner, or the owner's own name). A typed name that is not picked is not taken: Save reads *Pick the supplier from the
   list*. *+ New supplier* takes a new one, with a warning when its first word matches a known supplier.
2. **Date** — a calendar box, with *Scan day* and *Today*; the Read line shows it dd-mm-yyyy. The server already accepted yyyy-mm-dd.
3. **Stationery lines** — *+ Add a line*, × to remove, an item box that searches the list (a green tick when chosen), *+ Add "<name>"
   to the list* opening a small form on the line (name, unit, rate). × on a line read from the paper keeps it as *not a stock item*, so
   it never comes back counted; × on a line typed by hand removes it. The rate is optional and shown on the owner's screen only (S674:
   no rate on Shavez's screens). The lines total against the paper's amount, naming the lines without a rate. A chosen item needs its
   quantity before Save.
4. **A listed supplier's challan (Variety Stationers) can be sorted on the desk**: each line *Clinic* or *NK Pathology* (S674's sides);
   a line with no side, or every line NK (that paper is sorted on the Stationery page, which places it on the NK lane), is refused in
   words, nothing saved; Clinic and NK lines together mark the paper *mixed*; the lines carry the paper's own date, as the Stationery
   page's do (the statement's month). Saved lines come back with their sides, so a re-save never turns NK into Clinic. Any other
   paper's lines are the clinic's whatever the page sends (an NK side only on the listed flow); a listed supplier's bill is not asked. A paper that holds NK lines and would leave that flow (re-typed as a bill, a supplier re-spelled or taken off the list) is refused, so its NK lines never turn Clinic. The Stationery page's own sorting is unchanged; the desk's list still leaves a listed supplier's read challan to that page.
5. **Procedure room lines** — the product box searches the list in place of the long drop-down (Not on the list / Not a list item /
   + Add to the list as before).
6. **Read it again** under *Nothing could be read* — asks the app's own re-read (`/bills/<id>/reread`, the same as the bill page's
   button; a stored date the calendar cannot show is sent back as it was, never wiped); over the next minute the EMPTY boxes fill by themselves if it reads, and the line says what was filled.

NOT here (the second kit): X-ray film lines and Others lines on the desk (they need new storage).

**Files and pins (FROM -> TO).** `/root/assetapp/sorting_desk.py` `35fdd6c5` (S674's TO) -> the kit's whole file (22 counted edits + 2
whole JavaScript functions, `edits_s715.py`). `make_s715.py` rebuilds it on the box from the live bytes and refuses unless it equals
the kit's file. No data step, no table, no column. Read only, pinned: `clinic_papers.py 89a3cd0a`, `asset_register.py 63a8b15b`,
`asset_machine.py 7dbd5e0c`, `procroom.py e51c00a1`, `batteries.py bb082b4c`, `xray_costs.py 5823bae2`, `claude_reader.py 1277e80d`,
`claude_reread.py ed7023d2`, `stationery.py 3a22c6bb`. Restarts `assetapp` only.

**Kit.** `edits_s715.py` · `make_s715.py` · `sorting_desk.py` · `walk_s715_page.py` (the desk page's own script in a real Chromium
against a stand-in server with made-up data: V1-V29, K1-K6; 33 of 33 green on the TO; on the live FROM 27 of 27 new checks red, the 6
keep-checks green) · `walk_s715_app.py` (the REAL app on a scratch copy of the live database, made-up rows only: A0, V1-V13, K1-K2;
`--expect-red` on the live file; run by the installer on the box) · `install_s715.sh` (also prints, read only, the papers of the last 7 days
the reader did not read, and why) · `rehearse_s715.sh` (R1-R7) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.
Proven on manojz (06-Nov, the device VM, the app files of the newest code bundle at their pins): the app walk 16 of 16 green on a
fresh database, its control on the live file 14 of 14 new checks red and both keep-checks green; the rehearsal R1-R7 all green. An
independent cold review, three rounds: R1 NOT SAFE (2 blockers -- the build script refused its own --expect; desk-sorted Variety
lines dated the sorting day, not the challan's -- and 7 should-fix, all built), R2 NOT SAFE (1 blocker -- a type change to Challan
did not redraw the Clinic/NK boxes -- and 2 should-fix, built), R3 SAFE TO INSTALL.

**Install (the owner, after publishing):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S715_DESK_ITEM_LINES/install_s715.sh`

**UNDO (one line):** `\cp -p /root/assetapp/sorting_desk.py.bak_S715_35fdd6c5 /root/assetapp/sorting_desk.py && systemctl restart assetapp`
