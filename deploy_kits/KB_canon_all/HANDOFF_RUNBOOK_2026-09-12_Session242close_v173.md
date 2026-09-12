# HANDOFF RUNBOOK — v173 · S242 close · 12-Sep-2026

## §0 · WHAT HAPPENED

One evening. **Three portal changes, and the staff app stopped being a prediction.**

1. **D481 — the register tile went to reception.** `Docterz daily collection` had been withdrawn
   from every staff login at S239 for holding zero entries. That measured usage, not fit. Granted
   to Shavez, Shivani and Alisha; `tile_grants.json` v10 → v11, one line, no code, no restart.
2. **F-444 / D482 — the register was reading Docterz's calendar.** It opened on yesterday because
   its candidate days came from `clinic_day_revenue`, which Docterz fills *after* the day. Now
   opens on **today**. `clinic_register.py` `93a31e68…` → `c6b87682…`.
3. **F-445 / D483 — Amir's page had no door.** `/finance/amir` had been live since S241 with no
   tile anywhere in `portal.py`. He now carries **one** tile, `Amir ka kaam`; five others are
   **parked, not removed**. `portal.py` `ed558b36…` → `d08721f6…`, `tile_grants.json` v11 → v12.

**Then it was used.** Shavez signed in. **Alisha made the first entry the daily register has ever
carried**, at 21:26 IST — cash ₹15,100, UPI ₹6,300, split across heads, totals agreeing to the
rupee. Amir's account was verified in an incognito window; he starts tomorrow.

4. **F-446 / D484 — the drawer count is optional by design.** The assistant called its empty
   section a missed step; the owner had told Alisha to leave it. **A day with the nine boxes filled
   and the count blank is COMPLETE and is never to be flagged.**
5. **F-447 — a blocker had been generalised for four closes.** `gen_live_pins.py` and
   `MD5SUMS_ALL.txt` never needed the dead device shell. **Both ran at this close**, and the
   manifest rows were verified by hashing the files themselves.
6. **F-448 — and it had cost something.** Run for the first time in four sessions, the folder's own
   Phase-0 gate (`md5sum -c MD5SUMS_ALL.txt`) **exited 1**: `CANONICAL_MANIFEST.md` failed against a
   stale expectation, and three S241 canon files were in no row at all. Nothing had drifted.
   Rebuilt: **485 → 495 rows, added 10, dropped 0, exit 0 on all 495**.

**New fault codes:** F-444, F-445, F-446, F-447, F-448. **SOP changes:** none. **Surveillance scope:**
unchanged.

## §1 · MENTAL MODELS WORTH CARRYING

- **"Live" is not "reachable."** A page can be built, walked, pinned and running, and still be
  invisible to the person it was built for. The delivery is part of the deliverable.
- **An empty field is a question, not a verdict.** Twice in one evening: a tile withdrawn for having
  no entries when the people who fill it could not see it, and a blank drawer count read as a
  missed step when it was never required.
- **Name the resource, not the tool.** A blocked step names what it actually needs. "The shell is
  dead" was true and stopped three steps of which only one touched a shell.
- **Run the gate even when you cannot rebuild it.** An unrun gate and a green gate are
  indistinguishable in a close report. This one had been red since S241.
- **The repository can rebuild `portal.py`.** The S204 base plus twelve anchored patchers reproduce
  every declared pin exactly, landing on the live one. Use it instead of asking for a hash.
- **`tile_grants.json` shows; it never grants.** A tile is convenience; the route's own gate decides
  access. And a grant matches a tile by NAME — the two files always move together.

## §2 · THE LIVE BACKLOG

**⭐0 — what needs the owner**

1. **Reprint August and LOCK it.** Still the only thing standing on his side.
2. **Amir's password** — reset from `https://followup.dr-manoj.in/portal/users`, login `amir`.
   Nobody can look the old one up; it is stored only as a salted hash.
3. **A8c — pull the VPS deploy clone** (one line, below). Without it the pin checker reports a
   normal amber after every close, and an amber that is normal is an amber nobody reads.
4. Amir's two daily purchase reports and a fresh SALT WISE ITEM LIST export.

**⭐1 — what I build next**

1. **Darpan's claim queue** — `open → contacted → settled`, settled names an outcome, self-closes
   on a matching purchase return, ages to the top at fourteen days (D471). Amir's page has been
   writing `amir_claim` rows since it went live; **0 raised so far**, so the queue opens quiet.
2. The reception override for a missing punch (D468) — attendance app, not finance.
3. The "no export today" alarm (D467 phase 2, item 3).
4. Retire manojz's data jobs; manojz becomes development only.
5. **F-413** — masking the five inherited numbers in the KB History Archive.
6. The item list refreshing itself after every export · bill-history backfill · the three-column
   stock view with a stale-export refusal.

## §3 · INSTALL DISCIPLINE — what this session confirms

- **A kit is proven by a LIVE-SHAPE walk**, and this session's walks asked the real thing: a real
  Flask mount over a real sqlite database for the register, and `portal.py`'s own
  `_visible_sections` for the tiles. Neither read a JSON file and called it proof.
- **Rehearse the installer, not just the payload.** The Amir kit's whole installer was run end to
  end against a fake box — including its second run answering ALREADY INSTALLED.
- **Gate on a pin you derived, not one you asked for.** Both code kits refused unless the box was
  on the expected pin, and both printed the pin predicted before the install.
- **Check `.gitignore` before the publish.** Line 161 (`!deploy_kits/*/tile_grants.json`) covers
  this session's payloads; F-300/F-310 are exactly this shape.

## §4 · THE BOUNDARY

Unchanged. The VPS needs the owner because he holds every credential by design. Everything else —
building, walking, hashing, recording, reading live pages — is the assistant's, and this session
moved more of it off his plate: the pin list and the sums file are no longer his to wait for.

---
*v173 · supersedes v172 · written at the S242 close. Next free: **D485 · F-449 · Session 243**.*
