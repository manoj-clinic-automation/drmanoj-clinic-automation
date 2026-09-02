# HANDOFF RUNBOOK — v150 · S217/218 marathon close · 02-Sep-2026
*Supersedes v149 (S216 close). Tier 0.*

## §0 · WHAT HAPPENED
One marathon session, 01–02 Sep. Opened on "MARG UPI MPR not reaching, Darpan drawer
inflated, CounterGaps 500". Diagnosis found FOUR stacked faults: 150 smoke-fixture files
poisoning the live statement store since S179 (a 30-Aug backfill wiped 9 days of bank
detail) · the undeployed D356 column crashing day-gaps on the first unmatched day · the
0.70 confidence gate silently parking ~118 CNs + name-only bills for 5 months · ICICI's
mail slipping past the single 09:30 push. All four repaired the same session, then the
owner ordered and received the FINAL hub: English-only, alert bar carrying everything,
▶ Walk the day, Bank MPR card, staff-cards directory, heal-on-landing engine, bank-truth
corrections (his OK), the D355 review backfill (queue → 0), drawer true at ₹8,817.
Full table: `S218_BUILD_BRIEF.md`. Contract: `S218_CARDS_FINAL_CONTRACT.md` rev2.

## §1 · MENTAL MODELS EARNED
- **The owner's law of order-dependence:** feeds land late and out of order; a record
  written in the gap sticks after reality heals. Live-computed surfaces heal themselves;
  written records need a heal engine. Never build a shouting record without its recheck.
- **A gate that quietly diverts is worse than one that refuses loudly** — the review queue
  hid five months of returns while every surface said "no patient".
- **Corroboration against a stub pool is not corroboration** (WALK-IN's 1,956 bills
  "corroborate" anything) — verdicts need an identity precondition.
- A test's fixtures must never share a store with live data (150 files said so).
- An escape level is a byte: assert patch anchors from EXECUTED constants, never from
  re-read source (the S218 patch refusal).
- The guard chain works: three pin-guards refused exactly when they should have.

## §2 · THE LIVE BACKLOG — the owner's Marg-first plan
In START_HERE_SESSION_219 §plan, verbatim priority M1–M7 + the unavoidable-in-between
list. NEFT portal WAITS (owner). August staff close (Surendra ₹516.08, Pravesh ₹569)
still owed and carries its clock.

## §3 · INSTALL DISCIPLINE — additions earned
- Money writes never ship blind: harvest live bytes first (auto-apply is the test case).
- Multi-step pastes may stop mid-chain: design every paste so a partial run is safe and
  the completion paste needs no guards that the first half already consumed.
- Full-file page replacements guarded on the live pin beat stacked HTML patches.
- Rehearse on a LIVE-SHAPED copy (backup + simulated today), not the bare backup.

## §4 · THE BOUNDARY — what this close deferred, explicitly
Archive v1.64 append · Register v5.66 · manifest recompute · gen_live_pins · cold kit +
mirror (F: C-S216-8 stall unresolved) · Notion log · F-minting (7 candidates in the
brief) — **all owed at the S219 open**, S211-close precedent. The owner's pin readback
paste (OWNER_TODO ⭐0) is the first act of S219: finance_app took two guarded hotfixes
after its kit, so its md5 is READ from the box, never assumed. Four one-store runbooks
(v116, v139, v144, v145) still await filing to git canon — carried, not deleted.

*v150 · written at the S217/218 close, 02-Sep-2026.*
