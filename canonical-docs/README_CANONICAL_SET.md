# canonical-docs/ — current governing set (post-restructure, D247)

This folder is the GitHub **mirror** of the project's canonical documents. **Live systems and
project knowledge are canonical (D160); this repo is the mirror** — it can lag, and where it
disagrees, project knowledge / the live artefact wins.

> **The single source of truth for *what is canonical and current* is `CANONICAL_MANIFEST.md`** —
> it lists every canonical doc, its tier, and its md5. This README deliberately does **not** name
> document versions, so it cannot go stale on a version bump (the fault that retired the old
> README and START-HERE v4). To know the current set and hashes, read the manifest.

## How the set is organised (D247)

The knowledge base is split into two consolidated single files (neither a delta chain — S100/D202):

- **KB Register** — *current state only*: the systems register, one-line decision + finding
  indexes, current live-file versions + md5s, and the backlog. **Authority on what is true NOW.**
- **KB History Archive** — *append-only*: every `§S###` session narrative and every full decision /
  finding text, verbatim. **Authority on what HAPPENED.** Opened on demand.

Every canonical doc is tagged in the manifest by **tier**:

- **Tier 0 — session loop:** the manifest, the current `START_HERE_SESSION_###`, the KB Register,
  the latest `HANDOFF_RUNBOOK`, and any open incident. Read at the start of every session.
- **Tier 1 — reference:** the KB History Archive, the specs (Umbrella · Call Console Evolution ·
  Diagnostics & Surveillance · Frontend Dashboard · Maintenance-SOP · AI Verdict Layer Master), the
  API quick-reference, the Fault → Action Register, and closed incident reports. Hash-verified every
  session; read only when a task touches them.
- **Tier 2 — frozen products:** one as-built **dossier** per frozen product (`dossiers/`), plus the
  FROZEN ledger in the manifest. Hash-verified only; never edited without an explicit owner waiver
  (D34) + a version bump.

## Layout

- `CANONICAL_MANIFEST.md` — the linchpin (tiers + hashes). Read this first.
- the Tier-0 and Tier-1 docs — flat in this folder.
- `dossiers/` — the Tier-2 frozen-product dossiers.
- `archive/` — every superseded version. When a doc is bumped, its predecessor is moved here
  (standing rule since the S148 trim); git history + the KB History Archive preserve everything.

## Policy

- Canonical docs are **single consolidated files**, never delta chains (S100 / D202, clarified by D247).
- Phase 0 every session: verify **every** manifest row by md5 (all tiers); a mismatch halts work
  until reconciled (D172/D188). A filename is not provenance.

---
*README refreshed at Session 149 to the post-restructure tiered model. It carries no version numbers
by design — the manifest is authoritative for the doc set and hashes.*
