# HANDOFF RUNBOOK — Session 67 · v47 · 2026-07-05

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · with: Claude**
**FULL EOS — plan-tool artifacts built (v24, v25); NO live/VPS code touched.** Baseline in:
KB v1.34, Umbrella v1.25, Runbook v46 (S66). Baseline out: **KB v1.36 (CONSOLIDATED), Umbrella
v1.26, Runbook v47 (S67).** **KB wins on any conflict.**

---

## §0 — WHAT HAPPENED THIS SESSION (S67)

Full BUILD session on **Track 1** (hosted plan-tool + vitals). All offline; no VPS.

1. **Locked the two write-file schemas** (`vitals_ledger.csv`, `plan_ledger.csv`) — KB §67.3.
   Vitals append-only, derived values stored in-ledger; plan_ledger references vitals via
   `Vitals_ID_Used` (no duplicated weight). Owner-approved.
2. **Built v24 — offline patient lookup** (`rehab_nutrition_plan_v24.html`, md5
   `8c11be6b235578b5f3979448da8ba8b8`). Load-CSV button, Clinic-ID/mobile lookup → auto-fill +
   dx/comorb pre-fill (editable), shared-mobile pick-list, age shown-not-trusted, vitals manual.
   8-scenario headless test passed. **Owner-approved offline.**
3. **VERIFIED `Patient_UID` origin from a live Docterz export** — it is **Docterz-generated** (not
   tracker-generated as §66 inferred), but a **backend field not shown at the front of Docterz**.
   Corrects the record (D129). Also: Docterz `Vitals` column exists-but-empty; Docterz has DOB +
   precise age (the CSV integer age is a lossy derivation). KB §67.1–§67.2.
4. **Built v25 — embedded vitals section + new-patient path** (`rehab_nutrition_plan_v25.html`, md5
   `92e3c637d0742d3ae1775ab21f871ea1`). Owner's vitals door reuses `compute()` (BMI matches the
   plan), assembles the exact `vitals_ledger` row on screen (write deferred to hosting, decision B).
   New-patient toggle captures Clinic ID + name + mobile only (no UID field), row marked "UID pending
   sync". Headless-tested. **Owner-approved offline.**
5. **Consolidated the KB** — v1.33(full)→v1.34→v1.35 deltas collapsed into **v1.36 self-contained**,
   plus this session's §67 build + D129–D131. (Owner asked for full consolidation this EOS.)

**Decisions:** D129, D130, D131 (KB §67.6).

---

## §1 — STATE (unchanged; no live code touched)

Identical to S64/S65/S66 close — see KB v1.36 §12 verbatim. WABA bridge BUILT+LIVE, sends BLOCKED
vendor-side (D120); `wa_approve` still nohup (not systemd); key rotation overdue; health report /
watchman / attendance / follow-up push all live as before.

**The plan-tool is NOT live** — v25 is an offline Thread-A artifact (not hosted, not committed).

---

## §2 — BACKLOG (what to pick up next)

### Track 1 — hosted plan-tool + vitals (this session's track)
Schemas LOCKED, v24+v25 built & approved offline. Next steps in order:
1. **plan_ledger row assembly in the tool** — mirror the v25 vitals-row preview for the plan choices
   (conditions/comorbidities/diet/sheets printed + `Vitals_ID_Used` pointer). Small offline add → v26.
2. **Host the tool** (Flask + OLS, own private port, key-gated — D121). FIRST confirm on the VPS the
   exact folder the tracker syncs `patient_master.csv` + `patient_diagnosis.csv` to (D122); if not yet
   synced, add that one sync step. OLS forwards the FULL path → Flask answers at its context path.
3. **The real CSV write path** — the single vitals writer (server-side) that appends to
   `vitals_ledger.csv`, computes BMI/category/ratio for every row (D131), assigns `Vitals_ID`.
4. **Staff BP-only page** (D124/D127/D131) — separate hosted tool: measurement fields ONLY, NO calc on
   screen; writes through the same one vitals writer.
5. **New-patient reconciliation job** (D131) — stitch UID-blank rows to the real Docterz UID once the
   tracker ingests them (match on Clinic ID + mobile).

Plan-tool current artifact: **v25** (`rehab_nutrition_plan_v25.html`, md5 `92e3c637d0742d3ae1775ab21f871ea1`).

### STANDING (surfaces every session until done)
- **📘 Living "Clinic Data Map"** (KB §66.6) — one exhaustive research/doc pass of the ENTIRE data
  structure incl. the now-verified Docterz headwater (§67.1), kept updated on every file/column/writer
  change. Canonical alongside the KB.

### Track 2 — live-systems backlog (unchanged, carried from v46)
1. **🔴 WABA authorizer fault (D120)** — Lokesh must fix MyOperator publicapi AWS gateway; blocks ALL
   WABA sends; re-fire TEST when it clears. AWS request-id `eb82db53-47b2-48f1-b744-027a754be56c`.
2. **Make `wa_approve` a systemd service** (`wa-approver.service`) — nohup dies on SSH close; add to watchman.
3. **Rotate `WA_APPROVE_KEY`** + service-account key (Tier A1) + AKEY_14.
4. **Upstream watcher dup bug** — true-identical rows; `inspect_dupes.py`; sender unchanged (D119).
5. `call_transcription.py` GitHub commit; Stage-3 AI verdict layer; clinic_health_report.py UTC→IST fix;
   Orthopedic_Clinic_Rehab_Nutrition_v12.xlsm audit fixes (My_Plan!B31 #NAME? etc.); GitHub commit S59–S64.

---

## §3 — DECISIONS THIS SESSION
D129 (Patient_UID is Docterz-generated, backend-only) · D130 (new-patient: Clinic ID+name+mobile only,
UID blank) · D131 (new-patient reconciliation stitches UID later; staff page no on-screen calc but
writer computes derived fields). Full text KB §67.6.

---

## §4 — DELIVERABLES (downloads; Drive connector write fails → drag-drop)
Docs:
- `Clinic_Master_KB_SystemsRegister_v1_36.md` (CONSOLIDATED, self-contained)
- `Dr_Manoj_Clinic_Umbrella_Architecture_v1_26_Delta.md`
- `HANDOFF_RUNBOOK_2026-07-05_Session67_v47.md` (this file)
- `NEXT_SESSION_OPENER_PlanTool_Continue_v3.md`

Plan-tool artifacts (Thread-A, recoverable, NOT committed to live repo):
- `rehab_nutrition_plan_v24.html` (md5 `8c11be6b235578b5f3979448da8ba8b8`)
- `rehab_nutrition_plan_v25.html` (md5 `92e3c637d0742d3ae1775ab21f871ea1`) — CURRENT
- `v24_test_data/patient_master.csv` + `patient_diagnosis.csv` (SYNTHETIC test data — no real PHI)

ZIPs:
- `COLD_KIT_Session67_<stamp>.zip` — all final docs + artifacts, this + prior sessions.
- `GIT_UPLOAD_Session67_<stamp>.zip` — separate, with commit summary (plan-tool artifacts only,
  IF owner decides to commit — see §5).

---

## §5 — GITHUB NOTE (read before committing)
**Nothing LIVE changed this session** → no *required* live-repo commit. The plan-tool (v24/v25) is an
offline Thread-A artifact; committing it folds it into the live repo, which is a DEPLOY decision.
The GIT_UPLOAD zip is prepared with a suggested path `plan-tool/` and a commit summary SO THAT, if/when
you deploy the tool to the portal, the commit is ready. It also flags the still-outstanding S59–S64
live-code commit as a separate Track-2 backlog item. **Do not push unless you intend to.**

---

## §6 — CANONICAL DOCS AFTER THIS SESSION
- KB: **Clinic_Master_KB_SystemsRegister_v1_36.md** (CONSOLIDATED — supersedes v1.33/34/35)
- Runbook: **HANDOFF_RUNBOOK_2026-07-05_Session67_v47.md** (this file)
- Umbrella: **Dr_Manoj_Clinic_Umbrella_Architecture_v1_26_Delta.md**
- Unchanged: API_QUICK_REFERENCE_CARD, Call_Console_Evolution_Spec v1.5, Diagnostics_Surveillance v1.5,
  Fault_Action_Register v1(S63), Maintenance_SOP_Spec v1.1, Followup_Taxonomy v1(S56).

**Next session:** continue Track 1 (plan_ledger row assembly → hosting) per the v3 opener, OR Track 2
(live backlog) per the canonical START_HERE opener. Keep the two openers separate.
