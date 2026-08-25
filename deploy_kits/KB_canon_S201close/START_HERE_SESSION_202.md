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

## ⚠ ONE CANDIDATE FINDING, RECORDED NOT MINTED (your ruling, or mine if you'd rather)

**F-123 is drifting, and the S201 close found it while running Phase 0's own check.** S187 retired
the stale twin so that *exactly one* file named `CANONICAL_MANIFEST.md` existed in the repo, and
S191's Phase 0 confirmed it (the other two were correctly named `.SNAPSHOT_S181` and
`.RETIRED_S177_stale`). **There are now FOUR bare-named copies** — the real one at the repo root
plus a snapshot in each of `KB_canon_all/`, `KB_canon_S198close/`, `KB_canon_S199close/` and
`KB_canon_S200close/`. None of the three closes that added one flagged it, and a strict F-123 check
would now refuse.

**Nothing is wrong with the content** — each is that close's honest snapshot. The fault is that the
rule S187 established has been quietly eroded, which is how `Diagnostics_v1_7` and the S131 stumps
began. **The S201 close deliberately did NOT add a fifth** (`KB_canon_S201close/` carries no
manifest copy; `SUMS_NOTE.txt` there says so and gives the root manifest's md5 instead).

**Recorded, not fixed**, because renaming four files in your repo is a change to something already
published and that is yours to authorise. The S187 remedy is the obvious one: rename each to
`CANONICAL_MANIFEST.md.SNAPSHOT_S###`. Say the word at the S202 open and it becomes **F-184**, or
tell me to just do it.

---

**Next free: D349 · F-184 · A-D25 · Session 202.**
**Cold kit: 4 of 3–5 since S197 — DUE. Take it at the S202 close.**

*START_HERE_SESSION_202 · written at the S201 close · supersedes 201.*
