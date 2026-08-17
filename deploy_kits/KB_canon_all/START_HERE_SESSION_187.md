# START HERE — Session 187

Hi Claude. Continuing my clinic-automation project (**Session 187**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(Session entry point regenerated at the S186 close. Follow `START_HERE_PROMPT_v5` = the project's
custom instructions. This file carries the Phase-0 pointers current as of S186 and the S187 tasks.)*

**Working protocol:** plain language · ONE step at a time, wait for explicit confirmation · full-file
replacements · ALL-CAPS = urgent · mask patient numbers to last-4, never print secrets · nothing live
rebuilt without explicit OK, manual workflow stays the fallback · build/test offline, **rehearse the
installer against a throwaway target**, then install via the **D317 kit chain**, now delivered by the
**D324 method** (kits written straight into the local repo, published by one pasted `PUSH.bat` path) ·
asset + finance apps use system `/usr/bin/python3` (F-53); `/root/wa` + portal gunicorn use
`/root/wa/venv/bin/python3`.

---

## ✅ The canon is CURRENT. Nothing is owed.

S186 folded itself in completely: **KB Register v5.11** · **KB History Archive v1.34** ·
**Fault_Action_Register v2.20** · **HANDOFF_RUNBOOK v120** · manifest rebuilt. **The Fault Register has
no owed append for the first time since S181.** Expect Phase 0 to be quiet.

## Phase 0 — do this FIRST (verification before work)

**Documents** — one command against git bytes *(a hash verdict is pronounced only on bytes delivered
as a FILE; re-keyed inline text may corroborate, never convict)*:
```
cd /tmp && rm -rf kbv && git clone --depth 1 -q \
  https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
  && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```
**Then the F-88 cross-check** — a passing `md5sum -c` proves a kit internally *consistent*, not
*current*: extract every md5 in `CANONICAL_MANIFEST.md` and match it against real file hashes; the
tokens matching no file are live-code pins, Tier-2 digests and the three D316 closed-as-lost rows.
**Then the F-107 inverse check:** confirm every Tier-0 document you are about to read **has a manifest
row** — the manifest catches a *wrong* row and is blind to a *missing* one.

**Live code (D321) — owner-run on the box:**
```
python3 /root/deploy/verify_live_pins.py
```
It should read **GREEN** this session. If it says AMBER, its pin list was not regenerated at the S186
close — say so rather than working around it (F-110).

1. Open **`CANONICAL_MANIFEST.md`** and verify every doc row by md5.
2. Read into context only **Tier 0**: manifest, this file, **KB Register v5.11**,
   **HANDOFF_RUNBOOK v120**. No open incident. Open S183/S184/S186 finance docs on demand.
3. Confirm, then ask which backlog item to start (**Runbook v120 §2**).

## ⭐ S187 TASKS — owner's choice

**A. The item-wise go-live decision.** Everything it was waiting on is done: the daily Marg path is
proven end to end (14/15 Aug, 33 bills, 147 drug lines), the review queue is empty, the dashboard is
quiet. This is a decision, not a build.

**B. 12 June — the Marg lines exceed the declared day total by ₹8,487.** Live money, hidden inside 120
identical shouts since June. Also: **3 May has zero lines** (re-upload the May export through the
workbench — that is F-113 made visible), 9 May −₹665, 2 Jun −₹690.

**C. The F-107 / F-108 structural checks** — make the inverse Phase-0 check mechanical, and assert the
Fault Register's next-free number equals its last index row + 1 at every append.

**Blocked on the owner, not on me:** Darpan's ₹30,000 (scans — **and the ₹10,000's category is still
undecided**; booking it wrong double-counts in his Ledger) · 14/15 Aug still `draft` · the **Hindi
labels**, which unblock the custody block on Darpan's entry screen.

**Owed and named:** the CLI `marg_backfill.py` NOT-FILED flag and its `attributed ? · review ?` display
bug · the Staff Ledger check on ₹70,000 of Darpan's advances · F-106 selftest split · F-97 part 2 and
the 76 untracked live files · 4 May and 27 May missing days.

## Where the truth lives

- **`CANONICAL_MANIFEST.md`** — doc set / tiers / hashes. STATUS **current at S186**.
- **KB Register v5.11** (now) · **KB History Archive v1.34** (history, §S65–§S186) ·
  **Fault_Action_Register v2.20** (F-0 … F-114, next free **F-115**) · **HANDOFF_RUNBOOK v120**.
- **Live finance**: cash in hand **₹2,05,198** (→ ₹1,75,198 once Darpan's ₹30,000 is entered) ·
  `negative_cash` **0** · review queue **0** · `line_sum_vs_day_total` **4** · 15 verified Yes Bank
  deposits · Marg uploads through `/finance/workbench`.

**Connected sources:** Google Drive · Gmail · Notion · GitHub (`drmanoj-clinic-automation`, PUBLIC by
D320) · ClickUp parked (D17). Patient data is NOT in this project.

**Next free: D325 · F-115 · A-D25 · Session 187.** Cold-kit count **2 of 3–5**.

*START_HERE_SESSION_187 — regenerated at the S186 close. Supersedes START_HERE_SESSION_186.*
