# HANDOFF RUNBOOK — v123 (Session 188 close · 18 Aug 2026)

> **Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline.
> **The canon is current and NOTHING is owed at this close** — fourth clean handover in a row.
> Two kits live, both green to a projection written down before the box was touched, and five
> findings appended the session they were raised.

---

## §0 — WHAT HAPPENED (Session 188)

**Daily Flow v2 stage D2 is live: Darpan now saves, sees the bank and Marg check, then files.**
Two kits, no incident. `S188_D2a` 400/400 → 453/453; `S188_D2b` 453/453 → 464/464. **No decision
minted** — everything here is the execution of D326, and an implementation detail does not earn a
D-number.

**The build.** A maker-scoped `GET /finance/api/day/<date>/mirror`: his declared figures, ICICI
settled UPI with a match-or-gap verdict, the Marg verdict in **three** states (`applied` /
`staged_not_applied` / `absent` — because "no comparison" has two causes needing two different
people to act), his scans, his opening carry, the days he owes. **Save-then-see is enforced on the
server**, not promised by the page: an unsaved day answers `409 not_saved`. A `day_mirror_reveal`
row records the reveal with a **fingerprint of the money shown**, so tapping Scan — which silently
saves a draft — is correctly not an edit; a later save that moves the money writes an
`EDITED_AFTER_REVEAL` flag. **That badge reaches the checker's Day Page with no checker-side code
change at all**, because `/full` already renders `data_flag` rows. The entry page was rebuilt under
**Clinic Design Language v1** with the H1c logo and the folded-help slots D6 will land in.

**The owner's timing answer dissolved the hardest design question.** *"Darpan files next morning
only after 10 am"* — so ICICI (pushed 09:30 daily since S179) fires every morning, and Marg fires as
soon as the owner has pressed **Apply**. That coupling was named up front: **your Apply is now what
arms his morning cross-check.**

**Five findings, and the shape of the session is that each was found by building the next thing on
top of the last.** F-127 (the maker's page was pulling the whole unit cash position) was found while
reading his surfaces to design his scoped view. F-128 (the rehearsal harness had been granting the
smoke user a checker role, so eight role-refusal assertions passed by accident) was found because
F-127's fix *is* a role refusal and would not go green. F-129 (a checker's glance armed the badge
against the maker) was found while writing the owner's own first-look instructions — the safe advice
needed a caveat, and the caveat was the signal. F-130 and F-131 came at the close.

**Two things behaved exactly as designed.** `PUBLISH_ALL.bat` met a stale index lock, printed
`git add FAILED` and committed nothing — **F-124's** fix earning its keep. And a rehearsed red on a
throwaway box restored both files byte-perfect before either kit was offered.

**At this close:** Archive **v1.37** (§S188, the 726,539 characters before the v1.36 END marker
proven byte-identical) · Fault Register **v2.24** (F-127…F-131) · Register **v5.24** · manifest
rebuilt · START_HERE **189**.

---

## §1 — MENTAL MODELS

1. **Carried and undiminished:** survey the box before writing to it · the bank arbitrates, the
   human confirms · the fold-in belongs at the head of a session, never the tail · a record
   asserting something about another component is a claim, not a fact · a true statement can expire
   · test the mechanism, do not argue about it · **the projection is the check** · a count beats a
   derivation · record live pins as they move · never attest to a hash that will change after you
   hash it · a checker may not print a claim it did not test · a gate that fires is the system
   working · the untested path was the exit · secrets have a one-way valve into chat.
2. **⭐ A route states its own role (F-127).** A gate that protects the *unit* boundary does not
   protect the *role* boundary inside it. The absence of a `require(...)` is a defect, not a
   default — and a route that needs `checker` and forgets to say so accepts the maker silently,
   while looking protected the whole time.
3. **⭐ A test fixture must not grant the privilege the test exists to refuse (F-128).** The
   rehearsal harness is not exempt from the discipline it exists to serve. Assert a refusal from a
   seat that genuinely lacks the role, never from one the fixture has quietly seated.
4. **⭐ A marker that records "this was shown" must record WHO it was shown to (F-129).** Otherwise
   it will speak about somebody else. A record that is true and misattributed is harder to catch
   than one that is false, because nothing about it reads as wrong.
5. **⭐ When a kit deliberately preserves every id, the test must assert something it did NOT
   preserve (F-130).** Otherwise the change and its absence are indistinguishable, and a green suite
   is answering a question it was never asked. A hash typed at a terminal is not a gate.
6. **⭐ A command that looks read-only is not read-only until its side effects are checked
   (F-131).** And **a workaround repeated without a record is not a solved fault — it is a fault
   scheduled to be rediscovered.** Fourteen index locks across four sessions proved both halves.
7. **Two of the five findings were found by fixing the one before.** Building the next thing on top
   is the cheapest audit this project has. Nothing else this session found anything.

---

## §2 — LIVE BACKLOG

**⭐ 0. Walk Darpan through it — once, before 10am.** Save → the check → File, where there were two
independent buttons. This is the only item on this list that a person has to do rather than a file.

**⭐ 1. F-130's fix — three lines per page, no runtime risk.** Add the design-fingerprint assertions
(`--surface-page:#f3f2ee`, `id="toTop"`, `class="kick"`, the folded-help block) to the served-HTML
checks for `approvals`, `workbench` and `review`. The entry page already has them. Until this lands,
a page can silently revert its design and every gate stays green.

**⭐ 2. F-131's leftovers — one delete, from the PC.**
`del "D:\dr-manoj-git\drmanoj-clinic-automation\.git\index.lock.*"` — 14 files. Inside `.git/`, so
they can never be committed, but they are the physical record of four sessions of silent workaround.

**⭐ 3. The rest of the signed contract** (`S187_Daily_Flow_v2_Target_Design` + the returns/360
addendum): **D-R returns at reception** with the **D327 `counter` role** → **360 wiring** (Console
Sanjeevni strip + refill-skippers, read-only fail-soft) → **orthotics purchase side** (read the
asset app's scan-purchase data model first) → **D5 feeds** (Yes Bank via personal Gmail —
forward-rule vs scoped script still open) → **D6 contextual instructions** (parked; the
`<details class="help">` slots are already in the entry page waiting for it).

**⭐ 4. The §4a gate before any D3.** Verify the Staff Ledger ₹70,000 claim (read-only). D326(c)
blocks the salary bridge until it is done.

**5. 17 Aug is unfiled and its Marg report is staged** — file the day, then Apply the push. That
also gives the D2 mirror its first real Marg comparison.

**6. Darpan's ₹30,000** (three scans; the ₹10,000's category still undecided). Cash reads ₹2,05,198
until entered; ₹1,75,198 after. **7. 14 & 15 Aug** still draft — submit and approve; they are now
safe for you to open. **8. Orthotics vocabulary** — the Hub's card waits on keywords (a setting).

**9. `.gitattributes`: pin `*.html` and `*.new` to `eol=lf`.** D164 did this for `*.py` and `*.sh`
after a CRLF left `\r` on the VPS, and stopped there. Every HTML kit since S179 has worked by Linux
convention rather than by rule. One line each.

**10. Tailscale + RustDesk** — guided config, owner's PC + medical PC first (~30 min at both). **Now
also worth putting the VPS on the tailnet**: this session was driven from a phone over public SSH,
and a tailnet would make that routine and let public SSH close.

**11. Owed and named:** CLI `marg_backfill.py` NOT-FILED flag + display bug · F-106 selftest split ·
**F-97 part 2 — the repo's `finance/` tree is seven builds stale** (`finance_app.py` there is the
S180 build; `portal.py` pre-S182; two live HTML files absent entirely), and the live bytes exist only
inside kits · F-107/F-108 checks made mechanical · the three superseded intermediates in
`KB_canon_all` with no manifest row · 4 May and 27 May · 12 Jun ₹8,487 + 3 May zero-lines · Hindi
labels · WABA (F-82, vendor) · F-92 · F-93 · the stray file literally named
`followup-tracker/python test_send.py`.

**12. If you want full publish autonomy:** a scoped deploy-key decision (D328's boundary), risks
written down first.

**Cold-kit count: 2 of 3–5** (`KB_S187_close` was the last). Not due; due within 1–3 more sessions.

---

## §3 — INSTALL DISCIPLINE

The D317 kit chain stands: SUMS → KIT_ID → currency/state gate → precheck or smoke **before** any
swap → backup → apply → verify → **an honest red that restores**. Standing additions this session:
**the projection is written into the delivery note before the box is touched** (three for three this
session, all landing to the number) · **a differential smoke on the box** — the current app's suite
and the new one both run before anything moves, and the new suite must run MORE checks, so a kit
cannot quietly retire one · `bash -n` the WHOLE installer (F-126), and note it cannot see
`$KIT_$STAMP` parsing as a variable named `KIT_`, which `set -u` would have killed the install on ·
**a refusal is asserted from a seat that genuinely lacks the role** (F-128) · **`git --no-optional-locks`
against the desktop mount, never a bare `git`** (F-131).

Financial-book changes remain **gated migrations, offline-rehearsed against a copy of the real
store, reversible, never ad-hoc SQL**, projected before applied. `verify_live_pins.py` at every open
and close; the Register is corrected **FROM the box** (D321(d)). PHI, `finance.db`, raw Marg exports
and tokens never enter the repo, a kit, or chat (F-31 / F-49 / D320 / D328).

**END OF HANDOFF RUNBOOK v123 (Session 188).**
