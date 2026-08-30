# HANDOFF RUNBOOK — Session 208 close · 30 August 2026 · v142

**Tier 0. Read at Phase 0 with the manifest, the Register and any open incident.**

---

## §0 — WHAT HAPPENED

**The seven-kit night** — an attended build of ~30 hours (28-Aug ~16:30 → 30-Aug ~04:30 IST),
the largest session in the project. **SEVEN kits installed GREEN on the VPS**, in order:

| kit | one line | proof at install |
|---|---|---|
| `S208_STOCK_LEDGER` | the stock loop at `/finance/stock`; expected stock COMPUTED (baseline + dated purchases − sales) — supersedes S207_STOCK_VPS, which could never have worked (F-237 cand.) | 44/44 + 14/14 gate-join; smoke 722=722 |
| `S208_BANKMATCH` | every bank transaction kept; **320 files backfilled = 1,007 txns / 70 days**; matcher cron 09:45 +/15min→12:00 | 21/21 on the real 27-Aug; smoke = |
| `S208_DARPAN` | the day card (§0d: checker model, ₹50 tolerance, two-tap exceptions) + corrections page + owner tools; filing guard OFF by switch | 40/40; smoke = |
| `S208_LEDGER3` | ledger-check / repair-view / owner transfer · **pendCard predicate APPLIED** · `/finance/pipeline` | 56/56; smoke = |
| `S208_STAFF` | the S207 joiner register at `/finance/staff` with guided join/exit; **code register seeded (13, ghost 100 retired, next 101)**; two latent defects fixed (F-239 cand.) | 65/65 + 23/23; smoke = |
| `S208_UIFIX` | review tiles become doors; approvals nav links + flag ✕ — built from live bytes captured **in the owner-signed browser** (F-169 closed) | sha-proven both ends |
| `S208_CONSOLE` | the owner's console: verdicts computed FRESH, CN = sales-return back-audit vs the patient's own bill, **untraceable return ⇒ owner approval gate**, short-ID lookup | 74/74; smoke = |

Also: **the ₹5,437 UPI variance decomposed to the rupee** (3 rung-as-cash bills + 2 bank
orphans; the "sale variance" was one ₹2 nameless bill) · **Q1 steps 2–6 DONE** (FEFO
violation-shaped on 25 best-sellers — see `S208_Q1_ANALYTICS_FINDINGS`) · the 27-Aug
Darpan→Bhawna transfer diagnosed (row never reached the server; repair block ready, amount
pending) · **the assistant's browser is signed into the portal and stays signed in.**

## §1 — MENTAL MODELS EARNED

- **The tested path is not the live path** — token vs gate, app vs proxy, page vs HTTP, three
  times in one night. Test the join, not the halves.
- **Anchor gates for additive patches; kit-own md5 for full replacements.** A fingerprint of
  *predicted* history refused a good install and taught this.
- **State-asserting tests age out (F-106).** Delta-based only.
- **The smoke suite defends RULINGS.** It refused a "fix" that contradicted C2 — correctly.
- **A prepared kit is proven only by a live-shape walk** (two green-tested defects, incl. an
  exit flow that could never complete).
- **Records are not status.** Compute verdicts fresh; show the record beside them labelled.
- **The browser is a first-class tool**: signed in once by the owner, it fetched, patched and
  delivered live-only files withboth-end sha proof — and its sign-in persists.

## §2 — OPEN BACKLOG (live list = `OWNER_TODO_LIVE.md`; snapshot)

**Owner:** run `md5sum /root/finance/finance_app.py` (completes the pin list) · 27-Aug transfer
amount → repair block (sprint plan v10) · Darpan onto the card → flip guard · Amir joining via
`/finance/staff` (code 101 ready) + biometric on next visit · Pravesh vidaai same page ·
Amir's visit: BOTH purchase exports 27-Aug→date · point user-manage tile at `/finance/staff` ·
rename `PUBLISH_ALL_.bat` over `PUBLISH_ALL.bat` · ratify/renumber the F-fork (now +F-237/238/239)
· §S205 ruling · token rotation · restore test · 7-May Marg backup cause · Ram Singh chase.
**Build next:** Sprint 5 — patient master to the VPS (GAS push, Followup-Tracker →
`/finance/api/patient-master`) · purchase-bill links into drill-downs · portal tile rename →
"Marg sales pipeline" + landing (one `cat` of the portal file, or the signed-in browser) ·
scanner bake-in · ladder into engines · exchange path · advance-reconciliation UI.

## §3 — INSTALL DISCIPLINE

All seven kits installed by the owner via `vps_deploy.sh`; every installer measured the smoke
suite before touching anything and restored on red (two restores actually fired and were
correct). Full-replacement files' live md5s = their kit md5s. `finance_app.py` carries three
program-patch blocks (stock · darpan · staff) + the pend clause — **its live md5 is the one
pin awaiting capture from the box.** S207_STOCK_VPS carries SUPERSEDED.md — never install it.

## §4 — THE BOUNDARY

The VPS was touched **only** through the owner running gated installers. The assistant executed
no credentials anywhere; the browser sign-in was the owner's own act. `MargArchive` written only
by its watcher. Publishes: owner-run through the gated bat (final publish of this close:
assistant-executed via computer control per the owner's new standing instruction, output
verified). Patient numbers masked throughout; the phone gate ran clean before every commit.

---
*v142 · S208 close · supersedes v141.*
