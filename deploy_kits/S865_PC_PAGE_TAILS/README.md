# S865_PC_PAGE_TAILS — the parent, S480, 18-Nov-2026

**His word:** "go" (08:51 IST 18-Nov) on the Clinic PCs page tails (Runbook §2A item 2, F-1386's tails (a)–(d)).

**What he sees** on `https://followup.dr-manoj.in/finance/pcs`:
- **(a) The pathology lab PC has its own card** (it said "Not set up yet" though its agent has run since 25-Oct), judged by the lab module's own hours and thresholds (lab_door.health_row: open 08:00-21:00 Mon-Sat, 08:00-14:00 Sun): *Working* when heard in the last 20 minutes; *Needs a look* when silent over an hour while the lab is open (*Not working* after 3 hours), when no Labmate data has reached the server for 26 hours, or when the PC itself reports something to look at (a count only); *No report — switched off* out of hours up to 26 hours. It names when it was heard and when the data last arrived (MB). Once lab_door's own health row is wired into the health page (key `labpc`), that row wins. Kit line: set up by the lab agent kit `INSTALL_LAB_AGENT.bat` (S655); no one-button kit here yet.
- **(b) The biometric set-up card** now carries the 13/14-Nov event (the clock stopped, the machine shut down, to go to BL Computers) and the server's 5-minute watch on the machine (S830); "Notes checked 18-Nov-2026". The five other cards were re-read: nothing in them changed since 22-Oct (their open points are his to settle and stay listed).

**Files (the parent's):** `/root/finance/pc_kits.py` 45d6f15d → see TO_PINS · `/root/finance/setup_notes.py` aa7ee189 → see TO_PINS. Reads `/root/labdata/lab_heartbeat.json` and `/root/labdata/incoming/snapshots.json` (lab_door.py's, the NK Pathology chat's) — read only.

**Also done this session, outside this kit:** (c) F-1397 — `D:\Downloads\_kbtools\pc_kits_current.py` on manojz now takes the manifest's CURRENT pin list (aa2f1596 → f37a5400, backup beside it; S822's walk 38/38 on it). (d) The seven August files: the 17-Nov report shows the medical PC has none of them any more (mirror-only); the Sanjeevni chat told.

**Proof:** `walk_s865.py` 23/23 on a made-up root at a fixed clock (the page through Flask for every role; the lab card in eleven states, open and shut hours; the biometric lines); control on the live files red (7/23). The installer prints the lab card's state on the live files before placing.

**Install:** his publish, then one server line (in the installer's head). **Undo:** `bash /tmp/s865kit/install_S865_PC_PAGE_TAILS.sh --undo`.

**Cold review (S480):** SAFE TO INSTALL; its 3 SHOULD built in (opening hours as lab_door's; the key `labpc` so lab_door's row wins once wired; the PC's own 'attention' as a count) and LOW 4-6 (26-hour snapshot rule, bad index entries skipped, MB under 0.1, the watch wording).
