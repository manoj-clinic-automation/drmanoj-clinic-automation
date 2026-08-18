# START HERE — Session 190

Hi Claude. Continuing my clinic-automation project (**Session 190**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(Session entry point written at the S189 close. Follow `START_HERE_PROMPT_v5` = the project's
custom instructions.)*

**Working protocol:** plain language · ONE step at a time, wait for explicit confirmation · full-file
replacements · ALL-CAPS = urgent · mask patient numbers to last-4, never print secrets — a secret
pasted into chat is burned; repo-write credentials never transit chat (D328) · nothing live rebuilt
without explicit OK · build/test offline against a store carrying the LIVE store's SHAPE (F-140) ·
`bash -n` the WHOLE installer (F-126) · **the projection written BEFORE measuring** · a count-equal
kit proves itself by REPRODUCING the failure it cures (W1b/E1b) · every selftest check that can fail
embeds the server's answer in its label · delta assertions across the whole block (F-106/F-138) ·
install via the D317 kit chain, published by `PUBLISH_ALL.bat` (D328) · asset + finance apps use
system `/usr/bin/python3` (F-53); `/root/wa` + portal use `/root/wa/venv/bin/python3` · new/rebuilt
pages follow `Clinic_Design_Language_v1` · `git --no-optional-locks` against the desktop mount ·
**EOS automation boundary (Runbook v125 §4): the assistant runs the whole close; the owner's
residual work is one PUBLISH_ALL double-click + the on-box pin-list copy.**

## The canon is CURRENT, folded in AT the S189 close. Nothing is owed.

S189: seven kits live, one retired unlived by its own gate, findings F-130…F-133 + F-135…F-140 all
raised-and-handled the session they were found, the ₹2 lakh question closed by schema + count, the
₹70,000 gate VERIFIED OPEN, **D329 minted** (the Advance Pool — the signed design is
`S189_Advance_Pool_Design_D329.md`), smoke **478 → 509**, THREE mid-session canon folds each proven
zero-loss by reverse application, four proved GREENs. Archive **v1.40** (§S189) · Fault Register
**v2.29** (F-0…F-140, next free **F-141**) · Register **v5.30** · Runbook **v125** ·
`EOS_DEFINITION_PORTABLE.md` written.

> **Read F-135 and F-137 before trusting any instruction this file gives you.** Twice this project's
> record prescribed work against files nobody had opened. Survey first, always.

## Phase 0 — do this FIRST (verification before work)

**Documents** — one command against git bytes:
```
cd /tmp && rm -rf kbv && git clone --depth 1 -q \
  https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
  && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```
Exit **0**; a WARNING is a FAIL (F-119). Then the F-88 cross-check · the F-107 inverse check ·
exactly ONE `CANONICAL_MANIFEST.md` (F-123) · confirm the pin list's `source_md5` equals the
manifest's CURRENT Register pin by hashing the Register file (A8/F-134).

**Live code (D321) — owner-run on the box:**
```
python3 /root/deploy/verify_live_pins.py
```
Expect **GREEN · match 43 · `source : VERIFIED ON THIS MACHINE`**. If RED on `finance_app.py` /
`finance_entry.html`, the owner has not yet copied `live_pins_S189close.txt` to
`/root/deploy/live_pins.txt` — the one manual step, not a fault.

1. Open **`CANONICAL_MANIFEST.md`**, verify every row by md5.
2. Read into context only **Tier 0**: manifest, this file, **KB Register v5.30**, **Runbook v125**.
   No open incident.
3. Confirm, then ask which backlog item to start (**Runbook v125 §2**).

## ⭐ S190 TASKS

**A. THE D329 BUILD — the Advance Pool (top task).** Read the signed contract
`S189_Advance_Pool_Design_D329.md` FIRST, then the LIVE ledger engine's close code (F-137: read the
schema before integrating). Order: **`S190_SL1`** (Staff Ledger: pool categories · the
`advance_instalment` setting, default ₹5,000 · close integration in the deduction order ·
Advance-Skip max 2/FY, no capitalisation · Advance-Waive, reasoned · the reconciliation card with
one-tap LINK · the scoped receive endpoint, fail-closed) → **token generated on-box into both
systemd units** (never chat) → **`S190_F1`** (finance: push-on-approval, idempotent by expense id ·
LINK · `ledger_posted` truthful at last). Rehearse the ledger build against a JSONL store shaped
like the live one (F-140). The pool opens at ₹20,000; the ₹40,000 stays out (verified recovered).

**B. If the ₹30,000 sitting hasn't happened yet, it goes first** (Runbook §2 ⭐0 — one sitting,
four backlog items, projection ₹1,75,198.00 to the rupee).

**C. Owed and named:** Runbook v125 §2 item 2 — the full list, headed by `dev_seed_smoke_db.py`
(the F-87 tool stalls at the S180 schema; owner's call whether it earns F-141), the draft-resave
hazard, and F-97 part 2 (the repo's `finance/` tree eight builds stale).

## Where the truth lives

- **`CANONICAL_MANIFEST.md`** — doc set / tiers / hashes. STATUS **current at the S189 close**.
- **KB Register v5.30** (now) · **KB History Archive v1.40** (§S65–§S189) · **Fault_Action_Register
  v2.29** (F-0…F-140, next free **F-141**) · **HANDOFF_RUNBOOK v125** · **END_OF_SESSION_PROMPT v5**
  · **EOS_DEFINITION_PORTABLE** (the cross-project EOS spec).
- **Live finance:** smoke **509/509** · cash in hand ₹2,05,198 (→ ₹1,75,198 once the ₹30,000 is
  entered — the counted figure) · custody: Dr Manoj ₹18,963 · Dr Bhawna ₹1,56,235 (17 Aug count) ·
  17 Aug unfiled with its Marg push staged · 14/15 Aug draft · the ₹70,000 verified closed.
- **Live pins:** `finance_app.py` `5cb73ff83b591535053c7911026ecd8b` · `finance_entry.html`
  `1c7d2dc3179f29e9de0b9fb0d77c6fe1` · `finance_approvals.html` `028255054662924713e03362c3976b05` ·
  `portal.py` `bd4ed0a3b89659676e7e193998eeb1a9` · `staff_ledger.py` `92665b64f015fee9302ac3da6100f5c8`
  (service-verified S189) · checker/generator **v1.2**.

**Connected sources:** Google Drive · Gmail · Notion · GitHub (PUBLIC by D320) · ClickUp parked
(D17). Patient data is NOT in this project.

**Next free: D330 · F-141 · A-D25 · Session 190.** Cold-kit count **3 of 3–5** (`KB_S189_close`).

*START_HERE_SESSION_190 — written at the S189 close. Supersedes START_HERE_SESSION_189.*
