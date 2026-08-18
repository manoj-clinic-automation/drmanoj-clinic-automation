# D247 — Canonical Data Management: Tiers · Register/Archive Split · Frozen Dossiers

**Dr. Manoj Agarwal Clinic · Bareilly · Session 147 · Owner: Dr. Manoj Agarwal · Drafted with: Claude**

**STATUS: proposed this session (S147). Becomes canonical only on EOS install (owner-verified). Nothing is moved, split, or frozen by this file — it is the decision and the map.**

---

## Part A — DECISION D247 (full text)

**Why.** The KB (`Clinic_Master_KB_SystemsRegister`, v1.72, ~4,300 lines) is append‑only. Every session it gains a `§S###` narrative, a top‑of‑file consolidation note, and the full text of that session's decisions — and sheds nothing. The dominant per‑session cost is reading the whole project history at start and rewriting all of it at end. D202/S100 ("one consolidated file, no delta chain") was meant to stop *fragile* delta chains; in practice it has produced one file that behaves like an ever‑growing delta chain glued together.

**Ruling.**

1. **Register / Archive split.** The KB becomes two consolidated single files:
   - **KB Register** — *current state only*: the systems register, a one‑line decision index (D1…D246), a one‑line finding index, current live‑file versions + md5s, and the backlog. **Authority on what is true NOW.** Rides the session loop.
   - **KB History Archive** — *append‑only*: every `§S###` narrative and every full D/F text, carried over **verbatim** (nothing dropped — D172). **Authority on what HAPPENED.** Out of the loop; opened on demand.
   - Both remain consolidated single files; neither is a delta chain. **This clarifies D202/S100, it does not repeal it.**

2. **Three tiers.** Every canonical doc is tagged Tier 0/1/2 in `CANONICAL_MANIFEST.md`:
   - **Tier 0 (loop)** — read at start, rewritten at end.
   - **Tier 1 (reference)** — hash‑verified at start; read only if the session's task touches it; rewritten only if it changed.
   - **Tier 2 (frozen)** — hash‑verified at start; never read in the loop, never rewritten; changing one requires an **explicit owner waiver** (D34 discipline) + a version bump.

3. **Frozen products get a dossier + a ledger.** Each frozen product has exactly **one** canonical as‑built dossier (the deep‑reference doc). The **FROZEN ledger** is a thin index — one row per product: name · dossier file · artefact location · artefact md5 · frozen‑as‑of (S/D) · waiver rule. **Dossier weight matches product weight** (a heavy audit vs a one‑page card).

4. **Phase 0 verifies the manifest by md5 for ALL tiers, but reads only Tier 0.** Integrity is proven for everything (cheap — hash compare only); context is spent only on the hot set.

5. **Authority order (unchanged in spirit).** "The KB wins if anything disagrees" now reads: **the Register wins on current state; the Archive wins on history.** The two cannot conflict — the Archive is dated history and asserts nothing about *now*.

**Provenance (binding).** Every md5 in the manifest is computed from the **live artefact** at freeze/version time (D172/D188) — no hash is ever assumed. A dossier for a not‑yet‑documented product is built **from the live artefact, never from memory.**

**Relates to.** Clarifies D202/S100 · extends D34 (freeze‑by‑waiver) to the frozen‑product set · parents D223/D236/D246 (the three‑product lineage).

---

## Part B — CANONICAL MANIFEST (tiered)  → becomes `CANONICAL_MANIFEST.md`

*md5 shown where already on record (from the S147 Phase 0 table). "compute at EOS" = to be hashed from the live artefact when this lands. "pending split/build" = the file does not exist yet.*

### Tier 0 — session loop (read at start · rewritten at end)

| Doc | Version | md5 (doc) | Notes |
|---|---|---|---|
| `START_HERE_SESSION_###` | per session | set at EOS | entry point; regenerated every close‑out |
| **KB Register** | v2.0 (after split) | pending split | current‑state; replaces the monolithic KB in the loop |
| `HANDOFF_RUNBOOK` | v84 | `4da9e09f…` | §0 what happened · §2 backlog |
| active incident | — | — | **only while open**; none open now (F‑44 closed) |

### Tier 1 — reference (hash‑verified · read only if touched · rewrite only if changed)

| Doc | Version | md5 (doc) | Notes |
|---|---|---|---|
| **KB History Archive** | v1.0 (after split) | pending split | all `§S###` + full D/F text, verbatim |
| `Dr_Manoj_Clinic_Umbrella_Architecture` | v1.58 | `728cc649…` | strategy + decisions log |
| `Call_Console_Evolution_Spec` | v2.4 | `63978d98…` | dashboard‑as‑dialer (active subsystem) |
| `Frontend_Dashboard_Documentation` | v4 (S140) | `02ef929b…` | dashboard still evolving (v18.28f, gist tile) |
| `Diagnostics_Surveillance_System_Spec` | v2.3 | `bdd5fa54…` | fault codes / detection |
| `Maintenance_SOP_System_Spec` | v1.1 | `35b257ee…` | forward‑looking (project not live yet) |
| `API_QUICK_REFERENCE_CARD` | — | `68c4fc34…` | small + stable; consult when touching MyOperator |
| `AI_Verdict_Layer_Master` | v1 (S145) | `bd4b67f6…` | Product B analytics |
| `Clinic_Callback_Tracker_AppsScript_Audit` | v1.9 | `41dd9fd6…` | **unfinished audit** (Pass 4 not started); subject still evolving — stays reference, is NOT the frozen dossier |
| `Fault_Action_Register` | v2.1 | compute at EOS | **manifest gap found:** not in the S147 Phase 0 set — reconcile in |
| `END_OF_SESSION_PROMPT_v3` | v3 | compute at EOS | process doc; to be updated in Step 4 |
| closed incident files (e.g. F‑44) | — | `774898e8…` (F‑44) | history; consulted on demand |

### Tier 2 — frozen (hash‑verified only · never in the loop · waiver to change)

See the FROZEN ledger below for the per‑product detail. Tier‑2 dossiers are the ONLY canonical text for each frozen product.

| Product | Dossier | Dossier status |
|---|---|---|
| WABA approved templates | `WABA_Approved_Templates_v1_S137.md` | **EXISTS → adopt (clean)** |
| Callback Tracker (core) | *to build — as‑built dossier* | TO BUILD (medium) |
| Attendance system | *to build — as‑built dossier* | TO BUILD (medium) |
| Nutrition / Diet HTML | *to build — as‑built card* | TO BUILD (one‑page) |
| Consent HTML | *to build — as‑built card* | TO BUILD (one‑page) |

---

## Part C — FROZEN LEDGER (thin index → lives with the manifest)

*One row per frozen product. The artefact md5 is the live file's hash, computed at freeze — not the dossier's.*

| Product | Dossier file | Artefact location | Artefact md5 | Frozen as of | Waiver rule |
|---|---|---|---|---|---|
| WABA templates | `WABA_Approved_Templates_v1_S137.md` | MyOperator panel (14 approved) | compute at freeze | S___ / D247 | Meta re‑approval + version bump |
| Callback Tracker core | *(dossier TBD)* | Apps Script proj. + `WebApp.gs` (D34‑frozen) + Sheet `1USj…klo0` | compute at freeze | S___ / D247 | explicit waiver (D34) + bump |
| Attendance system | *(dossier TBD)* | live artefact (path/URL to confirm) | compute at freeze | S___ / D247 | explicit waiver + bump |
| Nutrition / Diet HTML | *(card TBD)* | live `.html` (path to confirm) | compute at freeze | S___ / D247 | explicit waiver + bump |
| Consent HTML | *(card TBD)* | live `.html` (path to confirm) | compute at freeze | S___ / D247 | explicit waiver + bump |

---

## Part D — DOSSIER TEMPLATE (fixed shape, so every dossier reads the same)

Each as‑built dossier — heavy or light — uses these six parts and no more:

1. **What it is / does** — plain language.
2. **Where it lives** — file paths, URLs, Sheet/panel IDs.
3. **How it works** — the mechanism, in plain terms.
4. **Decisions & findings that shaped it** — the D/F numbers, one line each.
5. **Known quirks / limits** — what to watch if it's ever reopened.
6. **Freeze note** — frozen as of S___/D247; the waiver rule to change it.

A one‑page **card** is the same six parts, each a line or two. Match the weight to the product — do not over‑document a form.

---

## Part E — WHAT CHANGES IN THE SESSION LOOP

**Before:** read ~12 docs incl. the full 4,300‑line KB at start; rewrite the full KB at end.
**After:** read 2–3 small Tier‑0 docs + verify ~12 hashes at start; at end, rewrite 2–3 small docs and **append one short dated entry** to the Archive. Tier 1 opened only if touched; Tier 2 never.

---

## Part F — ROADMAP (staged; one step at a time, owner confirms each)

- **Step 1 — THIS FILE.** D247 + tiered manifest + frozen ledger + dossier template + build list. *Nothing moved.* ← delivered.
- **Step 2 — the KB split.** Generate **KB Register v2.0** (current‑state) + **KB History Archive v1.0** (verbatim carry of all history). Hash both; prove nothing was dropped. The one big one‑time surgery — done carefully, reviewed before install.
- **Step 3 — build the missing dossiers** from live artefacts, one per turn, spread over sessions: WABA (adopt, 0 work) → Callback Tracker core → Attendance → Nutrition card → Consent card.
- **Step 4 — update the loop docs.** Edit `START_HERE` generator + `END_OF_SESSION_PROMPT_v3` so Phase 0 verifies `CANONICAL_MANIFEST.md` (all tiers) but reads only Tier 0.
- **Ongoing EOS:** append a dated entry to the Archive; update the Register + refresh the manifest hashes. That's the whole close‑out now.

---

## RESOLVED — Callback Tracker freeze scope (confirmed, S147)

Owner confirmed (S147): freeze the **core** — the Sheet + `WebApp.gs` (D34‑frozen) — and write it a proper as‑built dossier. The **Console / Dashboard UI** (`Callconsole.gs`, `Dashboard.html`; v18.28f, one‑tap, D223 gist tile pending) stays an **active Tier‑1 subsystem**, covered by `Call_Console_Evolution_Spec` + `Frontend_Dashboard_Documentation`.

**Tier 2 is now FINAL:** WABA templates (adopt) · Callback Tracker core (dossier to build) · Attendance system (dossier to build) · Nutrition/Diet HTML (card) · Consent HTML (card).

---

**END OF D247 DRAFT — Session 147. Next: Step 2 (the KB split), on your go.**
