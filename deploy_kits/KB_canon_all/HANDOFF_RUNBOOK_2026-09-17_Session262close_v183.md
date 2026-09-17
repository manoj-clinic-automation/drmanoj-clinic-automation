# HANDOFF RUNBOOK — v183 · Session 262 close · 17-Sep-2026 IST

## §0 · WHAT HAPPENED

**One sitting, 06:48 → close, the first session of "Sanjeevni — Pharmacy & Marg", beside the parent's S261
and then S263 in the same clone. Three kits built offline, published and installed by the owner from one line
each, all three live and read back on the rendered pages by noon. Two VPS pins moved. F-494 and D524 closed.
F-507 … F-509 minted; D529 … D531. EOS.**

**1 · The move, proven from the new side (D528 part 2, step 1).** The 35 staged documents written to this
project's knowledge and read back — two hashed exactly against `SANJEEVNI_STAGING_SUMS.md5`, the Book whole.
`project_info` 0 → **117,736**. The parent deleted the same 35 (1,593,475 → 1,475,742); the two deltas agree
to three bytes. Two sessions ran at once from one START_HERE; this one took S262 because it read the board
first (F-509).

**2 · S282_LINE_OWNER — F-494 repaired.** Bill 160 / 1-Sep under two suppliers; five BILL/ITEM WISE lines
(₹17,776.68) owned by nobody. The ITEM WISE export carried the same lines with their owners — the rule gives
a two-owner line to the one supplier ITEMWISE names for that exact line. 20 checks; dry run on the nightly
database: 5 placed, 0 left. Live: `purchase_app.py` `3535dc97…` → `216a0cd9…`; September sheet reads DAANSHI
₹5,377 · KEDAR ₹48,960, no unowned line.

**3 · S284_SHAVEZ_MAKER — D524 closed, D529.** Not a `unit_role` maker row (which would also let him file the
day, give verdicts, type carry-forwards, read the phone book) but a named list in `setting`,
`purchase.cheque_users = shavez`, fail-closed — the phone-book/salt-list pattern. 26 checks. Live:
`216a0cd9…` → `d1476f80…`. The register renders empty; September's ₹400 cheque waits on the lane.

**4 · S285_SUPPLIER_CHECK — the owner's ask of the morning, D530 · D531.** August: Amir entered a purchase
under the wrong supplier, found by a person, corrected by hand — Marg is consistent with such a mistake, so
nothing could see it. Now: a bill whose item has never come from its supplier while another has supplied it
on ≥ 2 earlier bills carries a warning on step 4, in Hindi, above *Theek hai*; reason *Supplier galat likha*
(not a claim). And the list shows only bills a live export still carries — the corrected-away bill leaves by
itself (F-508). 36 checks driving both modules as code; 5 of 226 bills since July would have warned. Live:
`amir_day.py` `a9f20622…` → `b3c20319…`. Step 4 and the owner's day view read clean.

**5 · Recorded, not built.** F-507: `freshness_legs.json` on the box ≠ its S230 pin — re-pinned to the
bundle's bytes; the diff is the parent's. The refused 16-Sep 23:55 export is the owner's own daily summary
sale report (Darpan prints it, pays the day against it) — its title carried no date; teach the router. The
15-Sep salt list is the one on the server and sufficient (his word). Numbers: drift 0 · dead 1 · **stale 3,
over the line — the Book v1.3 not reached** · folders per the 05:05 report.

## §1 · MENTAL MODELS THIS SESSION EARNED

- **The witness is usually already on the server.** F-494's fix needed no new data: the item-wise export
  had the owners all along. Before designing a capture, ask which existing export already says it.
- **A role is a bundle; a grant is a line.** When the ask is "let X write this one thing", a named list
  scoped to that thing is smaller, reversible in one line, and does not change what the role means.
- **Marg is consistent with its own mistakes.** A wrong supplier passes every Marg-side cross-check.
  Only history (item ↔ supplier affinity) or the paper bill can see it — and history is on the server.
- **Superseded must reach every reader.** The month forgot superseded exports at S225; the list a person
  answers on did not, until S285. When a table gains "superseded", grep every query that reads it.
- **Claim the number on the board first.** Two projects, one series, no lock — the board is the lock (F-509).
- **A page read as text still tells you where to look.** Every live read this session was done by a
  sub-agent as text and then confirmed against the store (the sheet against `purchase_line`, the register
  against `purchase_cheque`) before it was written down.

## §2 · THE LIVE BACKLOG — this project's

**The assistant's:** the Book v1.3 (F-493 §7.2; stale 3 — first) · the router taught the owner's daily
summary sale report's title shape (no date on the title row) · the item↔supplier check's second stage —
purchase returns under the wrong supplier, and the same bill number under two suppliers on one day (the
F-494 shape) shown on Amir's screen · Darpan's day-close place in the portal (code side, ready for when his
three stock corrections are done) · `SANJEEVNI_START_HERE_PROMPT_v1.1` (the shared-systems map) · the
tidy-up chain (one store for sale lines → retire the manojz senders → Sanjeevni in its own process), gated on
`sh_run.differ = 0` for seven runs (F-493) · the first live look at S285 once Amir's export lands today.

**The parent's, named here because this session found them:** the `freshness_legs.json` diff (F-507).

**His, deferred at his word:** `OWNER_TODO_LIVE.md` — the Sanjeevni section: his three stock corrections
before Darpan's flow; August's finalise; AGARWAL SURGICALS' bank details; the two merges; the ₹400 cheque.

## §3 · INSTALL DISCIPLINE

Three VPS installs, each: pin from the 17-Sep bundle, patch on a copy, predicted pin read back and refused if
different, `py_compile`, backup beside the file, service restarted and health read, rollback byte-identical
on any failure. S282 rehearsed its database pass on a copy before the live one and kept `finance.db.bak_S282`.
S284 refuses on the pre-S282 file. Nothing changed on manojz or the medical PC. The publish's own gates
(numbers/credentials, `.gitignore`) were run on every kit before it was named for the publish.

## §4 · THE BOUNDARY

This close writes its canon into the shared `KB_canon_all` (Register v5.102, Archive v1.99, Fault v2.86,
this runbook, `START_HERE_SESSION_264`, the pin list, the manifest, `MD5SUMS_ALL.txt`) and the build brief
into this project's knowledge. **The publish is the owner's double-click and is owed; the parent's S263, open
beside this close, chains on these versions.** Nothing further changes on the VPS at this close.
