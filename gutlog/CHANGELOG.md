# Changelog

## v3.0 - 2026-07-19
Full rebuild. Fresh schema (no migration from v2 - negligible data).

**New**
- Completion-ring strip + streak counter on the Log tab; gradient header.
- Multi-select symptom grid (tap-all-that-apply, one save).
- Library-backed meals: 87-food library behind a search/basket picker with
  live protein-vs-57g bar and FODMAP-load meter; just-in-time new foods; a
  Manage-Foods sub-screen (favourite / edit / delete / filter).
- Per-dose PRN ledger: multi-select medicines logged as individual timestamped
  dose events; "+1 dose" repeat; "today so far" grouping.
- Buprenorphine patch tracker (apply/remove, days-worn counter).
- Course tracker with live day counter.
- Vitals, episodes, food tests, labs (next-due), consults, file vault.
- Review tab: SVG trend charts (pain/tea/coffee, FODMAP load, doses/day),
  protein hit-rate, tables, and 11 per-table CSV exports.
- Everything timestamped; whole-DB backup + per-table CSV.

**Decisions locked**
- Fresh start over migration (uniform ledger for clean analytics).
- 5-tab nav kept (Log / Meals / Meds / Files / Review); food library moved to
  background (behind meals) rather than its own tab.
- Tylenol = paracetamol 500 mg (corrected from 650).
- Zuprinor = buprenorphine transdermal 5 mcg/hr, own entry type.
- Protein target 57 g/day; tea recipe 0.3 tsp sugar; coffee half-milk/half-water.

## v3.0.1 - 2026-07-19 (same day, post-deploy patch)
- **Vitals:** added Temperature (deg F) field + `vitals.temp` column, delivered
  to the live DB via idempotent auto-migration (no rebuild, no password reset).
- **Day tab gut-pain sites:** added Right iliac fossa, Hypogastrium (renamed
  from "Hypogastric"), Left flank, Right flank, Umbilical, Diffuse.
- **Episodes:** added a Back group (Back pain, Low back pain) alongside
  Neck and Hip.
- **Ops:** GutLog registered in clinic-watchdog (guarded services 9 -> 10).
