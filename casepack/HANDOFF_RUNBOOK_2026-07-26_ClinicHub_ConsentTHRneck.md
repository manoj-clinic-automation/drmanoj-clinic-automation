# HANDOFF RUNBOOK — 2026-07-26 — Clinic Hub v1 + Consent THR-neck-femur
*(covers the 2026-07-22 working session; written at close-out 2026-07-26; supersedes runbook 2026-07-21b — Master Doc v1.1 is current truth)*

## §0 What happened

**Consent engine (LOCKED region, opened with approval):**
- New procedure entry **`thrneck` — "THR for fracture neck femur / कूल्हा प्रत्यारोपण — गर्दन फ्रैक्चर"**, born from live case C-2026-000003 (Kamlesh Singh, fracture neck femur, hand-edited consent). Doctor-authored fix-vs-replace opening; **गुल्ले deliberately retained** (patients' dialect); grammar corrected; tokenised. Same body/risks/implant-joint behaviour as elective THR; added to both joint-recognition lists. Elective THR untouched.
- **Phase 1k delivered:** tick-box add-on **`extension` "ऑपरेशन में बदलाव/विस्तार की मंजूरी"** (doctor's exact wording — "मंजूरी (अनुमति)"), prints after risk paragraph, before आयुष्मान clause. Tick-box only (decision D3=ख). Co-exists with old "आपात निर्णय" add-on.
- **Attest trimmed (D4):** inline "हस्ताक्षर: ___ दिनांक/समय: ___" → "हस्ताक्षर व दिनांक/समय नीचे बॉक्स में:". This is the new LOCKED CS_ATTEST text.
- **New live file:** md5 `2d18d1c3873675f48e250275a564f2f4`, 277,641 bytes. Deployed & verified by doctor. 17 structural checks + node --check passed at build.

**Clinic Hub v1 — built & live** at `D:\clinic_hub\`:
- `clinic_hub.html`: 4 cards (Case Pack :5058/case · Follow-up Tracker :5000 · Vitals & Plan :5057/vitals · GMB Review Assist by relative file link), live status dots (no-cors fetch, 5 s poll), new-tab links.
- `open_clinic_hub.bat`: **self-contained** — starts casepack+vitals directly (`start /D` with full folder paths, port checks, .py existence checks, readable errors). Never calls the per-tool bats.
- **Tracker deliberately NOT auto-started** — its own bat's CSV-archiving is a safety ritual (one-upload-per-day discipline).
- Path truth: Case Pack folder = **`D:\casepack tool`** (old bat's header comment `D:\surgical_casepack` is stale; its broken `cd` line worked "by luck" on direct clicks).
- Accepted quirk: hub launch also opens the casepack+vitals self-opened tabs. Fix designed (HUB_LAUNCH env guard) — deferred; needs `casepack_app.py` + `vitals_app.py` uploads.

**GMB Review Assist — inspected, upgrade designed & queued:** variation pools + shuffle button (anti-duplicate; Google review-filter risk flagged honestly), WhatsApp message = draft + **direct long Google review URL** (shortlink rejected — interstitial warning; QR rejected by doctor), catalogue refresh. Blocked on doctor supplying the review URL.

**Incidents:** Claude build container died mid-session; deliverables switched to paste-in-chat; recovered 2026-07-26 and md5 of the preserved casepack file re-verified.

**Addendum at close-out (2026-07-26):** between sessions, the doctor expanded the hub in the *Clinic Systems & Automation* project — 5th card **CC Statements → Tally** (:5059, `D:\Scripts\statements_app.py`, auto-runs daily on hub start) + matching launcher block. Those newer files were already in GitHub; this close-out kit was rebuilt around them (the first-cut kit carried the older 4-card versions and was discarded before any git drop — no regression occurred).

## §1 Mental models to carry forward
- Hub = deliberately dumb: one static page + one launcher; no fourth running app.
- Launcher self-containment: never depend on per-tool bats; check the .py exists before starting; fail loud, never silent.
- `%~dp0` beats hardcoded paths; stale comments in bats are landmines.
- Debug-version-first (bat that stays open and narrates) solved both failures tonight in one round each.
- **Hub = shared surface across projects.** Canonical copy lives in GitHub `clinic-hub/`; either project may extend it, but always starting from the repo copy, and must commit back. Close-outs must ask "has the other project touched shared files?" before cutting kits — today proved why.

## §2 Open backlog
1. Hub tab-quirk fix (needs 2 .py uploads).
2. GMB upgrade pass (needs Google review URL).
3. Repair `open_casepack.bat` + `open_vitals.bat` with `%~dp0`.
4. Termin relabel · Anawin-plain auto-add — pending small decisions.
5. HBP-2022 ingestion (source doc still missing).
6. Phone-file regeneration timing.
7. Doctor 30-sec: desktop shortcut "Clinic Tools".
