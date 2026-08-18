# START HERE — Session 189

Hi Claude. Continuing my clinic-automation project (**Session 189**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(Session entry point regenerated at the S188 close. Follow `START_HERE_PROMPT_v5` = the project's
custom instructions. This file carries the Phase-0 pointers current as of the S188 close and the
S189 tasks.)*

**Working protocol:** plain language · ONE step at a time, wait for explicit confirmation · full-file
replacements · ALL-CAPS = urgent · mask patient numbers to last-4, never print secrets — **a secret
pasted into chat is burned, and repo-write credentials never transit chat (D328)** · nothing live
rebuilt without explicit OK, manual workflow stays the fallback · build/test offline, rehearse the
installer against a throwaway target, **`bash -n` the WHOLE installer (F-126)**, **write the
projection down BEFORE measuring**, then install via the **D317 kit chain**, published by
**`PUBLISH_ALL.bat`** (D328) · asset + finance apps use system `/usr/bin/python3` (F-53);
`/root/wa` + portal gunicorn use `/root/wa/venv/bin/python3` · **new/rebuilt pages follow
`Clinic_Design_Language_v1.md`** · **never run a bare `git` command against the desktop mount — use
`git --no-optional-locks` (F-131)**.

---

## The canon is CURRENT, folded in AT the S188 close. Nothing is owed.

Session 188 shipped **two kits** (Daily Flow v2 stage D2 — Darpan's mirror; and its F-129 fix) and
folded everything in the same day: Archive **v1.37** (§S188) · Fault Register **v2.24**
(F-127…F-131, five findings, all the session they were raised — **fourth consecutive clean close**) ·
Register **v5.24** · Runbook **v123** · manifest rebuilt. **No decision minted** — S188 is the
execution of D326.

## Phase 0 — do this FIRST (verification before work)

**Documents** — one command against git bytes *(a hash verdict is pronounced only on bytes delivered
as a FILE; re-keyed inline text may corroborate, never convict)*:
```
cd /tmp && rm -rf kbv && git clone --depth 1 -q \
  https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv \
  && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```
It must exit **0** — a WARNING is a FAIL (F-119). **Then the F-88 cross-check** (manifest md5 tokens
vs real file hashes; every non-matching token must be a live-code pin, a Tier-2 digest, or a D316
closed-as-lost row). **Then the F-107 inverse check**: every Tier-0 document about to be read has a
manifest row. **And exactly ONE file in the clone may be named `CANONICAL_MANIFEST.md` (F-123).**

**Live code (D321) — owner-run on the box:**
```
python3 /root/deploy/verify_live_pins.py
```
Expect **GREEN with `source : VERIFIED`**. If AMBER, read its stated reason (usually: pull the repo,
or the pin list predates the close). If RED, the drift is evidence about the record first (F-118).

1. Open **`CANONICAL_MANIFEST.md`** and verify every doc row by md5.
2. Read into context only **Tier 0**: manifest, this file, **KB Register v5.24**,
   **HANDOFF_RUNBOOK v123**. No open incident.
3. Confirm, then ask which backlog item to start (**Runbook v123 §2**).

## ⭐ S189 TASKS

**A. The two small ones first — both cheap, both closing findings raised at the S188 close.**
**F-130:** add the design-fingerprint assertions (`--surface-page:#f3f2ee`, `id="toTop"`,
`class="kick"`, the folded-help block) to the served-HTML checks for `approvals`, `workbench` and
`review`; the entry page already has them. Until this lands, a page can silently revert its design
and every gate stays green. **F-131:** the owner deletes the 14 `.git/index.lock.*` files from the
PC — the bridge cannot.

**B. THE BUILD, continuing the signed contract** (`S187_Daily_Flow_v2_Target_Design` + the
returns/360 addendum, both pinned — read them before building): **D-R returns at reception** with the
**D327 `counter` role** → **360 wiring** (Console Sanjeevni strip + refill-skippers, read-only
fail-soft) → **orthotics purchase side** (read the Asset Register's scan-purchase data model FIRST) →
**D5 feeds** (Yes Bank via the owner's personal Gmail — forward-rule vs scoped script is the open
decision) → **D6 contextual instructions** (parked; the entry page's `<details class="help">` slots
are already waiting for it). Owner picks the entry point.

**C. The §4a gate FIRST if the build reaches D3:** verify the Staff Ledger ₹70,000 claim
(read-only) — D326(c) blocks the salary bridge until it is done.

**D. Tailscale + RustDesk** — owner's PC + medical PC (~30 min at both). **Now also worth putting the
VPS on the tailnet:** S188 was driven from a phone over public SSH, and a tailnet would make that
routine and let public SSH close.

**Owner one-clicks, whenever convenient:** **walk Darpan through Save → the check → File, once,
before 10am** (the only item here a person must do) · file **17 Aug**, then **Apply** its staged Marg
push — that also gives the mirror its first real Marg comparison · Darpan's ₹30,000 scans · submit
and approve 14 & 15 Aug (now safe to open) · enter the orthotics keywords.

**Owed and named:** `.gitattributes` — pin `*.html` and `*.new` to `eol=lf` (D164 did `*.py`/`*.sh`
and stopped) · **F-97 part 2 — the repo's `finance/` tree is seven builds stale**, live bytes exist
only inside kits · CLI `marg_backfill.py` NOT-FILED flag + display bug · F-106 selftest split ·
F-107/F-108 checks made mechanical · the three superseded intermediates in `KB_canon_all` with no
manifest row · 4 May + 27 May · 12 Jun ₹8,487 + 3 May zero-lines · Hindi labels · WABA (F-82,
vendor) · F-92 · F-93 · the stray file named `followup-tracker/python test_send.py`.

## Where the truth lives

- **`CANONICAL_MANIFEST.md`** — doc set / tiers / hashes. STATUS **current at S188 close**.
- **KB Register v5.24** (now) · **KB History Archive v1.37** (history, §S65–§S188) ·
  **Fault_Action_Register v2.24** (F-0 … F-131, next free **F-132**) · **HANDOFF_RUNBOOK v123**.
- **Live finance:** cash in hand **₹2,05,198** (→ ₹1,75,198 once Darpan's ₹30,000 is entered) ·
  `negative_cash` **0** · review queue **0** · **17 Aug unfiled with a Marg push staged** · 14/15 Aug
  draft · the branded **Sanjeevni Hub** at `/finance/approvals` is the owner's one page.
- **Live pins:** `finance_app.py` `3a7086f851720dd161bc43c3c1fd45dd` · `finance_ui/finance_entry.html`
  `2c23b461bdae5a4ed6a4c4ed4708b4f9` · `finance_approvals.html` `028255054662924713e03362c3976b05`
  (**verified on the box at S188**) · `portal.py` `bd4ed0a3b89659676e7e193998eeb1a9` ·
  `finance_workbench.html` `420f82c2846bc49d0d12ab5040d8c542` · checker/generator **v1.2**.

**Connected sources:** Google Drive · Gmail · Notion · GitHub (`drmanoj-clinic-automation`, PUBLIC
by D320) · ClickUp parked (D17). Patient data is NOT in this project.

**Next free: D329 · F-132 · A-D25 · Session 189.** Cold-kit count **2 of 3–5**.

*START_HERE_SESSION_189 — regenerated at the S188 close. Supersedes START_HERE_SESSION_188.*
