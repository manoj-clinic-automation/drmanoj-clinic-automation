# S218_HUB_FINAL_2 — the clean page (final data pass, owner's "OK" of 02-Sep)

1. **correct_days_s218.py** — the two relic days move to bank truth (owner's
   explicit OK): 28-Aug cash 8,710/UPI 6,687 · 31-Aug cash 32,809/UPI 7,363.
   Totals unchanged, old lines preserved in day_revision, reconcile re-run —
   both mismatch flags close themselves; the drawer drops ₹13,051 to its true
   position. Rehearsed: closing 2,95,086 → 2,82,035, match=True both days.
2. **backfill_lookup_s218.py** — books every open review row (86 at rehearsal)
   per D355: clinic-id-in-name → master; phone-last4+name unique → master;
   else the bill's own name as an open stub (never a silent queue). One
   traceable ingest_batch per day (adapter s218_lookup); review rows resolved,
   never deleted; per-day money-effect table printed AND written to
   /root/finance/s218_backfill_effects.csv for Darpan. Queue → 0. Idempotent.
3. **finance_heal.py v2** — adds the line_sum recheck (review empty + the live
   identity rule clean → healed). The "12 days waiting" contradiction ends.
4. **finance_approvals.html v4** — Staff cards card on the owner's hub
   (registry-driven, same list as Darpan's) + nav link.
5. **patch_walk_link_s218.py** — the walk's not-filed step now opens the
   Review console (the old /finance/daily link role-bounced the owner to the
   portal — his live-walk catch).
Known-honest remainder: bills booked under a name-stub count as "unmatched"
in identity checks until the master gains them — they sit folded in the
parked section, never shouting; master matches improve with each Docterz sync.
Rollback: day_revision rows (corrections) · ingest_batch adapter='s218_lookup'
(backfill, per-batch reversible) · .bak files (patches).
