# START HERE — Session 188

Hi Claude. Continuing my clinic-automation project (**Session 188**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(Session entry point regenerated at the S187 close. Follow `START_HERE_PROMPT_v5` = the project's
custom instructions. This file carries the Phase-0 pointers current as of the S187 close and the
S188 tasks.)*

**Working protocol:** plain language · ONE step at a time, wait for explicit confirmation · full-file
replacements · ALL-CAPS = urgent · mask patient numbers to last-4, never print secrets — **a secret
pasted into chat is burned (proven twice at S187), and repo-write credentials never transit chat
(D328)** · nothing live rebuilt without explicit OK, manual workflow stays the fallback · build/test
offline, rehearse the installer against a throwaway target, **`bash -n` the WHOLE installer
(F-126)**, then install via the **D317 kit chain**, published by **`PUBLISH_ALL.bat`** (one desktop
icon, D328; per-kit `PUSH.bat` as fallback) · asset + finance apps use system `/usr/bin/python3`
(F-53); `/root/wa` + portal gunicorn use `/root/wa/venv/bin/python3` · **new/rebuilt pages follow
`Clinic_Design_Language_v1.md`** (the S187 default).

---

## The canon is CURRENT, folded in AT the S187 close. Nothing is owed.

Session 187 shipped **eight kits** (attestation chain v1.2 · B5 reception push · Daily Flow v2
stage D1 · the portal tile chain · the branded Sanjeevni Hub) and then folded everything in the same
day: Archive **v1.36** (§S187) · Fault Register **v2.22** (F-122…F-126, second consecutive close
with no owed append) · Register **v5.22** · Runbook **v122** · manifest rebuilt **and
de-duplicated** (the five "(pre-…) CURRENT" rows are gone) · the twin manifest retired (F-123) ·
the two owed S186 docs and the three S187 design docs **filed and pinned**.

## Phase 0 — do this FIRST (verification before work)

**Documents** — one command against git bytes *(a hash verdict is pronounced only on bytes delivered
as a FILE; re-keyed inline text may corroborate, never convict)*:
```
cd /tmp && rm -rf kbv && git clone --depth 1 -q \
  https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
  && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```
It must exit **0** — a WARNING is a FAIL (F-119). **Then the F-88 cross-check** (manifest md5 tokens
vs real file hashes; non-matching tokens must each be a live-code pin, a Tier-2 digest, or a D316
closed-as-lost row). **Then the F-107 inverse check**: every Tier-0 document about to be read has a
manifest row. **And exactly ONE file in the clone may be named `CANONICAL_MANIFEST.md` (F-123).**

**Live code (D321) — owner-run on the box:**
```
python3 /root/deploy/verify_live_pins.py
```
**Expect GREEN with `source : VERIFIED` — and for the first time the word is PROVED**: the v1.2
checker hash-hunts the pin list's source Register in `/root/deploy/repo` canon and parses the
manifest beside it (F-122 closed). If AMBER, read its stated reason (usually: pull the repo, or the
pin list predates the close). If RED, the drift is evidence about the record first (F-118).

1. Open **`CANONICAL_MANIFEST.md`** and verify every doc row by md5.
2. Read into context only **Tier 0**: manifest, this file, **KB Register v5.22**,
   **HANDOFF_RUNBOOK v122**. No open incident. Open the S187 design docs when the build touches
   them — they are Tier 1 and pinned.
3. Confirm, then ask which backlog item to start (**Runbook v122 §2**).

## ⭐ S188 TASKS

**A. THE BUILD, on the signed Daily Flow v2 contract** (`S187_Daily_Flow_v2_Target_Design` + the
returns/360 addendum, both pinned — read them before building): **D-R returns at reception** (with
the **D327 `counter` role** — portal login, look-up/log-returns/orthotics only, nothing
checker-side) → **D2 Darpan's mirror** (save-then-see, `edited_after_reveal`) → **360 wiring**
(Console Sanjeevni strip + refill-skipper list, read-only fail-soft) → **orthotics purchase side**
(asset-app scanned purchase bills; read the Asset Register's scan-purchase data model FIRST) →
**D5 feeds** (Yes Bank via the owner's personal Gmail — forward-rule vs scoped script is the open
decision) → **D6 contextual instructions** (parked; pairs with Hindi labels). Owner picks the entry
point; proposed order is the addendum §8.4.

**B. The §4a gate FIRST if the build reaches D3:** verify the Staff Ledger ₹70,000 claim (read-only)
— D326(c) blocks the salary bridge until it is done.

**C. Tailscale + RustDesk** — guided config, owner's PC + medical PC first; parallel track,
whenever the owner has ~30 minutes at both machines.

**Owner one-clicks, whenever convenient:** **Apply** the first pending reception push (Hub → Marg
card) · enter the orthotics keywords (Hub → Orthotics) · run `MAKE_DESKTOP_ICON.bat` on the medical
PC (files already beside the sender) · Darpan's ₹30,000 scans (the ₹10,000's category still
undecided) · submit/approve 14 & 15 Aug.

**Owed and named:** CLI `marg_backfill.py` NOT-FILED flag + display bug · F-106 selftest split ·
F-97 part 2 (loaded-in-memory · PC-side half · 76 untracked files) · F-107/F-108 checks made
mechanical · 4 May + 27 May · 12 Jun ₹8,487 + 3 May zero-lines · Hindi labels · WABA (F-82,
vendor) · F-92 · F-93.

## Where the truth lives

- **`CANONICAL_MANIFEST.md`** — doc set / tiers / hashes. STATUS **current at S187 close**.
- **KB Register v5.22** (now) · **KB History Archive v1.36** (history, §S65–§S187) ·
  **Fault_Action_Register v2.22** (F-0 … F-126, next free **F-127**) · **HANDOFF_RUNBOOK v122**.
- **Live finance:** cash in hand **₹2,05,198** (→ ₹1,75,198 once Darpan's ₹30,000 is entered) ·
  `negative_cash` **0** · review queue **0** · one reception push staged awaiting Apply · the
  branded **Sanjeevni Hub** at `/finance/approvals` is the owner's one page; the workbench keeps
  Yes Bank / custody entry / drawer count; month close stays on review.
- **Live pins:** `finance_app.py` `db4373a5671dc90d384166a5771e098b` · `finance_approvals.html`
  `028255054662924713e03362c3976b05` · `portal.py` `bd4ed0a3b89659676e7e193998eeb1a9` ·
  `finance_workbench.html` `420f82c2846bc49d0d12ab5040d8c542` · checker/generator **v1.2**.

**Connected sources:** Google Drive · Gmail · Notion · GitHub (`drmanoj-clinic-automation`, PUBLIC
by D320) · ClickUp parked (D17). Patient data is NOT in this project.

**Next free: D329 · F-127 · A-D25 · Session 188.** Cold-kit count **1 of 3–5** (`KB_S187_close`).

*START_HERE_SESSION_188 — regenerated at the S187 close. Supersedes START_HERE_SESSION_187.*
