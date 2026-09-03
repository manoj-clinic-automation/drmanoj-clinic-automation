# HANDOFF RUNBOOK — v154 · Session 222 close, folded at the Session 223 open · 03 September 2026 IST (night)

**Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline ·
§4 the boundary. **§2 is the close-time snapshot; `OWNER_TODO_LIVE.md` is the always-current truth.**

---

## §0 — WHAT HAPPENED AT S222, AND WHAT THE S223 OPEN PAID

**The session that stopped screens from lying. Eleven kits, ten installed on the day, every pin
predicted offline and read back identical.** Two faults closed, both of them a screen asserting
something the system had never checked.

| kit | what went live | pin after |
|---|---|---|
| `S222_DESK_USERS` | **F-296 CLOSED** — `returns.desk_users`, an opt-in allow-list read at the desk's only door. Set → those logins plus maker/checker. **Unset, blank or unreadable → nothing changes**, so reception cannot be locked out by a half-applied change. Walk 40/40 | returns_desk **3296eca0** |
| `S222_CORRECTIONS_TRAP` | *"a control that refuses is a trap"* — the ledger-check and transfer block hidden from anyone the server refuses; the page **ASKS** rather than guessing at a role. An error SHOWS it, deliberately | darpan_corrections **26b1defe** |
| `S222_JOINER_LOGIN` → `ALLRECS` → `FORMS` → `SECTIONS` | **F-295 CLOSED** — the page creates the login and **proves it by signing in as him**, restoring its backup if the sign-in fails | joiner_app **3e213e4d** |
| the six `staff_manage` kits | joining is a FORM, leaving is a PICKER with no text box, the console is **English** (D366), sections by system | staff_manage **71540e8c** |
| `S222_PORTAL_ENTRY` | Manage Users is the front door: joiner · leaver · all records | portal **c89ffa9f** |
| `S222_AMIR_JOINER` | report-only: the record was **already 6/6 COMPLETE**. It wrote nothing and stays as the **verifier** | *(no write)* |
| `S222_SCANAPP_INAPP` | *(staged; installed at the S223 open, 22:59 IST)* the `/scanapp` prefix + `/healthz`; the scan app opens INSIDE the app window | asset_register **71bd3277**, portal **23824f92** |
| `S222_TILE_GRANTS` | *(staged; installed at the S223 open, 23:07 IST)* per-person tiles leave the source for `tile_grants.json` | portal **d15acef3** |

**The number that justified the joiner form: fourteen sessions of joins had been filed as FULLTIME
with no authorities at all.** Not one was wrong on purpose — the page had never asked.

**Findings:** F-297 … F-301 minted at the S223 open, **all five the assistant's own**. F-297 the
self-contradicting pin row · F-298 two chained kits handed over backwards (the gate refused,
correctly, on the live login system) · F-299 a stale repo copy quoted to the owner as a checked fact
— **he corrected it** · F-300 a blanket `*.json` in `.gitignore` that would have shipped a kit with
its whole payload missing · **F-301 the fold's own finding: `KB_Register_v5_69_S221` contains no S221
wave block and not one S221 pin**, while all four of its self-referential lines say it does.

**Decisions:** none minted; **D367 remains free.**

**The S222 close debt, paid in full at the S223 open:** Fault Register **v2.52** · Archive **v1.68**
(§S222 appended, pure append proven: first 1,078,797 bytes byte-identical, +14,150 → 1,092,947) ·
KB Register **v5.70** (with the S221 wave carried in) · this Runbook **v154** · manifest and
`MD5SUMS_ALL` regenerated last · the reduction tranche measured and moved.

---

## §1 — MENTAL MODELS EARNED HERE

1. **A close is verified against the CONTENT it claims to have added, not against the four pointers
   that describe it** (F-301). The H1, the narrative, the lineage row and the END marker are a
   checklist, not a proof. A version bump asserts a wave exists; the close must show the rows.
2. **Any generated artefact must be provably lossless against its previous generation, or the
   generation is a deletion** (F-301). `live_pins.txt` is generated from the Register; regenerating
   it from a Register that had lost a wave would have erased eleven live truths in one command.
3. **A file's provenance is checked before it is QUOTED, not only before it is edited** (F-299).
   Reading is not the risky act — asserting is. A statement of fact about a live file names the pin
   it was read from, or it is a hypothesis and must be said as one.
4. **When a canonical record disagrees with itself, neither half is evidence — go to the artefact**
   (F-297). And a generated checker inherits the errors of whatever generates it.
5. **A kit chained on another kit's output names its predecessor in its own INSTALL** (F-298). A
   from-pin gate is the last defence, never the plan: anything it has to catch was mis-sequenced.
6. **A kit's payload is never subject to a repo-wide ignore rule**, and a publish gate verifies the
   kit's file LIST against its manifest, not only the bytes that arrived (F-300).
7. **A page that shows a credential must have created it, or must say it has not** (F-295). An
   onboarding step that ends in a screen rather than in a state is not a step.
8. **A role is not a scope** (F-296, closed here). The moment a second desk keys off the same role,
   the role has become a group, and a group needs a membership list.

---

## §2 — THE LIVE BACKLOG (close-time snapshot)

**⭐0 — the owner:**

1. **DONE at the S223 open** — the two staged kits installed, in order, every pin matched.
   *(Check on the phone: 📷 Scan Purchase must stay inside the app window; `assets.dr-manoj.in`
   must still open normally in a browser.)*
2. **After the next publish**, one line on the VPS so the pin checker sees the new Register (F-240):
   `git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main`
3. **Export the SALE and STOCK reports from Marg** each evening after closing; the rest is automatic.
   The 22:30 nightly push has no history yet — the drift page says if a report did not arrive.
4. **On the returns card:** tap OK or reject on any **₹1,000+** return; tap **counted** on the
   spot-count list when a shelf is counted.
5. **The Darpan tile ruling** — `USER_TILE_MASK["darpan"]` still hides Attendance, Staff Register and
   Scan Purchase on a premise that is dead. Three deletions in `tile_grants.json`; no deploy, no
   restart.
6. **The ruling owed since S210** — `darpan_app.py` exists in no store in reproducible form.
7. **Give Darpan his sheet**; show reception the Vaapsi Desk.
8. **Rulings still owed**: the S214 / S215 / S216 candidate sets.
9. **The delete lists** — `_to_delete_S222\` on `D:\dr-manoj-git\` · the SSD `99_HOUSEKEEPING_TODO.md`
   · token rotation (parked) · the VINBACTUM / RUNVACE write-off vouchers.

**⭐1 — the build order:**

1. **Own advances, and apply for more** — the staff register scoped to a person's own view, in the
   **D334 present-request shape**: he asks, nothing self-approves, the request time is the record,
   the owner rules. Never a rate, never a total, never anyone else's (**F-31: salary is
   doctor-only**). **Buildable entirely offline** — `staff_register.py` live bytes byte-exact at
   `deploy_kits/S200_R7/` (`f85a4b06`), `staff_ledger.py` at `deploy_kits/S202_D349B/` (`9e764f80`).
2. **The per-person screen** — granted · comes with the login · never, with **Dr Bhawna as a second
   owner-level person** (drawer, salary, advances, attendance, scan). The middle column is the one
   nothing in this clinic has ever shown.
3. **The eight PENDING S221 pins** — re-hash on the box and promote. They are recorded, they are not
   passes.
4. **Docterz revenue Phase 1** — the Drive sweep is DONE (53 business days, 03-Jul → 03-Sep:
   43 days lose nothing, ten move, ₹3,300 net unattributed; **₹8,700 of card money inside the UPI
   line**; 144 F-93 phantom rows; and two days that declare MORE tender than total, which a dropped
   leg cannot cause). Next: the PC-side parser fix (seven tokens, footer as the day's authority,
   F-93), then the VPS legs — `upi_txn` for the rail, then the reader, store, page and bank compare.
5. Then: M3 purchase tables · M4 Phase B · M5 · M6 · the F-269 route patch · the August staff close ·
   the scanner A5 vertical resize.

**Standing holds:** AUGUST PURCHASE IS PROVISIONAL · NEFT portal WAITS · the hub's shape is not
reopened · the spot-count bridge is PARKED · **attendance under the main domain is PARKED** — its app
pulls punches from the biometric machine.

---

## §3 — INSTALL DISCIPLINE (as S221, extended by this session's own failures)

- Anchored patchers, verbatim anchors, refuse-unless-exactly-once, `.bak` beside the file, compile
  check with restore, `MARK` for idempotence. One paste per kit, every current pin guarded by `test`.
- **Reproduce the live bytes offline before anchoring**; predict every pin, and **name the
  line-ending convention** — PC-side CRLF, VPS-side LF (F-294).
- **Two kits chained on one file are handed over as one ordered instruction, predecessor named**
  (F-298). Never leave the order to be inferred from a document the owner is reading at 8 a.m.
- **Never pipe a gate** (F-291). Check the exit code explicitly before chaining.
- Selftest on a COPY of the live db, then a **LIVE-SHAPE walk through the real entry point with the
  real caller's objects** (F-286). A browser render for any page change, run as a **differential**
  against the unpatched artefact (F-293).
- A permission change ships with a list of **every route that keys on that role** (F-296).
- **A publish gate checks the kit's file LIST against its manifest** (F-300).
- No compile, no `git status`, nothing that writes, inside a kit folder on the owner's disk (F-285);
  `git --no-optional-locks` on the mounted repo (F-233/F-285).
- **A statement of fact about a live file names the pin it was read from** (F-299).

---

## §4 — THE BOUNDARY

Built and live: everything in §0, including the two kits that were staged at the S222 close and
installed at the S223 open with every pin matched.

**Unbuilt and named:** the staff register scoped to a person's own advances, with the request path
(⭐1-1) · the per-person screen · the Darpan tile mask, awaiting one word from the owner · the eight
PENDING S221 pins, awaiting a box read · the `darpan_app.py` ruling, owed since S210 and now
load-bearing · the Docterz parser fix and its VPS legs · attendance under the main domain and the
spot-count bridge, both **parked by the owner, not by the assistant**.

---
*HANDOFF_RUNBOOK v154 · written at the S223 open, 03-Sep-2026 (night), as the S222 close debt.
Supersedes v153.*
