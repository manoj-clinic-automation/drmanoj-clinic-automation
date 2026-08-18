# START HERE — SESSION 136
**Dr. Manoj Agarwal Clinic · continue from Session 135 (11 Jul 2026, FULL EOS)**

## Phase 0 — verify before anything (D172/D188/D201)
Expected md5s of the canonical set in project knowledge (computed at S135 close; verify, don't trust):
run the hash check on each file below and compare to `START_HERE` table printed at S135 close-out
(the definitive table travels in the close-out message and the cold kit's MANIFEST).

Files that MUST be present: KB **v1.61** · Runbook **v73** · Umbrella **v1.47** · Audit **v1.6** ·
`START_HERE_SESSION_136.md` · API Quick-Ref · Call Console Spec v2.0 · Diagnostics Spec v2.1 ·
Maintenance SOP Spec v1.1 · Fault Register v2.1 · Frontend Doc **v2 (S134)** — if Frontend v2 is
absent, the owner still holds the S134 download; request upload, do not reconstruct.
Files that must be ABSENT: KB ≤v1.60, Runbook ≤v72, Umbrella ≤v1.46, Audit ≤v1.5,
START_HERE_134/135, `Clinic_Callback_Tracker__4_.json` and `__5_.json` (superseded — see below).

## Phase 0b — fresh Apps Script export
S135 deployed twice (v18.22 → v18.23) but no post-deploy JSON export exists. Owner: export the
project as `Clinic_Callback_Tracker__6_.json` and upload. Expected inside it:
`Dashboard` `132d62579702b5c651347af97dea2c03` (v18.23) · `Callconsole` `44330498575dc5b46f6ed623445d05c2` ·
`OutcomeLog` `9fc4c941bc067a40ce43eb40e8e81376` · `Main` `1a85166c…` · `WebApp` `5173c3c7…` · `Health` `9461d01b…`.
Any drift = someone edited the editor since S135; stop and reconcile.

## Phase 0c — VPS ritual
`bash /root/wa/rotate_callhook.sh status` (CALLHOOK steps 3–4 still open; Lokesh).

## Phase 1 — where we are
Read Runbook v73 §0–§2. Live state: dashboard v18.23; F-34/F-35 closed and live-verified;
processor hardened (D210); visit ledger 829 rows clean; mirror one-row-per-UID (7,407).

## Phase 2 — the queued work (owner picks)
- **Recommended: Block C** — one clock + quota load (F-13/F-5 + F-6/F-12; D185 orders it before Block D).
- **Or: clinical-data-report migration build** — plan in KB §S135.6; needs owner's yes/no on the
  follow-up-column cross-check first.
- Standing: F-0 decision sheet · D205 inputs · service-account key rotation (chronic, Tier-A1).

**Next free: D211 · F-36. Session counter: this file's session is 136; it advances only on a completed EOS.**
