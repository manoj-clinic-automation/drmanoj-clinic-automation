# START HERE — SESSION 202

Hi Claude. Continuing my clinic-automation project (**Session 202**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

**Working protocol (follow strictly):**

- Plain language, no assumed coding knowledge.
- ONE step at a time — wait for my explicit confirmation before the next.
- Full-file replacements only, never diffs I have to hand-edit.
- ALL-CAPS from me = urgent.
- Mask all patient numbers (last-4 only) and all secrets/tokens — never print them.
- Nothing already live is rebuilt without my explicit OK. Manual workflow always stays as fallback.
- Build/test offline → `py_compile` (I use `python`, not `python3`) → then I install.
- For VPS python, always use `/root/wa/venv/bin/python3`.
- **Always give me the COMPLETE path, and say which machine it is on.**
- **Prefer ONE file I double-click over a sequence of GUI steps or a long console paste.**
- **ALWAYS give me VPS commands as a copy block** — every time, no exceptions, never mixed into
  prose and never combined with steps for another machine. **One block per machine.**

---

## PHASE 0 — DO THIS FIRST. Verification before work.

1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin) — current at the **S201 close**.
2. **Verify every row by md5** — hash-compare only, all tiers. A row whose hash does not match
   **halts work until reconciled** (D172/D188). A filename is not provenance (D188).
3. **Read into context only Tier 0:** the manifest, this START_HERE, **KB Register v5.46**,
   **HANDOFF_RUNBOOK v135**, and any open incident. Tier 1 on demand; Tier 2 never in the loop.
4. Run the standing checks: **F-88** (every manifest md5 token accounted for) · **F-107 inverse**
   (every Tier-0 doc in use has a row) · **F-119** (`md5sum -c` must exit 0 — a WARNING is a FAIL) ·
   **F-123** (exactly one `CANONICAL_MANIFEST.md`) · **A8** (the pin list's `source_md5` equals the
   manifest's CURRENT Register pin).
5. **`verify_live_pins.py`** — expect **GREEN against `live_pins_S201close.txt`**. The S200 list
   will show drift on `finance_app.py`, which the box has right: that is the **F-134 stale-list
   condition, not a fault**. If I have not yet copied the new list to `/root/deploy/live_pins.txt`,
   that is the first thing to tell me.
6. Then confirm, and ask which backlog item to start.

---

## WHERE THE TRUTH LIVES

- **`CANONICAL_MANIFEST.md`** — the doc set, tiers and hashes. WINS on "what is canonical / current."
- **KB Register v5.46** (Tier 0) — what is true NOW: systems register, decisions index, live-file
  versions.
- **KB History Archive v1.48** (Tier 1) — every session narrative, verbatim. §S201 is last.
- **HANDOFF_RUNBOOK v135** (Tier 0) — §0 what happened last · §2 the close-time backlog snapshot.
- **`OWNER_TODO_LIVE.md`** — **the always-current owner list**, refreshed at every close (step A10
  of `END_OF_SESSION_PROMPT_v7`). **Deliberately un-manifested** — it edits continuously, so hashing
  it would break Phase 0 by design. Runbook §2 is the snapshot; this is the live truth.
- **Fault_Action_Register v2.38** (Tier 1) — findings F-0 … F-183.
- **`END_OF_SESSION_PROMPT_v7.md`** — the close-out routine. **v7 adds A10** (the owner to-do).

Marg pipeline references (Tier 1, on demand): `MARG_PIPELINE_REFERENCE_v1.md` (how it works) ·
`MARG_INGESTION_REFERENCE_v1.md` (what the server does) · `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md`
(the 60-second check and the fault flow).

---

## WHAT S201 DID (one paragraph)

Opened on one missing Marg report and closed every hole in the chain. **F-179: the outbox had no
consumer** — eleven verified reports sat correct and undelivered for three days while every component
reported success. Three kits live, three exact projections: `S201_A1FIX` (680→683, closing **AF-2**,
dead since S195) · `S201_HEALTH` (683→690) · `S201_UI` (690→**693**); `finance_app.py` →
**`3f72e9ad16d915fe5ced45c4e28a2248`**. **D347** (the medical-PC pipeline: Drive bidirectional,
Tailscale read-only D:-only and NOT load-bearing, the agent supervises but never self-updates — it
**self-reports** its drift) and **D348** (**sale bills without a clinic ID** — *variance* and *low
confidence* retired; `min_confidence` closed by measuring 192 bills, not by my judgement). F-179…F-183
minted; **F-183 is OPEN by choice**. Agent S201.1 → **S201.11** (installed). A **second Marg output
tree on `C:\Users\Public\MARG\`** was found, which manojz structurally cannot see.

---

## ⭐0 — MY ACTIONS (before the August close)

1. **Copy `live_pins_S201close.txt` → `/root/deploy/live_pins.txt`** on the box, then run the checker.
2. **TOKEN ROTATION** — `FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`, aging since 21-Aug, highest
   severity. **THREE copies of the Marg token exist** (systemd unit · medical PC · manojz cache).
   **Never hand-copy between machines** — a hand-copy went stale and answered 401 for five days.
3. **Darpan's ₹20,000 SPECIAL** `0cc0b26b38c5` · **Pravesh exits 31-Aug** · **July cash top-ups
   ₹4,519** · **Surendra ₹516** · **Arjun's actual-paid figure** · **Shivani's two August items**.
4. UPI/bank: the correction-checklist day + the 4 disagreement days · **AF-3's duplicate-advance
   scan before the close** · verify **R9** on the box (grouped Advances page).
5. Marg tidy when convenient (nothing deletes): `CLEANUP_DRIVE.bat` on manojz ·
   `CLEANUP_MEDICAL.bat` on the medical PC · empty `D:\Downloads\margsync\_to_delete\` (7.6 MB).

**The full, always-current list is `OWNER_TODO_LIVE.md`.**

---

## ⭐1 — WHAT I ASKED TO BE PRIORITISED THIS SESSION

**The `/ops` runbook surface — parked at S201 for priority in S202.** Symptom-indexed, owner-only,
each fault a dropdown decision tree, linked as a **second door** from every `/finance/health` row.
**Two rulings already made and carried forward:**

- **Served from the repo, never uploaded.** An uploaded copy is a second source of truth with no
  hash and no owner — F-23 and the S131 stumps exactly.
- **A runbook page never states a hash, version, count or path inline; it reads them live.**
  Otherwise it is a delta doc, which **D202** forbids.

**Honest prerequisite: B2 first.** The 60-second check's three files all live on manojz and the VPS
cannot see them, so `/ops` without B2 tells me what to do but not whether I need to. Cheap version:
manojz posts a small status JSON at the end of each 10-minute pull.

Then: **F-183** (the backwards `0.60` tier + single-digit clinic IDs) · identifier capture on the
health page (73% this week, 57%–92% by day) · B3–B7 · the ledger kit · F-178 surfacing · Staff
Console Phase 0 (my four rulings owed) · **Purchase Portal D335** as the other flagship.

---

## ⭐2 — THE AUGUST CLOSE = the first fully LIVE, ENFORCED run

A leaver (Pravesh) · Darpan's SPECIAL + ₹3.55L schedules · three auto-recoveries · Shivani's two
items · the first suspended-charge cancel/collect cycle. **Watch, don't assume.**

---

## ⚠ ONE REAL FINDING, AND ONE CLAIM I GOT WRONG AND WITHDREW

**F-184 (S201) — the close-out routine never refreshed `deploy_kits/KB_canon_all/`, so the pin
checker could not prove its source.** `verify_live_pins.py` proves the pin list by looking in
**exactly one folder** — `repo/deploy_kits/KB_canon_all/` — for a file that hashes to `source_md5`,
and for the `CANONICAL_MANIFEST.md` **beside it** pinning that same hash as CURRENT. A per-close
`KB_canon_S###close/` folder does not satisfy it; the checker never looks there.

**The S200 close left that folder at Register v5.44 (S199) while pinning v5.45**, so its run could
only ever return **AMBER (`register_not_in_repo`)** — every pinned file matching, the source
unprovable. The S201 run returned exactly that, and reading the checker rather than trusting the
word "GREEN" in a header is what found it. **F-134's shape, one folder over: a derived artefact must
be rebuilt in the same routine that changes its source.** Fixed structurally — `END_OF_SESSION_PROMPT`
v7 gains **step A8b**, and the S201 canon (plus the missing v5.45) is now in that folder.

**WITHDRAWN — my F-123 claim was wrong in the part that mattered.** At this close I flagged four
bare-named `CANONICAL_MANIFEST.md` copies in the repo as rule-erosion. **`KB_canon_all/CANONICAL_MANIFEST.md`
is not drift — it is load-bearing**, and the checker cannot work without it. I asserted that before
reading `verify_live_pins.py`, which is the same fault as reporting `vps_deploy.sh` broken off the
stale repo copy earlier in this session: **a claim about a mechanism, made without opening the
mechanism.** The per-close snapshot copies remain a looser question and are harmless; there is no
F-123 action for you to authorise. Recorded rather than deleted, per F-23 discipline.

**Next free: D349 · F-184 · A-D25 · Session 202.**
**Cold kit: 4 of 3–5 since S197 — DUE. Take it at the S202 close.**

*START_HERE_SESSION_202 · written at the S201 close · supersedes 201.*
