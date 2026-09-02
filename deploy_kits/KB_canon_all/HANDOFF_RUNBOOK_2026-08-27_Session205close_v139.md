# HANDOFF RUNBOOK — v139 (Session 205 · THE SESSION THAT WORKED THROUGH THE NIGHT · 27 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the boundary.**

---

## §0 — WHAT HAPPENED (Session 205 — FULL build EOS)

Opened on *"B2 is priority, all automation is priority"* and ran from roughly 04:30 to 07:45 IST.
The owner slept for part of it and said so: *"i had slept and u did the grind."*

1. **PHASE 0 GREEN.** `md5sum -c` exit 0, **225/225** · `.gitattributes` still pins `*.md` ·
   repo HEAD equal to GitHub HEAD.

2. **⭐0-2 CLOSED BY THE OWNER** — the S204 pin list copied; `verify_live_pins.py` **GREEN, 47/47,
   drift 0**, and the source proved canonical on the box.

3. **B2 CLOSED, BOTH HALVES.** manojz reports Tailscale at both ends · **a performed share test**
   (TCP 445 *and* a real directory read — ping cannot tell "PC gone" from "share refusing", which
   is what cost 8h40m) · **which point is down in words** · which transport carried the cycle ·
   whether a credential exists and which Windows account ran · MagicDNS vs the hardcoded number.
   The VPS reads all of it, plus the **`backup` field that had been sent since S203 and never once
   looked at**. Proven by the **05:50 scheduled run**, not by hand.

4. **F-195 PROVEN, THEN FIXED.** A 2×2 matrix over the live `_gate`/`current_user`/`roles_for`
   bytes: the S203 test that claims to post *"the REAL caller's shape — token header, NO session"*
   **stays green when the gate clause it exists to prove is deleted**. With the identity actually
   stripped it goes 401. Kit `S205_B`, **722/722** on the box.

5. **AF-1 FIXED AND INSTALLED (F-206).** `SEND_TO_CLINIC.bat` could say ACCEPTED when nothing was
   sent and then **blacklist that report for ever**. The record named one stale file; **there were
   two** — `last_http.txt` has the same fault and worse, because `:one` loops and report #2 could
   inherit report #1's code. Decision table: **v3 correct on 5 of 8 rows, v4 on 8 of 8.**

6. **THE MEDICAL PC BECAME REACHABLE.** `medical_agent` S205.1 turns the three-name allowlist into
   a manifest: destination confined to `D:\SendToClinic`, **a non-python file must arrive with its
   md5 declared and matching**, `.py` still compile-checked, the agent itself never deliverable.
   **23/23** on the gate, including the escape attempts. Proved end to end by reporting
   `SEND_TO_CLINIC.bat up to date (fdaf7100)` — **changing nothing**.

7. **A1 — five months of item-level purchase data un-quarantined.** `PURCHASE_ITEMWISE` taught to
   the router; the pipeline rescued and filed all five by itself at 07:10; `_UNKNOWN` is empty.
   **`"GRAND TOTAL"`, the marker its sibling signature uses, matches 0 of 5** — Marg splits it
   across two cells here and `ends_with` searches cells. Copying it would have refused every real
   report.

8. **F-213 … F-217 RAISED.** F-213 `gen_live_pins.py` unpinned (confirmed by his own checker run) ·
   **F-214** `.gitattributes` justifies a rule with a measurement nobody took · **F-215** the
   reinstall kit held **pre-fix bytes** and its own `md5sum -c` was GREEN · **F-216** 47 of 85
   untracked VPS files exist **only there**, including the whole finance deployment toolchain ·
   **F-217** a selftest that can only pass where the thing it tests cannot happen.

9. **D350 §4 DELIVERED** — `S205_LIVE_TOOLS`, 24 files each verified **against its live source**,
   0 drift, plus both reinstall documents. **Neither rehearsed.**

---

## §1 — MENTAL MODELS (added this session)

- **A check must be asked what question it actually answers.** Four instances in one session:
  a test (F-195), a kit's `md5sum -c` (F-215), a pin check green over an incomplete list (F-216),
  a selftest (F-217). *A check that passes for a reason other than the one it names.*
- **A kit verified against its own copy proves nothing about what is running.** F-209's mirror
  image: there a hash was green and the bytes did not exist; here the bytes exist, they are the
  wrong bytes, and the hash is green for that too.
- **A selftest must be able to FAIL on the machine it runs on.** One that only passes where the
  condition cannot occur has never been run.
- **A rule written from a belief about a file nobody measured.** F-208's error, applied to a file
  attribute instead of a document.
- **A size and a path are not provenance** — the corollary to D188.
- **The reserve route must read as degraded from the day it exists**, or the second failure arrives
  with no warning.
- **Whoever sends should be whoever verified.** The reason manojz is in the revenue path is
  historical — it had a spreadsheet reader — not architectural.
- **A verifier that blocks the filing creates a worse problem than the mismatch.**
- **The bottleneck has rarely been how fast code is written. It has been waiting on rulings.**

---

## §2 — THE LIVE BACKLOG

> The maintained copy is **`OWNER_TODO_LIVE.md`**. This is the close-time snapshot.
> The full working view is **`claude/S205_PENDENCY_PLAN.md`**, sorted by who can act.

**⭐0 — his:** the **August close** (July top-ups ₹4,519 · Surendra ₹516 → ₹855 · Arjun · Shivani ·
AF-3's scan) · **Pravesh 31-Aug** · **bind the scheduled task to his device** (created, currently
cloud-only) · **grant desktop control** so publishing moves across · token rotation (five stores,
parked) · the restore test · the previous FY backup · Marg support · the Tally source files ·
**Darpan's data to be checked on the VPS.**

**⭐1 — builder:** the July settlement line · **Darpan's form (X2)** · the medical verifier in
reporting-only mode · **the standard exit system (X1)** · the dead-man's alarm · the unattended
queue Q1–Q4 · then F-183 · F-178 · Staff Console Phase 0 · Purchase Portal D335 · X3 August NEFT ·
X4 Amir's weekly set · X5 Club-4.

**⭐2 — the August close** remains the first fully live enforced run.

**⭐3 — blocked:** the no-clinic-ID bills → Docterz · Lab PC / Labmate · D348 vs
`MARG_INGESTION_REFERENCE_v1` §9 item 5 · the coverage-map addendum still to fold.

---

## §3 — INSTALL DISCIPLINE (updated)

Unchanged from v138, plus five earned this session:

- **Check whether a document is manifest-pinned BEFORE editing it.** `MARG_WALL_CARD` was edited
  and only caught at the close; Phase 0 would have opened RED.
- **If you tell him to fetch something, put it where the fetch will find it.** A builder was left
  out of the repo and his `git pull` brought nothing.
- **Derive an end-marker from every real sample, never from the sibling signature.** 0 of 5.
- **A non-compilable file must arrive with its intended hash.** Stronger than the compile check it
  replaces: it proves the file is the one intended, not merely that it parses.
- **State the scope of a proof out loud.** Three proofs this session were predicate-level because
  the real thing could not be run offline, and each says so in its own output.

---

## §4 — THE BOUNDARY (moved this session, and recorded)

**What moved:** the **medical PC** is now reachable without a physical visit — through a gated
channel that confines destinations, requires declared hashes, and refuses the agent itself. The
owner authorised **desktop control** and a **scheduled unattended task**; the task exists but is
**not yet bound to his device**, and desktop control was never actioned.

**What has NOT moved:** **the VPS is his alone** and holds no credentials for anyone else. Live
money rules change only by his own paste. Nothing already live is rebuilt without his explicit OK,
and the manual workflow always stays the fallback. **The unattended scope is written down and
narrow** — read-only on manojz, documents and staged kits only, never a live-file swap, never
`ToMedical\`, never a publish, never the VPS.

---

*HANDOFF_RUNBOOK v139 · written at the S205 close · supersedes v138.*
