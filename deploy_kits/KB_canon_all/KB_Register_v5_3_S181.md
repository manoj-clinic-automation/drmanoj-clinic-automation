# KB REGISTER — v5.3 (Tier 0 · current state · rides the session loop) — S181 clinic module LIVE + the deploy chain

**Dr. Manoj Agarwal Clinic · Bareilly · created S147 (D247). Replaces the monolithic KB v1.72 in the session loop; the Register is the authority on what is true NOW.**

> **How to use.** *Now* → this file. *History* → **KB History Archive v1.28** (Tier 1). *Live backlog* → **HANDOFF_RUNBOOK §2** (v114). *Findings register* → **Fault_Action_Register v2.17** (Tier 1; ALL THREE owed appends APPLIED at S181 — F-82…F-89 now in the register itself, full text §7.1; the append artefacts are provenance only). *Doc manifest + hashes* → **CANONICAL_MANIFEST.md**.

---

> **v5.3 — S181 (the CLINIC module LIVE — built, redesigned and installed via the NEW one-command deploy chain; the three housekeeping debts cleared).** Additive: the clinic-finance live entries below updated (finance_app v5 builds in one session, final `86382f62…`; clinic entry UI `0c64fda2…`; two migrations applied; three new tables), **D317–D319** join the decisions index, **F-90–F-95** the findings index, Fault Register **v2.17** and Asset Register **v1.11.0-R** become the CURRENT Tier-1 rows, and a v5.3 lineage row is added. Nothing in v5.2 cut. Full narrative: **Archive §S181** (the longest section in the Archive). Parallel run: the clinic Google Form CONTINUES until clinic runs clean (D313). Next free: **D320 · F-96 · Session 182**.

> **v5.2 — S180 (the Marg pharmacy feed built offline end-to-end; sale returns made to reach the books; FOUR live installs).** `finance_ingest.py` and `finance_app.py` were both replaced, four new modules landed at `/root/finance/`, and the database gained one redefined view and one new table. This bump is **additive**: the six live-file entries below are updated or added, **D314** and **D315** join the decisions index, **F-85…F-88** join the findings index, and a v5.2 row joins the lineage. Nothing in v5.1 was cut. Full narrative: **Archive §S180**. Sole live-state reference for the finance subsystem remains `S179_Finance_LIVE_State` (Tier-1) — **now partly superseded on md5s by the table below, which wins**. Next free: **D317 · F-90 · Session 181**.

> **THE SEVEN UNREACHABLE ROWS WERE RESOLVED AT THE S180 CLOSE — FOUR RECOVERED, THREE LOST (D316, F-89).** A hash-based recovery tool searched the owner's `D:` and `C:` drives (by md5, not filename — D188 — and inside `.zip` archives; 26,745 files hashed). **Recovered, each matching its pinned md5:** `Fault_Action_Register` **v2.16** (Tier-1 CURRENT, from the S171 cold kit) · `Staff_Daily_Register_Dossier` v1.1 · `KB_Asset_Register` v1.10.3 · `KB_Register` v4.6. **Not found and declared LOST:** `KB_Asset_Register` **v1.11.0** (Tier-1 CURRENT) · `KB_Register` v5.0 · `KB_History_Archive` v1.26. All three are S177–S178 outputs, created **nine sessions after the last cold kit (S171)** — see F-89. Closed under **D316**: v5.0 and v1.26 as **LOST-SUPERSEDED** (v5.1 and v1.27 are verified present on disk, nothing current depends on them, no action); `KB_Asset_Register` v1.11.0 as **LOST-RECONSTRUCTABLE** — rebuild it from the recovered v1.10.3 plus Archive §S173–§S177. **A closed row does not halt Phase 0.**

---

> **v5.1 — S179 (one new live VPS subsystem: clinic-finance).** The Sanjeevni (medical) daily-revenue system was migrated off Google Forms onto the VPS — a new `clinic-finance` app, live and bank-reconciled, 121 legacy days imported as-recorded. This bump is **additive**: the finance live-file block was added to the table below, **D313** (finance subsystem architecture) to the decisions index, **F-84** (three self-found security faults + the offline-testing-shortcut lesson) to the findings index, and a v5.1 row to the lineage. Nothing in v5.0 was cut. Sole live-state reference: `S179_Finance_LIVE_State` (Tier-1). Full narrative: **Archive §S179**. Next session = clinic + lab modules (a replication of medical). Next free: **D314 · F-85 · Session 180**.

> **v5.0 — S178 COMPACTION (D247 re-applied; NO live code, NO Archive change).** The Register had drifted back toward a monolith: session history was duplicated in **three** overlapping forms — per-session *"S… additions"* blocks, a full prose *CHANGELOG*, and a *"§S… STATE"* tail. All three are **removed here with zero loss of context**, because every one of those session narratives is held **verbatim in the KB History Archive**, which is untouched. What the Register keeps is only **current state + indexes**: one consolidated live-file table (below), the current-state sections (§12/§12A · surveillance · parked · backlog), the **complete decisions index now through D313**, the findings index, and a compact **version-lineage** table. **Nothing that lived only in the Register was cut** — decisions D283–D312 (previously only inside the narrative blocks) were folded into the index, and every current live-file md5 was folded into the table below. Session narratives → **Archive §S…** · historical Register md5s → **CANONICAL_MANIFEST §S… blocks** · asset-app A-D1–A-D24 → **KB_Asset_Register** + Archive §S173–§S177.

## CURRENT LIVE FILE VERSIONS — CONSOLIDATED (the single source; "live as of" = the authoritative session block in the Archive)

> Replaces the old §S146-lifted header and the per-session live-file lines scattered through the removed "additions" blocks. Each md5 is the **latest** for that file; `§12A` below remains the fuller authority for the call-hook family. VPS python for `/root/wa`-context scripts = `/root/wa/venv/bin/python3`; the **asset app and the finance app use system `python3`** (F-53).

**Portal · console · gist (VPS `/root/portal/` + `/root/wa/`):**
| File | md5 | live as of |
|---|---|---|
| `/root/portal/portal.py` | `da4177091ba9f188be6a0ff3eaf25bd8` | S176 — SSO broker + console-v3 + casepack/WA/follow-up tiles + Scan-Purchase tile (finance tiles added S179 — see finance note) |
| `/root/portal/casepack_portal.py` | `341404d7e6d054b4c49fae09d59ea13b` | S172 — in-portal Surgical Case Pack (D309) |
| `/root/portal/portal_wa.py` | `34994b235c95a7c611996738ab14bdd1` | S172 — the ONE canonical WhatsApp sender (D310); DRYRUN default (F-82 vendor block) |
| `/root/portal/portal_followups.py` | `98547bc41869360bf224b190fc27cc5d` | S172 — follow-up batch (D311) |
| `/root/portal/clinic_sso.py` | `2bc6ba15e52512d3f866536e758079ed` | S158 — HMAC SSO token/cookie |
| `/root/portal/clinic_users.py` | `2e85a7c85d047d400b0417e7aca9f3b7` | S158 — PBKDF2 user store |
| `/root/wa/portal_console.py` | `552135b53564491dfe5629b2311b2076` | S171 — `console.db` builder (sole writer); cron `*/10 9–21` (D303) |
| `/root/wa/portal_gist.py` | `55e111d71e95032c21234ae540a49431` | S165 — gist builder (sole writer `portal_gist.json`) |
| `/root/wa/daily_digest.py` | `8140f54310bc19c238e9cf11f34b21e7` | S171 — 21:30 digest, reads `console.db` (Track G) |

**Clinic Finance (VPS `/root/finance/`, system `python3` — F-53; SSO-gated at `followup.dr-manoj.in/finance/`; D313 · F-84):**
| File | md5 | live as of |
|---|---|---|
| `/root/finance/finance_app.py` | `86382f62907b65cf17fded2ee914328e` | **S181** — the CLINIC unit added and redesigned in one session (kits S182_C1a…C2a, anticipatory labels — F-85 note): English four-tender entry (cash/upi/card/razorpay), strays with narration, drawer expenses, two-stage approval (verify → final, `clinic.final_checker`), tracker-day panel + token-gated feed. Live smoke **316/316 on the real store**. (S180 build `7b62b7ae…` retired; rollback pairs `.bak_S182`/`.bak_S182C2` on the box) |
| `/root/finance/finance_ui/finance_entry_clinic.html` | `0c64fda2005ea3cd6692aeb8fd3dc728` | **S181 NEW** — "Clinic Entry Form", simple English, four tenders, extra-collection + expenses repeaters, tracker card, register-pages uploads |
| migrations `S182_clinic` + `S182_c2` | `bd2bb0ee5c58ac694ff1f741d70fee98` · `22c67f25b17e39faaaf66376df10c373` | **S181 APPLIED** (markers set). attachment table REBUILT once (C1, knowingly); everything else additive: tables `clinic_verification` · `clinic_line_side` (razorpay rides beside day_line's mode CHECK) · `tracker_day`; clinic roles seeded REAL: makers shavez/alisha/shivani (+shavez checker for verify), checkers manoj/bhawna |
| `gas/VPS_Push_TrackerDay.gs` | `4e5c5b97d945fb63f8807bef54251be1` | **S181 delivered, NOT yet wired** — clinic Gmail GAS, daily tracker-day push (ids+amounts only; endpoint refuses names/phones) |
| `docterz_report.py` (PC-side, tracker) | `783fffde7607df9454b4015bd14b6fa3` | **S181 delivered, NOT yet integrated** — reads BOTH Docterz export variants, all 7 tender tokens, footer-asserted; recovers the dropped split legs (selftest 22/22; both real exports parse clean) |
| `/root/finance/finance_ingest.py` | `2cd0f264fb1a091f3e3ec7c3f4a17438` | **S180** — the `amount <= 0` junk filter no longer eats credit notes: zero/unreadable stays junk, a negative is a RETURN (D314). Selftest **50/50** |
| `/root/finance/marg_report.py` | `28b47d447cfd966411742055717a5c56` | **S180 NEW** — reads the Marg `.xls`; refuses the 3-column variant, a truncated export, or a day failing its own arithmetic; emits bill rows + drug rows; phone masked to last-4 (selftest 64/64 offline, 38/38 on the box) |
| `/root/finance/finance_returns.py` | `a46a87e65d951d59baeb9d86c9d8fe59` | **S180 NEW** — traces a credit note to its sale by patient, corroborated by the medicines returned; graded verdicts; expiry + 30-day flags; never refuses a return (selftest 28/28) |
| `/root/finance/finance_returns.sql` | `9cec4e317590f845beda87881721cf69` | **S180 NEW** — additive: table `sale_line_item` + 4 indexes + 3 `returns.*` settings |
| `/root/finance/finance_identity.py` | `81092e3ca18c9a85f1de06cc8055d967` | **S180 NEW** — proposes a patient for name-only lines from the accumulated roster; five grades; **proposes, never assigns** (selftest 44/44) |
| `/root/finance/finance_import_medical.py` | `7cfde93e1c18a030a031a60ff66795f6` | S179 — one-shot legacy importer (121 days; importer 12/12) |
| `/root/finance/finance_upi.py` | `3f5016f0c64f12b91ab55c18252705c1` | S179 — ICICI MPR `.xlsx` parser + reconciler; bank arbiter (selftest 14/14) |
| `/root/finance/finance_schema.sql` | `bef0d8100a1d7da30d049a9cd8eaf365` | S179 — INTEGER PAISE; computed opening/closing via views |
| `/root/finance/finance_ui/finance_entry.html` | `8ec6ad494fd6b97e5c7c70b6c42fdfc5` | S179 — maker "Daily Sale" (English) |
| `/root/finance/finance_ui/finance_review.html` | `ddd3d5f61fb2f41950b1a63aa3480650` | S179 — checker (KPIs, month grid, close, parked, day list, UPI approve-ack) |
| `/root/finance/finance_backup.sh` | `efe6f1b527bffafc21062bc352a063ee` | S179 — nightly verified backups (30 daily + 12 monthly) |
| `clinic-finance.service` | `59c03bfafc2cd63bc440053724b61c34` | S179 — systemd unit (port 8106; FINANCE_ALLOW_HEADER_AUTH deliberately absent) |
| clinic-Gmail GAS `VPS_Push_UPI.gs` | `955b291c99edd0f16c79836e54a1043d` | S179 — pushes daily ICICI MPR to the VPS at 09:30 (`{"ok":true,"pushed":8}`) |

*S180 database changes (live, additive/non-destructive): view `v_day_attribution` **redefined** so a `*_return` service subtracts from `attributed_p`; table **`sale_line_item`** + 4 indexes + 3 `returns.*` settings added. No table altered or rebuilt, no row read/written/deleted. VPS python gained **`xlrd 2.0.2`** (system `python3`). Rollback SQL for the view sits at the foot of `finance_migration_S180_returns.sql`; the table drops cleanly (nothing references it). Backups on the box: `finance.db.bak_20260815_203810` · `…_211437` · `…_221320` · `finance_ingest.py.bak_20260815_203810` · `finance_app.py.bak_20260815_221320`.*

*Dev-only, NOT installed: `dev_seed_smoke_db.py` builds a database satisfying `finance_app.py --selftest`'s preconditions (>100 filed days, approved/locked days, open exceptions, negative legacy cash tail, a bank deposit). **Its absence is what caused F-87.** Keep it.*

*PHI/data (NOT in repo or manifest — F-31/F-49): `finance.db*`, `scans/`, `exports/`, `medical_*.csv`, `access.log`. `FINANCE_CRON_TOKEN` lives only in the unit + GAS Script Properties. Merchant IDs: `…312505` Sanjeevni · `…306941` clinic · `…319164` NK Pathology.*

**Call-hook · verdict family (VPS `/root/wa/`; §12A is the fuller authority):**
| File | md5 | live as of |
|---|---|---|
| `/root/wa/call_hook_capture.py` | `beafccafbf7e81aa5f2736be939b2bbb` | S126 — v2 dual-key receiver |
| `/root/wa/flag_investigator.py` | `a9baa6ca22055bb188d5c65b93c47ba1` | S145 |
| `/root/wa/call_verdict.py` | `539ea68fb4ce99f0029fdbb53bbf8ebe` | S141 — v2.1 |
| `/root/wa/verdict_review.py` | `280eb2cef9295d89f30c7b84d4c94adb` | S143 — *superseded by the console referee (D297); retained* |
| `/root/wa/call_pipeline_worker.py` | `3c8be7f0f6f5960103fb1ed586c48cce` | S140 |
| `/root/wa/callhook_write_probe.py` | `705bd4a1d82068b1ccc74a2567e2ac67` | — |
| `/root/wa/make_force_keys.py` | `9b44831a0a2a2003fac5c4901f7da35c` | S143 |

**Salary · attendance · register:**
| File | md5 | live as of |
|---|---|---|
| `/root/staff_register/staff_register.py` | `cef768594bee5360a388e66028456495` | S164 |
| `/root/staff_register/salary_engine.py` | `5514918067243e3f39e7074144ee7db4` | S164 — standalone register salary (D289) |
| `/root/staff_ledger.py` | `92665b64f015fee9302ac3da6100f5c8` | S162/S164 — money-book after D288 |
| `/root/att_month_report.py` (v2.5) | `e64cad19d135618dec1413553e6bdc80` | S154 — additive report layer over the frozen att core |
| `/root/wa/clinic_watchdog.py` | `01ca6591a74ec8009bf9748fb7f480c2` | S156 — 11 services |

**Asset Register (VPS `/root/assetapp/`, system `python3` — F-53):**
| File | md5 | live as of |
|---|---|---|
| `/root/assetapp/asset_register.py` (v1.11.0) | `0cd8fc3bfe8d39322c6162a41124bddf` | S177 |
| `/root/assetapp/smoke_test.py` | `6e72373325f808b1d7eaeb99f51a7b14` | S177 — 342/0 |
| `/root/assetapp/scanner_widget.js` | `4fe8c89386a54ce90786823b53df55bc` | S175 — unchanged since v1.8.1 |
| `/root/shared/sarvam_ocr.py` | `b1cc567b70b5e67c8c021fa22590babf` | S175 — shared OCR module |

**Tier-2 frozen — live state (waiver to change; D34/D247):**
- `clinic_writer` `vitals_page.html` **v28** `fcedae303b620f3e5199f4b1e4766510` (live on `D:\clinic_writer\`, waiver D248/S150); folder digest `1b4f0f2299cd6c9e72b6d04f45847556` (S155). Engine/app/ledger schemas byte-unchanged.

## §12 STATE — what is live right now (UNCHANGED since Session 64 close)

**Nothing in §12 changed at Sessions 65–67 (no live code touched in any of them).** The live picture
from v1.32 stands verbatim:

- **WABA FOLLOW-UP BRIDGE — BUILT + LIVE on VPS, but SENDS BLOCKED vendor-side (D116–D120).**
  Three components in `/root/wa/`: `plan_followups_from_xlsx.py` (dry-run planner, LIVE),
  `wa_approve.py` (approve/deselect page, 127.0.0.1:8101 via OLS `/wa-approve`, **hand-run via
  nohup — NOT yet a systemd service**), `waba.py` (template sender, copied to VPS, unchanged).
  Safety = 2 open-gates (secret key in URL + TEST-mode default) + 2 live-send gates (LIVE toggle +
  daily-cap). Config in `/root/wa/wa_approve.env`; send creds in `/root/wa/.env`.
- **🔴 WABA SENDS BLOCKED — MyOperator-side AWS API Gateway fault (D120).** Send + templates-LIST
  GET both return HTTP 500 `x-amzn-ErrorType: AuthorizerConfigurationException`. Vendor-side, not
  ours (500 not 401/403; no-payload GET fails identically). Lokesh must fix the publicapi gateway
  authorizer. Fault code `WABA_SEND_AUTHORIZER_500` (ESCALATE-ONLY, vendor). AWS request-id on file:
  `eb82db53-47b2-48f1-b744-027a754be56c`.
- **Everything else from v1.31 §12 stands verbatim** — daily health report LIVE 08:00 IST;
  timer-freshness checker built+tested but STILL NOT armed; S61 watchman LIVE; stale-list sentinel
  LIVE; follow-up push VPS-native; attendance live; Dashboard v18.18; caller-ID SOP D93; duration
  gate D82; key rotation 🔴 overdue; AKEY_14; PHI base swap deferred.

**Known open (live-systems backlog, Track 2) — unchanged, restated:**
1. **🔴 WABA authorizer fault (D120)** — Lokesh; blocks ALL WABA sends; re-fire TEST when it clears.
2. **Make `wa_approve` a systemd service** — nohup dies on SSH close.
3. **Rotate `WA_APPROVE_KEY`** + service-account key (Tier A1) + AKEY_14.
4. **Upstream watcher dup bug** (clinic-PC) — 6 true-identical rows; diagnostic `inspect_dupes.py`.
5. Arm timer-freshness checker; maintenance jobs; "Agent shows as Staff" close; GitHub commit
   (S59–S64); data pass; P1–P10.
6. `call_transcription.py` GitHub commit; Stage-3 AI verdict layer; clinic_health_report.py UTC→IST
   fix; Orthopedic_Clinic_Rehab_Nutrition_v12.xlsm audit fixes (My_Plan!B31 #NAME? etc.).

---



## §12A CURRENT LIVE STATE — call-hook family (Sessions 125–127)

**`§12` above is a historical artefact.** Its own heading says *"UNCHANGED since Session 64 close"* and it has been true to that. It is preserved verbatim, not rewritten. Where §12 and §12A disagree about the call-hook family, **§12A wins.** (D175.)

**`call-hook.service` — LIVE.** `call_hook_capture.py` **v2 (dual-key)**. File on disk replaced 08-Jul **21:55**: 31,490 bytes, 701 lines, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43 selftest on the installed file. **Loaded into a running worker for the first time at 08-Jul 23:38:00** (rotation step 1) — until then the worker executed the pre-21:55 bytes, imported at 14:49:13. gunicorn `-w 1`, no `--preload`, `127.0.0.1:8098`. Gate accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, constant-time; refusals written to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** they are refused. Rollback: two byte-identical v2 copies, `call_hook_capture.py.bak_20260708_144241` and `.LIVE_v2_s126_20260708_212453` (both 30,749 bytes). v1 is not on the box; it lives in GitHub and the cold kit.

**`CALLHOOK_SECRET` rotation — STEPS 1 AND 2 COMPLETE. STEPS 3 AND 4 PARKED (S128, D176).**
> **PARKED means: not abandoned, not pending, and not to be raised at session start.** The dual-key gate (D162) permits the panel and the VPS to disagree indefinitely. Nothing degrades with time. See §S128 for the stated bound of the exposure. Resume only when the owner asks.
- **Step 1** ✅ 08-Jul 23:38:00. `CALLHOOK_SECRET_PREV` set equal to `CALLHOOK_SECRET`. Startup: `previous=SAME AS CURRENT (rotation not started; harmless)`. Verified across nine hours and 48 real calls, zero refusals, zero PREV-key acceptances (both variables identical, so `CALLHOOK_SECRET` matched first every time).
- **Step 2** ✅ 09-Jul 09:05:58. New key generated **on the VPS** (`openssl rand -hex 12` → 24 hex chars, no `@`, nothing that percent-encodes — the D165 encoding trap removed at source). Installed via `rotate_callhook.sh install`. Startup: `current=key_ea20dd  previous=key_db8972  -> ROTATION IN PROGRESS`. **Verified on live traffic at 09:35:** 64 calls accepted today, **12 on the previous key in 30 minutes**, `refused today: none`. This is the first production exercise of the previous-key branch (D174).
- **Step 3** ⏸️ **PARKED 09-Jul-2026 (S128).** The MyOperator panel still sends the old key `key_db8972`, and that is a stable, safe, indefinite state. When resumed it requires a clinic day with hours in front of it: update the panel, place one real call, confirm `on PREVIOUS key/30min` falls to `0` and `refused today: none` — **then re-check ≥1 hour later on the same clinic day.** An incident is closed by a successful re-test, not a successful test. **When resumed, a THIRD key must be generated** — `key_ea20dd` was exposed in a chat transcript at S128 open (D176) and must not be pasted into the panel.
- **Step 4** ⏸️ **PARKED, AND BLOCKED ON STEP 3 REGARDLESS.** Clearing `CALLHOOK_SECRET_PREV` while the panel holds the old key reconstructs the 06-Jul outage by hand. The command is deliberately absent from `rotate_callhook.sh`, from this KB, and from the runbook. See **D173**.

**BOTH keys are now live and both are exposed in chat transcripts.** `key_db8972` (12-char, `@`) since S94–S125; `key_ea20dd` (24-char hex) since S128 open, when Runbook v61 §5 instructed the owner to `grep` it to his terminal (**D176**). Neither dies before step 4. **The exposure is bounded, not urgent** — see §S128 for what the secret can and cannot do. Steps 1 and 2 bought exactly this: an exposure that is *unhurried* rather than *unfixable without an outage*.

**`rotate_callhook.sh` — NEW, on the VPS at `/root/wa/rotate_callhook.sh`.** Four subcommands: `status` (read-only), `stage` (builds `.env.candidate_s127`, eleven guards, self-deletes on any failure, never touches `.env`), `install` (re-runs guards, `cmp`-validates the rollback point *at the instant before* the atomic `mv`, swaps, clears bytecode, restarts, reads back the startup line), `rollback`. Keys appear only as `key_<md5[:6]>` labels. Built because a human reading forty exit codes is the bottleneck and the hazard. See **D171**.

**Known cosmetic defect in `rotate_callhook.sh` v1.0:** `status` looks back only two minutes for the startup line, so it prints a blank unless a restart has just happened. Harmless in `install`; misleading in `status`. Fix in the next session that touches the script — a blank that looks like a fault is the thing this project exists to eliminate.

**Rejected-at-the-door (Diagnostics Category 5) — IMPLEMENTED** in the receiver (D163), live 08-Jul 14:49. **`callhook_watchdog.py` v1.0 — BUILT**, on the VPS, manual runs only. **Two defects, both open:** (a) no coverage guard — a date the access log does not span reads as zero traffic and reports CRITICAL *"MyOperator is not delivering at all"*, a confident wrong diagnosis pointing away from the real cause; (b) `mask_key()` does not `unquote()` before hashing, so labels do not compare across sources (D165). **Not scheduled**: it exits 1 on WARN, so a naive `OnFailure` fires all day on already-fixed 403s.

**`ANTHROPIC_API_KEY len=111` sits unaccounted in `/root/wa/.env`**, loaded into the environment of a gunicorn worker that has no use for it. Added inside the outage window; recorded nowhere; nobody has identified what wrote it. Confirmed still present at S127 close. **Rotate it, find out what wrote it, and move it out of the call-hook worker's `.env`.** An unknown secret in a live process's environment is a fault whether or not it has caused one yet (D169).

---


---

## SURVEILLANCE REGISTER — unchanged since Session 64

No surveillance rows changed at S65–S67 (no live component added). The v1.32 register stands verbatim,
including the WABA-send fault row (`WABA_SEND_AUTHORIZER_500`, CRITICAL·ESCALATE-ONLY) and the
wa_approve "not yet service-monitored" note.

*(Forward-looking: when the hosted plan-tool + vitals tool become live services, each gets its own
surveillance row — liveness on its port/service, plus a freshness/disk check for the `plan_archive/`
PDF store (D132) and the two ledgers. The **finance app** is a live service as of S179 — a
surveillance row (liveness on `clinic-finance.service` / port 8106; `healthz` `sso_epoch_ok`;
`finance.db` backup freshness) is owed when the surveillance register is next rebuilt.)*

---

### Surveillance forward-notes folded from later sessions
*(These are forward-looking notes recorded in the deltas; no surveillance ROW is live yet for
these Track-1 tools. Kept here so the register stays complete.)*

**From v1.39 (S75):** When the Step-5 front-end goes live on the PC it becomes a local service
— at that point add a liveness/freshness row (local app up; ledgers + `plan_archive/` writable
+ syncing). *(Step 5 is now COMPLETE per §93, but as a PC-local offline app, not a monitored
live service; no VPS surveillance row applies.)*

---


---

## PARKED ITEMS REGISTER (new, S128)

Items placed here are **decided, safe, and closed to session-start review.** They are not backlog. They are re-opened only when the owner asks, by name.

| Item | Parked | State | Bound / why parking is safe |
|---|---|---|---|
| `CALLHOOK_SECRET` rotation steps 3 & 4 | 09-Jul-2026, S128 | Steps 1–2 complete; dual-key gate live | Both keys accepted, `refused today: none`, no clock. Exposure is data-integrity on `Call_Feed` only — no patient-data read, no call placement, no panel access. Resume needs a clinic morning **and a third key** (D176). |
| `setDashboardKey` / `setStaffKey` closure (F-9) | 09-Jul-2026, S129 | ⚠️ **ORDERED LAST, NOT SILENCED** | Owner directive: assess blast radius before touching `WebApp.gs` (D34). **This is not a safe item and must NOT be closed to session-start review.** It is ordered last because the fix requires suspending D34, not because the risk is low. Bound: exploitation needs the `/exec` URL *and* the function name. The names are absent from the served page but present in the GitHub repo — **repo visibility is `UNKNOWN` and must be confirmed (Block A-0).** `removeTriggers` / `removeHealthTrigger`, the loudest of the group, close in Block A and need no D34 waiver. |


---

## OPEN BACKLOG SNAPSHOT (as of S94 close — see Runbook for the live list)

**Six-item forward agenda (owner-set S94, recommended order):** (0) console `isGenericAgent_`
fix — DONE. (1) Duplicate patient entries in a day — PC-side de-dupe, SAFE, next execution item.
(2) Reconcile "didn't pick up but visited" — auto-settle on a real Docterz visit; overlaps
Track-1 Step 7. (3) Trim the >200 staff list — **DONE (S121, D148: cap 120 + Hard-to-Reach split).** (4) Live staff-activity summary on doctor dashboard — audited half
depends on item 5. (5) AI audit layer (Stage 3, D62) — **BUILT + PROVEN S122–S123 (D149–D153); next = nightly timer + Verdict Analysis Layer D154.**
(6) Historical taxonomy insights — analysis only, blocked on a de-identified export.

**Track-2 live backlog:** WABA authorizer fault (D120, Lokesh, blocks all sends) · make
`wa_approve` a systemd service · rotate `WA_APPROVE_KEY` + service-account key + AKEY_14 · arm
timer-freshness checker + maintenance jobs · `clinic_health_report.py` UTC→IST fix · courtesy
rotate `CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` (D145) · consider a `CALLHOOK_SECRET_MISMATCH_403`
detector (panel Failed OR no daily raw-log by mid-morning).

**Track-1 backlog:** Step 7
new-patient reconciliation (dovetails with agenda item 2) · living Clinic Data Map (§66.6). *(Hindi-spelling tidy in `vitals_page.html` LIB — DONE S150 under waiver D248.)*


---


> **NOTE (S147):** the snapshot above is historical (as of S94). The **live backlog is HANDOFF_RUNBOOK §2**.

---

## DECISIONS INDEX — CONSOLIDATED (D121–D175)

**Track-1 additions (D121–D134), from v1.38 base:**
- **D121** Host plan-tool as walled-off Flask+OLS VPS portal tool, key-gated. *(AMENDED by D136 — tool is PC-local, not VPS.)*
- **D122** Canonical CSV rule: newest-by-date from one fixed folder; never a Drive file-id. *(RESOLVED by D136 — clinic-PC local `data/` folder.)*
- **D123** Shared mobile → pick-list; age shown not trusted.
- **D124** Two faces: owner full version + staff BP-only version. *(Staff-page portion RETIRED by D135.)*
- **D125** Pre-fill dx/comorb; review & correct; often empty by design.
- **D126** Plan-tool never writes source; choices persist to plan_ledger.
- **D127** One vitals_ledger, one writer, two front doors; tool reads vitals back. *(Now one front door — doctor — after D135.)*
- **D128** Patient_UID = backend join/storage key; Clinic_Specific_Id = human handle.
- **D129** Patient_UID is Docterz-generated (verified); backend field, not shown at front.
- **D130** New-patient path: Clinic ID + name + mobile only; UID blank + "pending sync".
- **D131** New-patient reconciliation: stitch UID later on Clinic ID + mobile (hosted/Step-7 job).
- **D132** Archive both printout PDFs, patient-tagged (`plan_archive/<year>/<Patient_UID>/…`); new-patient PDFs → `pending/` bucket, stitched on reconciliation; ~100 MB/yr; generated server-side at hosting.
- **D133** Ledger + PDF storage home = VPS canonical; Drive mirror deferred. *(AMENDED by D137 — storage home is the clinic PC.)*
- **D134** `plan_ledger` schema +2 PDF-path columns (`Plan_PDF_Patient`, `Plan_PDF_Physio`); new 14-col order.

**Track-1 write-path (D135–D138), from v1.39 (S75):**
- **D135** Staff BP-only page retired (doctor-only vitals entry).
- **D136** Track-1 write-path PC-local; clinic-PC `data/` CSVs canonical (amends D121, resolves D122).
- **D137** PDF/ledger storage home = clinic PC → Drive sync (amends D133; structure unchanged).
- **D138** PDF engine = reportlab (pure-Python text-faithful archive).

**Track-1 front-end (D139–D142), from v1.40 (S93):**
- **D139** Front-end is its own auto-launched Flask app importing clinic_writer, separate from the live tracker; shared menu page; double-click `.bat` launch. Ports 5000 (tracker) / 5057 (vitals) never clash.
- **D140** Whole tool + engine + ledgers + archive live on **D:** (survives a Windows reformat; Drive sync is the real off-machine backup). Source CSVs stay on C:, read across drives.
- **D141** Diagnosis pre-fill mapped from `Orthopedic_Diagnosis_Taxonomy_Master.xlsx` (27 canonical categories): 12 auto-fill a rehab button, 15 blank-by-design; unmapped → "pick the exercise set", never a silent Knee-OA default.
- **D142** Bilingual archive PDF via per-run font switching (Helvetica English / NotoSansDevanagari Devanagari, engine `_mixed()`); physio PDF built from `sheetBlocks()` not screen-scraping; graceful font fallback; reportlab stays.

**Track-2 live fixes (D143–D145), from v1.41 (S94):**
- **D143** `isGenericAgent_` helper added to `OutcomeLog.gs` (generic = staff / doctor / unknown / agent / system / blank) so the Today outcome view can borrow the real caller name from the matched call when the outcome was filed under a generic label. Full-file replacement; node-check verified; deployed as New version (URL stable).
- **D144** Call-hook secret standard: the `?key=` gate for `/mo-callhook` (and similar self-chosen VPS webhook gates) shall be **plain alphanumeric, no special characters** — special chars corrupt under URL transport and caused the S94 403 outage. Applies to future rotations of these gates.
- **D145** (hygiene note) Courtesy rotation of `CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` advisable at a convenient time (self-chosen VPS gate keys, NOT WABA/MyOperator tokens; low-risk; no Lokesh coordination needed).
- **D146** Staff call-sheet de-duplication in `build_staff_call_workbook` (`processor.py`): one row per patient (group mobile+name+diagnosis, keep latest `Due_Date`, older cycles hidden no-note, reinstated rows win, blank-mobile→name-only, fail-safe fallback). Staff sheet only; audit workbook untouched. Verified 07-Jul (236→214). See §102.
- **D147** Two-file-type rule + Drive-sync direction (VERIFIED-NORMAL): `consultation_report_YYYY-MM-DD.csv` = daily raw inputs, many-and-dated by design; `visit_ledger.csv` = single cumulative ledger, never dated, one fixed path. `data\` folder Drive-synced (PC writes → Drive mirrors); settle freshness depends on sync. No code. See §107.
- **D148** Staff call-sheet cap + Hard-to-Reach split in `build_staff_call_workbook` (`processor.py`): (A) `Call_Attempts ≥ 3` + no contact → Hard-to-Reach tab (name·Clinic ID·mobile·diagnosis·last-visit·attempts; reinstated exempt) for doctor keep/archive; (B) cap **120** total — winnable first, oldest-dropout drip fills leftover room, winnable overflow rolls to tomorrow; fail-safe fallback; audit untouched. Amends D146 (reinstated wins *among rows surviving settle + 3-strike*). Verified 07-Jul (cap 120, drip 10, HTR 0). See §121.
- **D149** Stage-3 AI judge (`call_verdict.py`) — the transcript-only verdict layer (parent D62). Claude Haiku, ALL calls both directions, BLIND (transcript+direction+duration only; never the staff claim or any patient/agent identifier); answers in the LIVE dashboard vocabularies (11 FU codes / incoming lists) + UNCLEAR; six mandatory-review flags (postop·complaint·urgent·surgery·clinical·conduct); evidence excerpt per verdict; three-field record (staff/AI/doctor-final) version-stamped; writes its OWN `Call_Verdicts` tab in the doctor-only Call Audit sheet; calibration-first (no auto-accept, no actions in v1); diarisation deferred (owner "a"). Built + installed + proven (md5 `bb17720d4857e3c040e8c89e7cc2e095`, selftest 24/24, first real run 15/15). Claim-match ±45-min join found too weak (§122.4) — redesign is the next task. See §122.
- **D150** Stage-3 claim-match join REDESIGNED (`call_verdict.py`, replaces the §122.4 ±45-min window). Match on patient PHONE NUMBER over a whole-day FORWARD window (`call_start − 10 min` … `call_start + 28 h`, reaching the next-morning batch); earliest-unclaimed-in-window wins; two calls to one number pair in call-time ORDER; each row stamped Match Confidence (`unique`/`ordered`/`none`). Root cause fixed: staff file outcomes in morning batches, so a claim's `When` is filing-time not call-time. See §123.
- **D151** Judge-once-fill-later (upsert) for `Call_Verdicts`: the AI judges each call ONCE; when the staff claim lands later, the row's claim/verdict cells are updated in place (no second AI call); the doctor's own columns are never touched; re-runs are idempotent (₹0 on a no-new-work run). Header-mismatch fail-safe refuses to append onto an out-of-date layout. See §123.
- **D152** `Call_Verdicts` row ENRICHED: full Patient Number (from Join Key, always present; replaces the last-4 mask in the DOCTOR-ONLY sheet — blind-judge unaffected, AI still sees transcript only), Recording Link (joined from the Stage-1 `Call_Recordings` tab by Join Key), Match Confidence, and a name/Clinic-ID fallback by number for unmatched calls. Console logs stay masked to last-4. See §123.
- ⛔ **OVERTURNED BY D190 (S130).** *The finding below is FALSE. `saveIncomingOutcome` stamps `Section='Incoming'`, never `Source=incoming`; the incoming `Log outcome` button has been dead for every `Patient_Master` match since it shipped (F-8). "Zero rows, ever" recorded an impossibility as a staff habit. Read D190 and §S130 first. Retained unaltered per D175.*
- **D153** (finding) Staff do NOT file outcomes for INCOMING calls — zero `Source=incoming` rows in `Followup_Outcomes`, ever — so "No claim logged" is CORRECT for incoming calls, not a gap. Real match rate is measured on outgoing-with-claim only (06-Jul: 16/22 Match = 73%). See §123.
- **D154** (design-locked, build pending S124) Verdict Analysis Layer: a daily-updated, read-only, ONE-PATIENT-PER-SCREEN-VERTICAL Google Sheet segregating verdicts by scenario (Mismatch · AI-logged-staff-didn't · Unclear · Matches-collapsed) for fast doctor review; built on the proven `Call_Verdicts` data; one-writer-per-table preserved. See §123.7.

**Continuation — D155–D175 (added at v1.49, Session 127).**

> **Where D155–D160 physically live.** They were written into the tail of `§123.7` at v1.48 and were never added to this index; the index heading claimed `D121–D160` while its body stopped at `D154`. They are **re-homed here by reference, not by movement** — nothing is cut and re-pasted inside a canonical document (D175). Read them in `§123.7`, immediately before the `## §124` heading.

- **D155** Verdict Analysis Layer BUILT (`verdict_review.py`). *In `§123.7`.*
- **D156** Duration gate FAILS OPEN (`Dashboard.html` v18.19; amends D77/D82). *In `§123.7`.*
- ⛔ **PARTLY OVERTURNED BY D190 (S130).** *The numbers below stand. The clause "D153's principle stands (staff do not file outcomes for incoming calls)" is FALSE — D190 destroyed that principle. Retained unaltered per D175.*
- **D157** (correction to D153) 06-Jul was 36 outgoing / 26 incoming; real match rate **16/20 = 80%**. *In `§123.7`.*
- **D158** (OPEN DEFECT) The D150 phone-keyed forward-window join can bind an outgoing claim to an earlier incoming call. Display-mitigated only; **the join is not fixed.** *In `§123.7`.*
- **D159** (incident) `CALLHOOK_SECRET_MISMATCH_403` recurrence; VPS aligned to panel; clinic left on the old secret. *In `§123.7`.*
- **D160** (governance) The live Apps Script project, not GitHub, is the canonical dashboard. *In `§123.7`.*

> **D161 does not exist.** Confirmed by direct search of `v1.48` (S127): two occurrences, both forward-looking ("next free: D161"). It was reserved and skipped, never minted. It is not a lost decision.

- **D162** Dual-key acceptance is mandatory for any shared-secret gate. *§S125.*
- **D163** A gate must write down its refusals before it refuses. *§S125.*
- **D164** `.env` is never edited by line number; its contents are validated at startup. *§S125.* *(Rationale twice retracted — see D166.)*
- **D165** Masked key labels must be encoding-normalised (`unquote()`) before comparison. *§S125.*
- **D166** The correct entry in a knowledge base is sometimes `UNKNOWN`. *§S126.*
- **D167** A control that addresses one path into a hazard is not a control on the hazard (`core.autocrlf`). *§S126.*
- **D168** Install by candidate path and atomic `mv`; never overwrite the live file to test it. *§S126.*
- **D169** Secrets are inventoried by name and value length, never by value. *§S126.*
- **D170** Empty and absent are the same state for `CALLHOOK_SECRET_PREV`. Read the source. *§S127.*
- **D171** A multi-step production rotation is executed by a guarded script, not a human reading exit codes. *§S127.*
- **D172** A check's expected value must be derived from the artefact, never predicted from memory of it. *§S127.*
- **D173** Rotation step 4 must never precede step 3; the command is withheld until it can. *§S127.*
- **D174** A selftest is not a production verification. *§S127.*
- **D175** `§12` frozen as historical; `§12A` carries current state and wins. *§S127.*
- **D176** A procedure must never instruct a human to display a secret. *§S128.*
- **D177** A check must be calibrated to the clock of the thing it checks. *§S128B.*
- **D178** A monitored label must state what the artefact contains. *§S128B.*
- **D179** Report a count with the scope that makes it actionable, or not at all. *§S128B.*
- **D180** An audit finds; it does not fix. *§S128B.*
- **D181** Incoming calls become first-class; the receiver stops discarding what it already receives. *§S129.*
- **D182** An unknown incoming number gets a tile. Identity is established by staff, not by a filter. *§S129.*
- **D183** No call ends its day unlogged; the 21:30 sweep escalates both directions to the doctor. *§S129.*
- **D184** The outcome tile appears at hangup, not at ring. *§S129.*
- **D185** Nothing real-time is built on a system whose running cost is unmeasured. *§S129.*
- **D186** Verification of a subset is not verification of the set. *§S129.*
- **D187** A fix requiring D34's suspension is blast-radius-assessed first, and made last. *§S129.*
- **D188** A filename is not provenance. *§S129.*


### DECISIONS INDEX — D189–D257 (continued, S147; D247 added S149; D248 added S150; D249–D251 added S151; D252–D255 added S152; D256 added S153; D257 added S154; D258 added S155; D259 added S156 (backfilled S157); D260–D263 added S157; D264–D266 added S158; D267–D269 added S159; D270–D271 added S160)

*Lifted verbatim from each decision's own definition line where one existed; the rest authored from that decision's full text in the Archive, never from memory (D172). Complete through D247, no gaps.*

- **D189 — Delete, don't guard, an ungated function nothing calls; suspend D34 by name for exactly one removal.**
- **D190 — A workflow finding must be verified against the artefact before it's relied on; absence of data ≠ evidence of a habit.**
- **D191 — The AI judge proposes; the doctor disposes (two-phase gate).**
- **D192 — A third axis: CONTACT — did a usable conversation happen, and with whom.**
- **D193 — The doctor's dashboard is the sole writer of `Doctor_Verdicts`.**
- **D194 — `Do_Not_Call` is the single enforcement point (the dashboard structurally cannot enforce it elsewhere).**
- **D195 — The tile-return contract: incoming-tile removal moves off `Callbacks_Today.Staff` (reconciled against D78's 3-strike lineage).**
- **D196 — Incoming calls need a stable case identity; `saveIncomingOutcome` keys everything to it.**
- **D197 — Conduct is scored per call against a checklist, never as a number about a person.**
- **D198 — The judge stays blind to agent identity — a rule, not a convention.**
- **D199 — `script_not_followed` / `no_closing` are specified but inoperable until a clinic call-script exists.**
- **D200 — Recording lag is not a blocker and is never measured as a gate (per-call download, fetch-with-backoff).**
- **D201 — Presence is verified by hashing; absence must be proven, not inferred from a stale mirror.**
- **D202 — A decision lives in the KB decisions index, or it does not live.**
- **D203 — Detection and response are separate documents with a stated boundary.**
- **D204 — D113 is intent, not fact (reclassified).**
- **D205 — Patient-facing WABA features are designed at session start, never built as late-session additions.**
- **D206 — Trigger ownership: each file removes only its own triggers.**
- **D207 — Sign-out via a flag, not URL surgery (the Apps Script sandbox can't modify the parent URL).**
- **D208 — Shared-mobile identity fix (F-34 closed): three files; identity ⚠-verify on a shared-mobile no-name match.**
- **D209 — A review SEND-BACK drives the worklist: the verdict re-surfaces the tile with the note.**
- **D210 — Identity evidence at ingest: a single-mobile match is never "High" without a name.**
- **D211 — The dashboard read model is ONE bundled trip behind a per-role shared cache (`getDashboardBundle`).**
- **D212 — WhatsApp tiles show TODAY's outgoing call only, from data already in the bundle (no new reads).**
- **D213 — Seen-today patients get the approved `drmanoj_post_visit` template ({{1}} = name).**
- **D214 — §K one-tap button wording locked verbatim (मरीज़ आ रहे हैं · नहीं आएँगे · बात हुई — फिर call).**
- **D215 — Third attempt = auto-WABA + snooze + doctor NOTIFIED in the panel (read-only band, not an action).**
- **D216 — 3rd-strike message = the approved `drmanoj_followup_due` ({{1}} name, {{2}} due date).**
- **D217 — Incoming rows in `Call_Durations` are keyed `IN-<session_id>` (webhook `payload.id`).**
- **D218 — New final column `phone10`: caller's last-10-digit number, INCOMING rows only.**
- **D219** — F-10 cure pattern: opaque data refs (`dref`/`dget`, dedupe-bounded map, [a-z0-9] keys); no
- **D220** — Cross-day miss counter lives in the Callconsole bundle (`missTotals`); WebApp's per-day logic
- **D221** — K-code write mapping: 1–3 write k-codes with explicit settle column; button 4 writes
- **D222** — 3rd-strike WABA fires only on the transition to exactly 3, via the EXISTING relay's new
- **D223** — Portal "gist" tile registered as Pass 6: one clickable tile on `/portal` opening the doctor's
- **D224** — Attendance system canonical address is `https://attendance.dr-manoj.in`; portal tile updated.
- **D225 — New-lead band: an unknown caller on a CONNECTED incoming call is a high-value new lead.**
- **D226 — Lead lifetime = 3 days (dies on Patient_Master conversion, a terminal outcome, or expiry).**
- **D227 — ONE miss-counter rule for both call directions (the D220 counter applies uniformly).**
- **D228 — One-tap defaults ON; the ⚡ toggle is an escape hatch, removed once one-tap usage >42% for 5 clinic days.**
- **D229 — K-era claim tables (canonical in `call_verdict.py` v2): the CLAIM_EQUIV equivalences.**
- **D230 — D153 RETIRED: incoming no-claim + AI outcome = `SEC_AI_ONLY` (a real gap, no longer excused).**
- **D231 — The 03:40 verdict cron is the guaranteed floor/sweep; the at-hangup worker is the D200 fast path.**
- **D232 — Staff-buzz/ntfy notification idea DROPPED permanently — the tracker is the surface.**
- **D233 — Pipeline QUIET window 01:55–04:05 IST: kicks in the window wait; nightly batches own the slot.**
- **D234 — The kick-queue pattern: the hook writes kicks best-effort (degrade-safe); the worker consumes them.**
- **D235 — Explicit-row writes only; one writer in time (no Sheets append-detection for data rows).**
- **D236 — Digest layer design LOCKED (build before A8; the D223 tile consumes its output).**
- **D237 — Judge-calibration path: a one-time stratified referee set (~40 calls) spanning every stratum.**
- **D238 — The 11:00 pulse always sends and opens with the complete list of the morning's calls.**
- **D239 — Flag Investigator approved (S143 build, paired with the F-42 investigation).**
- **D240** `verdict_review.py` v3 — FORCED CARDS + ONE-DECIDER SPOT-CHECKS (parents D155/D237/D191).
- **D241** INSIGHT HARVEST REGISTER (parent D223; owner-approved list, S143). Fourteen analyses the
- **D242** AI_VERDICT_LAYER_MASTER — GATED WRITE (parent D223/charter S143). The consolidating `AI_Verdict_Layer_Master` document is written ONLY after the D239 Flag Investigator is live AND has run stably for a real clinic period (~S145–146), to avoid the delta-chain rewrite trap (D202) of documenting a moving target. Register-only; nothing is scheduled or built by this decision. Minted at S144 open per the charter; the Investigator went live the same session, so the stability clock now runs.
- **D243** THE #10 TWO-PIPELINE CONVERSION MODEL (parent D241 #10; owner domain input, S144). The clinic runs TWO distinct call funnels that must never be averaged into one conversion number. **(1) Follow-up — informational, no chase:** one call informs a patient a follow-up is due; the clinic does not pursue. The honest metric is *return around the due date* (reminder effectiveness), anchored on the DUE date, not the call — deliberately not a sales KPI, so it never becomes pressure on staff. #2 (retry/stop-after-N) largely does not apply here; the only nuance is a WhatsApp fallback if the single informational call does not connect. **(2) Incoming unknown-number enquiries — fresh leads:** conversion = enquiry → first visit inside a **3-day window** (owner-locked; also register #6). #10 therefore reports TWO numbers, separately. The "said-coming" half already exists in `Followup_Outcomes` (`will_come`/`confirmed`); the "actually-came" half comes from the **daily consultation-report exports** already landing — so #10 is buildable on today's exports and the export-MIGRATION decision is downgraded from blocker to enhancement. Locked: 3-day new-patient window · follow-ups no-chase · ~5-week analysis basis · slice by diagnosis (feeds #11). Open at build: the follow-up return window around the due date; the join key (phone vs clinic UID); the diagnosis field's presence/mapping.
- **D244** RECORDING-GAP DETECTION KEYS OFF PROVIDER STATUS, NOT DURATION (parent D239; finding F-44, S145). A call's duration includes ring/hold, so talk-seconds alone cannot distinguish a real conversation from a long-ringing miss. Every detector that reasons about "did we talk / should a recording exist" MUST read MyOperator's connected-vs-missed truth — the top-level `status` (`bridged` = a conversation; `missed`/`voicemail` = none), the same signal the Apps Script gate already uses (`status == "bridged" && customer_result == "answered"`) and the same `status "1"` vs `"2"` on the `/search` side. A `missed`/`status 2` call is NEVER a "lost recording"; it gets its own non-alert outcome (`missed_no_conversation`). `never_recorded` is reserved for the genuine gap: the provider says CONNECTED (status 1) yet produced no recording — the only subset the Lokesh threshold counts.
- **D245** AI_VERDICT_LAYER_MASTER WRITTEN AT S145 (parent D242; owner decision). The owner directed the Master's write at S145, overriding D242's ~S145–146 timing gate: the Investigator is live (S144) and its first correctness proof (F-44) has landed, so the layer is no longer the moving target D202 feared. The Master supersedes the S131 design spec and retires the S143 charter. **D242 is CLOSED by this write.**
- **D246** THE THREE-PRODUCT LINEAGE (parent D223/D236; owner affirmation, S146). The project is one lineage of three linked products on two substrates: **Followup Tracker** (clinic PC, offline — source of follow-up intent) → **Callback Tracker** (VPS, Sheet + Console — system of record / Product A) → **Call Intelligence** (VPS, `recordings-archive` — analytics / Product B). The boundary is conceptual + a code/doc/contract seam, NOT separate infrastructure: one VPS, one repo, one secret store, one EOS discipline for A+B; the Followup Tracker stands most separate (own machine, offline, frozen). The demarcation exists for triage and safe iteration: A is operational-urgent with a manual fallback and trends toward frozen; B is owner-facing, batch, next-day-tolerant, free to evolve without risking the core. Three seams; the two downstream are defined contracts (Callback→Intelligence via Sheet tabs; Investigator→Digest via `flag_investigator_results.json`, hardened by B1); the **Followup→Callback** seam is not yet a named contract — its break is the chain's highest-impact failure, and the parked Docterz export migration (D243) lives there. Register entries for verdicts/insights/analytics are tagged **Product B** from S146.
- **D247** CANONICAL DATA MANAGEMENT — THE TIERED KB (owner decision, S147; full text in `D247_Canonical_Data_Management_S147.md` and Archive §S147). The knowledge base is restructured: the monolithic KB v1.72 retires; **this Register** (small, Tier 0, rides the session loop — authority on what is true NOW) splits from the **KB History Archive** (append-only, Tier 1 — every session narrative + full decision text, verbatim). Every canonical document is listed with its tier and md5 in **`CANONICAL_MANIFEST.md`** (Tier 0, the linchpin Phase 0 verifies). Three tiers: **Tier 0** read every session; **Tier 1** hash-verified, opened on demand; **Tier 2** frozen products — hash-verified only, never in the loop, waiver to change (each with one canonical dossier). Clarifies **D202**: the split is two complete consolidated files, neither a delta chain. EOS becomes tier-aware (`END_OF_SESSION_PROMPT_v4`): append to the Archive, small targeted Register refreshes, maintain the manifest — no more whole-KB rewrites.
- **D248** WAIVER — `clinic_writer` unfrozen for one owner-approved batch (S150; D34 discipline). The Tier-2 frozen Nutrition/Diet write-path (`clinic_writer`, D247) was unfrozen under an explicit owner waiver for a batch of doctor-approved changes to `vitals_page.html`, then re-frozen with a version bump (dossier v1 → v1.1). All changes are in `vitals_page.html` only — the engine (`clinic_writer.py`), Flask app (`vitals_app.py`), ledger schemas (20/14 cols) and the archived-PDF/print output are untouched and byte-identical; no VPS/live code. Changes: **(a)** Hindi spelling/grammar tidy in the exercise/modality LIB strings (`name_hi`/`instr_hi`) — **closes the sole open dossier caveat** (§5/§6); **(b)** exercise library extended 126 → 128 (Frozen-Shoulder Standard Internal-Rotation towel; Rotator-Cuff Standard Cross-Body) plus a PIVD knee-to-chest stop-rule and a bottle-roll dose fix; **(c)** the Excel `Diet_Chart` tab ported into the tool as a new optional printable diet sheet gated by an “Include diet chart” checkbox (default ON) — **diet-aware** meal schedule (owner choice (b): eggs for Egg+Veg, soy/paneer swaps for Pure Veg, local fish + chicken for Non-Veg), the weekly **shopping list dropped**, sections A/B/C + comorbidity (relabelled D), feeding the existing text-only archive seam with zero engine change; **(d)** a **screen-only** reading-comfort colour theme (`@media screen`) — print is fully isolated and unchanged. `vitals_page.html` v26 → **v28**, md5 `fcedae303b620f3e5199f4b1e4766510`; owner-confirmed **installed live** on `D:\clinic_writer\`. A build-time `ReferenceError` (a Section-B `cond` scope slip) was caught by the functional node smoke test **before delivery** and fixed — reinforcing that `node --check` verifies syntax, not scope, and the artefact-level second check is mandatory (not a live fault; no F minted). *Full text: Archive §S150.*

- **D249** — Staff punctuality & incentive policy effective 01-08-2026: grace 10 min → marks (>30 min = 2), 3 marks = half-day deduction, >60 uninformed = half-day absent; incentive by salary band on marks, ramp Aug–Sep (≤5/≤8) then strict (≤2/≤5); Rs 200 evening cover only with punch-out; July is pre-policy preview. *Full text: Archive §S151.*
- **D250** — Darpan financial systemisation (figures workbook-only, F-31): two-tranche loan, FLAT Rs 1,000/mo interest (stops at tranche clear; skips capitalise), waterfall int→int-bearing→free, 2 skips/FY then recover-from-perks, ST advances clear in-month, classed+narrated ad-hoc ledger, outstation = cash at trip end + log settles biometric absents. Deliverable `Darpan_Loan_System_v2_3.xlsx` md5 `dd6689e1…`; **workbook integration = top job S152**. *Full text: Archive §S151.*
- **D251** — Salary-layer architecture: workbook home `D:\clinic_salary\` (never in git); one master per concern (no per-employee CSVs); Phase 1 LIVE `att_month_report.py`; Phase 2 = Google-Sheet migration + gspread output tab bundled with key rotations; Phase 3 = doctor-PORTAL salary tile bundled with D223 (not the staff attendance site), decided after Phase 2. *Full text: Archive §S151.*
- **D252** — Attendance discipline package eff. 01-08-2026 (extends D249; chat label "D251"): grace capped 8 days/month then ≤10 min = 1 mark; 3 marks = one day half-day (reworded); **Sundays counted normally (D249's Sundays-never-late rule revoked)**; uninformed absence ₹50 (default = informed, owner flags exceptions); >3 absent days/month = +₹100/day from day 4; cap crossed 3+ months/year → increment reduced/withheld at owner discretion. Fines enforce only with the September-run script. *Full text: Archive §S152.*
- **D253** — Sunday roster eff. 01-09-2026 (chat label "D252"): A (Shivani·Awdhesh·Pravesh·Darpan) 1st&3rd full duty · B (Alisha·Shavez·Ranjeet·Sukhveer) 2nd&4th · other Sundays fully off · C (Sandip·Vikki·Surendra) + Arjun stay every-Sunday-half-day · 5th Sunday = normal full day for all · pharmacy closed Sundays (Darpan housekeeping) · Shavez backs clinic on B-Sundays · swaps mutual + prior info · cost-neutral; `sunday_group` column + roster logic in the monthly report. *Full text: Archive §S152.*
- **D254** — The leave register defines "informed" (chat label "D253"): bound page-numbered reception register + approver initials, or an emergency phone call — a WhatsApp message alone ≠ informing → D252's ₹50; no separate non-compliance fine (the fine attaches to the absence, never the message); uninitialled timely entry = informed; 2-week warning-only transition. *Full text: Archive §S152.*
- **D255** — Staff Management System (DRAFT; chat label "D254"): attendance reframed as one module; Monthly-Adjustments ledger · Staff Advances auto-instalments · quarterly 50/50 Appraisal hosting D252's habitual clause · **maker-checker entry on the VPS dashboard** (append-only + contra entries, full audit stamps, phone-tap approval) · **issuance & entitlement registry** (dress/ID; chargeable replacements auto-deduct; one-time Google-Sheet import then freeze). Pending: rate card + maker confirmation + phase-split approval. Deadlines: report script 01-09; module before the 01-10 run. *Full text: Archive §S152.*
- **D256** — Attendance discipline computation rules, consolidated (S153; amends D252/D253): late bands per episode (grace ≤10 min, cap 8 days; 11–29=1, 30–59=2, ≥60=2/3 by informed flag) · Option-B slab deduction `floor(max(0,marks−limit)/3)` half-days, limit 8 Aug / 5 Sep+ (**Sept-strict: the notice overrides the S151 Aug+Sep ramp**) · incentive FULL=1 day salary, HALF=half day · OT = 2× per-minute rate, minutes-based, approval+punch-out compulsory, candidates only · early departure 3 tiers (≤30-min double-punch artefact = duty done · ≤120 auto-deduct 1× · >120 EARLY_BIG sheet-review vs register) · single punch = stayed till end · 30-day basis · Arjun minutes-exempt · Net = incentive+OT−deductions (OT in by default) · Sunday swap needs register entry + both signatures + doctor countersign · July 2026 diagnostic-only, Aug first billing month · leave register live 06-08-2026. *Full text: Archive §S153.*
- **D257** — Staff Ledger maker-checker BUILT (S154; implements D255(d) + ledger/advances slices of D255(a)(b)): makers Shavez (full) / Alisha (limited); doctors = checkers + DIRECT enterers; ad-hoc fines doctor-only, narration mandatory; rates ₹20/₹20/₹200/₹100, per day; advances full-current-month default, instalment override, declining balance, payout excluded from salary summary; append-only + contra-only corrections; self-entries flagged; swappable password logins; monthly close emits `approved_adjustments_YYYY-MM.csv` (nothing auto-pays); data F-31 on VPS; additive app (frozen core untouched) at `attendance.dr-manoj.in/ledger`. *Full text: Archive §S154.*
- **D258** — One home per rupee (S155): the Staff Ledger owns ALL staff money, structured loans included — workbook-exact loan engine (instalment IS the whole deduction, interest out of it, cross-tranche waterfall, skip=pause+Rs1000 capitalise, 2/FY, interest stops at tranche clear); Darpan migrated live + verified to the rupee; workbook Darpan sheets RETIRED 07-08-2026; workbook canonical home = VPS `/root/clinic_salary/`; repayment never typed, skip never a Rs 0 entry. *Full text: Archive §S155.*
- **D259** — Full backend salary automation (S156; BUILT+LIVE): `/salary` reads `att_month_report`'s output files as the interface (never re-derives policy; shared `month_adjustments()`); on-screen informed-flags/EARLY_BIG/OT/outstation; **APPROVE & LOCK** → `SALARY_PAID` rows + `salary_final_<month>.csv` + frozen `salary_final_<month>.html`; input-token anti-drift; a locked month is never recomputed (corrections = next-month adjustments); workbook read-only, retires after one clean month. *(Backfilled to this index S157 — the S156 index-lag, D172's own field again.)* *Full text: Archive §S156.*
- **D260** — The clinic + personal estate is ONE system across three hosts, mapped into a single reconciled master inventory; the "projects" are a documentation boundary, not a code one (the automation repo is a monorepo). Verify from live source, never from a register/dump/filename that merely looks current (reinforces D188). *Full text: Archive §S157.*
- **D261** — Portal single-sign-on = an SSO **broker** (owns login + roles doctor/manager, issues one signed `.dr-manoj.in` cookie) + a shared **verify-shim** per VPS app, each app keeping its own login as fallback. A shared cookie alone is NOT SSO — every app must trust and verify it. The Apps Script cockpit stays link-based. *Full text: Archive §S157.*
- **D262** — Portal app-selection: doctor portal = web SSO apps + cockpit(link) + optional report-Sheet views + a **PC-only local-tools group that absorbs the Clinic Hub**; manager portal = attendance + asset + ledger-entry(maker), no salary. Local apps are `localhost`+PHI → never served remotely. The cockpit is the only user-facing GAS tile; the personal cluster is excluded. *Full text: Archive §S157.*
- **D263** — A dedicated **`Salary_System_KB` (Tier-1)** consolidates the Staff Ledger + backend salary automation as one reference; system only, no staff figures (F-31). *Full text: Archive §S157.*


- **D270** Surgical Case Pack → VPS (off-Drive); reverses D262 / re-amends D137. Full text: Archive §S160.
- **D271** Staff Daily Register subsystem adopted (design v1.0). Full text: Archive §S160.
- **D272** Shavez is **both maker and checker**; on a date Shavez entered, his own one-click approve is DISABLED → an override (Manoj/Bhawna) must approve. Self-approval barred. Full text: Archive §S161.
- **D273** The **Register is the single staff-master**; the workbook→CSV path is RETIRED. The register (SQLite) is the source of truth and regenerates the derived read-only `staff_master.csv`; seed = the current CSV, `staff_id = user_id`. Full text: Archive §S161.
- **D274** Per-staff **appointment-document vault**, VPS-disk **off-Drive** (F-56 parked); custodian = Shavez + override; Alisha/Shivani excluded. Full text: Archive §S161.
- **D275** **Absence classification is the biometric/attendance system's job**; the register captures only the LEAVE decision + exceptions (it never re-derives presence/absence). Full text: Archive §S161.
- **D276** **Per-staff scoping.** Arjun (`minutes_exempt=1`): leave-only — NO dress/i-card/60-min-late/OT; over-quota leave = flat pro-rata base/30 per excess (still gets the leave quota). Extra-duty = **Shivani only**. Outstation = **Darpan only**. Label renames: "Informed by"→"Approved by"; "Cover"→"Extra duty". Full text: Archive §S161.
- **D277** **OT is approved-by-default**; it is NOT a maker field. Only the checker + override may review next-day to un-approve. Full text: Archive §S161.
- **D278** **Festival leave classified by DATE** (an advance festivals list); 2/year on top of the 2 regular monthly discretionary; Holi = a `festival_day` with `clinic_closed=1` (full closure, consumes nothing); unused festival encashed at FY-close (Diwali). Full text: Archive §S161.
- **D279** **Leave/absence salary model (the "C-model") — SUPERSEDES the dossier's §5 encashment design.** C = discretionary leaves taken + genuine (unsanctioned) absences (both eat a 2-day/month buffer; roster Sundays OFF are handled upstream). Every day of `max(0, C−2)` **plus** over-quota festival days is deducted at **base÷30**. The ₹50/₹100 fines stay and stack unchanged; late-marks/early logic unchanged; incentive → the annual pot. Full text: Archive §S161.
- **D280** **Unused-leave encashment is attendance-gated** — paid `((2−C)×base/30)` ONLY when there are **zero** deductible extra days; any extra absence forfeits it entirely (owner chose the gated option). Full text: Archive §S161.
- **D281** **The salary engine is a standalone read-only module** (`salary_engine.py`) reusing att's `salary_inputs` CSV + the ledger's `compute_salary` (read-only) — no re-implementation, no drift. **Stage A** = read-only preview (delta + complete new-model net). **Stage B** (the official locked/approvable run) is DEFERRED until the register is filled with real maker/checker data. Full text: Archive §S161.
- **D282** (clarification) **Sunday half-day for pre-Sep months is automatic**: `att_month_report.ROSTER_FROM="2026-09"`, so pre-Sep months use each staffer's `sun_start`/`sun_end` half-day columns. The register's Sunday toggle governs only the daily-grid DISPLAY, not the July salary math. Full text: Archive §S161.


### DECISIONS INDEX — D264–D269 (S158/S159; folded into the index at the S178 compaction — they had been minted but never bulleted here, only in the removed additions prose. Full text: Archive §S158–§S159.)

- **D264** — One-app-at-a-time SSO rollout + the inert-on-failure invariant (each verify-shim is inert if the portal secret is unreadable → the app behaves exactly as before; no edit can remove existing access). *§S158.*
- **D265** — Auth-vs-authorization shim law + the **manager→checker guardrail** (a manager never sees Salary; `…/salary` 403s). *§S158.*
- **D266** — Named per-person managers (shavez/alisha as `manager`). *§S158.*
- **D267** — Per-device PC-marker gating for Clinic-PC tiles (marker cookie via `/portal/mark-pc`); **no localhost probing** under Chrome PNA. *§S159.*
- **D268** — Capability URLs (CC Saver / Inbox Janitor) live only in git-ignored `portal_config.py`, never in the repo. *§S159.*
- **D269** — GMB is the static-HTML exception to D262 (VPS-hosted `/portal/gmb` behind login); CC→Tally VPS-hosting DECLINED. *§S159.*

### DECISIONS INDEX — D283–D312 (continued; folded into the index at the S178 compaction from the removed §S162–§S172 STATE/additions blocks. Full text: Archive §S162–§S172.)

- **D283** — Register-native Stage-B salary lock (`locked_run`; salary view = manoj+bhawna, lock = manoj-only; anchor ₹1,07,447). *§S162.*
- **D284** — Biometric daily grid + `leave_sanction` date range. *§S162.*
- **D285** — Portal `staff` role + tiles + salary split. *§S162.*
- **D286** — Leave/uniform/i-card moved out of the ledger into the register store. *§S162.*
- **D287** — Ledger salary accordion (layout-only) — **SUPERSEDED by D288, not installed.** *§S162.*
- **D288** — CONSOLIDATION: one salary system in the register; register salary READS the ledger money rows, the ledger reverts to money-book. *§S162.*
- **D289** — Standalone register salary engine (D288 executed): `/register/salary` computes the whole take-home from primitives; OT removed; incentive→annual pot; parity proven July (₹1,07,447 anchor to ₹0.66). *§S163.*
- **D290** — Register owns EARLY-BIG rulings (`earlybig_ruling`, one writer + doctor-only screen; register overlay wins over the ledger base). *§S163.*
- **D291** — Salary coverage keys off approved capture (≥1 `day_review` `status='approved'`, not exception-row count) — fixes F-67 (overpayment). *§S164.*
- **D292** — Pending-review board `/register/review` + role-aware `/register/review/counts` (keyed off `approval_blockers`; makers never see an approve count). *§S164.*
- **D293** — Shivani activated as a maker (`SR_INACTIVE_MAKERS` "shivani"→""). *§S164.*
- **D294** — Manoj-only portal user management (`/portal/users`, `PORTAL_USER_ADMINS=manoj`; self / last-active-doctor guards). *§S164.*
- **D295** — Darpan outstation +₹250/night is IN salary (not cash); closes the S163-open question. *§S165.*
- **D296** — D223 gist delivered as two units + the `portal_gist.json` contract (builder one-writer/fail-loud; portal consumes; metrics extend by adding JSON keys — no rework). *§S165.*
- **D297** — Call-Intelligence Console SIGNED (14-track; builder `portal_console.py`→`console.db`→doctor portal; retires the GAS referee + `verdict_review.py`; contract `D297_Call_Console_Contract_v4_FINAL.md`). *§S166.*
- **D298** — `console.db` build architecture (full-rebuild-idempotent atomic spine; header-by-name fail-loud; ported Netting net-missed; MyOperator `/search` reconcile in-cron; persistent transcript cache; F-31/F-49 on the PHI stores). *§S167.*
- **D299** — Agent attribution + backfill (`/search` `_us[received].ky`→`Agents.UserId`; additive `call_agent`; console prefers `call_agent > verdict.agent > outbound`; extends D246). *§S168.*
- **D300** — Console display/dedup rule (one-verdict-per-join_key `MAX(id)`, one-patient-per-phone before any count — F-74; AI-verdict fail-loud) + broadened staged build order. *§S168.*
- **D301** — Stage-2a agent backfill built at `--days 60` (100% vs 75%@30d; `/search` time-windowed; 1023 rows → 1001 distinct PK-deduped, documented). *§S169.*
- **D302** — The rev5 punch-list = the canonical ordered console backlog, autonomous execution; supersedes the build-dossier §8 roadmap as the *execution* authority. *§S169.*
- **D303** — Console cron is ALWAYS the full `--days 60` build under `flock` (never a light `--days` variant — F-75). *§S170.*
- **D304** — New persistent PHI stores: `console_reviews.db` (portal sole writer — dispositions vocabulary + send_backs) · `rec_cache/` (builder sole writer, 60-day/1 GB pruned) · builder-owned `Dr_Manoj_Call_List` tab; ALL gitignored. *§S170.*
- **D305** — 3-wave clubbing (amends D302 execution). *§S170.*
- **D306** — Review store VPS-canonical; the dead `Dr_Manoj_Call_List` sheet-push removed; nightly Drive backup owed. *§S171.*
- **D307** — v3 design system + preview-first loop + served-HTML gating (the G1 absence check). *§S171.*
- **D308** — Staff coaching model (Hindi coaching report + per-staff WhatsApp blocks) + signed recording-only staff links (training corpus). *§S171.*
- **D309** — Surgical Case Pack ported into the portal (`/portal/casepack*`; PHI → `/root/wa/casepack/`; PC tool = fallback). *§S172.*
- **D310** — The ONE canonical WhatsApp sender (`portal_wa.py`, template-family aware, DRY-RUN default; Phase-B GAS shared-secret shape). *§S172.*
- **D311** — Follow-up batch (`portal_followups.py` reads the daily `Staff_Action_Today_*.xlsx`; OD→template ladder; tier-grouped). *§S172.*
- **D312** — Portal UI served-from-disk + cache-bust (4 UI files edit-in-place, no restart; widget `?t=Date.now()`). *§S172.*

### DECISIONS INDEX — D313 (S179; the clinic-finance subsystem. Full text: Archive §S179.)

- **D313** — **Clinic Finance subsystem architecture (medical live; clinic + lab to replicate).** One VPS `clinic-finance` app (system python3, `/root/finance/`, `/finance` on the portal origin) migrates all three units' daily revenue off Google Forms — **medical first, clinic + lab a replication**. Locked invariants: money is INTEGER PAISE; **opening/closing cash is COMPUTED via SQL views, never typed** (kills the 36 carry-forward breaks by construction); revenue counts in full, cash does not (`day_noncash_bill`); a deposit is never split (only the OLD month's share named, `clears_ym`/`clears_amount_p`); missing days shout and never go silent; the **patient-revenue spine reads, never posts** (attribution reconciles to the day total, cannot alter it); the line source is a **pluggable adapter selected by column map, not code** (`sarvam_ocr`/`marg_export`/`labmate_export`/`tracker`/`manual`); UPI is **bank-arbitrated** (ICICI MPR self-checked against its own Grand Total; entered-vs-bank mismatch shouts until acknowledged); scans are evidence relocated to Drive, never deleted; the three units stay separate for accounts; auth is fail-closed (see F-84). Reversible: Forms retired per unit only after a clean parallel run; manual workflow is the standing fallback. Extends D261/D262 (portal/SSO) + D235 (one writer per store). Sole live-state reference: `S179_Finance_LIVE_State` (Tier-1). *§S179.*

### DECISIONS INDEX — D314–D316 (S180; the Marg feed, sale returns, and closing a lost canonical row. Full text: Archive §S180.)

- **D314** — **A sale return is stored as a MAGNITUDE, with its direction in the row's type — never as a negative amount.** `sale_item.amount_p` carries `CHECK (amount_p >= 0)`: a deliberate invariant (amounts are magnitudes; direction is the row's type). SQLite cannot drop a CHECK with `ALTER TABLE`, so removing it would mean create-copy-drop-rename on a live table holding 121 days of patient data — a data migration, to change a *reporting* behaviour. Instead a return stores as a positive `amount_p` with `service='<base>_return'` (`pharmacy_return` / `lab_test_return`), and **one view** (`v_day_attribution`) nets it back out; `sale_item` was first confirmed to be summed in exactly one place. The queue table `sale_item_review` has **no** such constraint and deliberately keeps the value **SIGNED**, so `in_review_p` stays honest — therefore **every path that moves a row from queue to spine must convert the sign back into a magnitude plus a `_return` service** (missing that was a live 500, fixed the same session). Adapters return `amount_p` as a magnitude plus a `kind`; `classify_amount()` keeps "no readable amount or exactly zero" as junk and treats a negative as a RETURN. Applies unchanged when clinic and lab replicate. *§S180.*
- **D316** — **An irrecoverable canonical row is CLOSED as LOST, never left permanently unverifiable.** Phase 0 verifies what the canonical set *claims* to contain. A row that genuinely cannot be recovered, if left listed-but-unverifiable, makes Phase 0 halt on the same rows every session — and a halt that always fires is a halt that gets waved through, which destroys the check's value for every other row. So an irrecoverable row is **closed** in the manifest: its pinned md5 is kept for provenance, and its consequence is stated as either **LOST-SUPERSEDED** (a later version is verified present; nothing current depends on it; no action) or **LOST-RECONSTRUCTABLE** (it is current, but a predecessor plus the Archive narrative can rebuild it; a backlog item, not a permanent flag). **A closed row is not drift and does not halt Phase 0.** Only a row listed as present that fails its hash does that. *§S180.*
- **D315** — **A patient-identity match is graded, and only the top grade may feed an audit.** Revenue attribution tolerates a probable match: being wrong costs a rupee in the wrong history. A discount or return audit does not: being wrong names the wrong patient, the wrong day and the wrong person behind the counter. The same match therefore carries two thresholds — all grades feed revenue, only the top grade feeds the audit. Implemented as `finance_identity` grades (`corroborated · unique_exact · near · ambiguous · none`; only the first two offered as a default click, `ambiguous` deliberately offering nothing) and `finance_returns` verdicts (`conclusive · probable · patient_only · none`; only `conclusive` audit-fit). A corollary measured at S180: the clinic ID is four digits on 111 of 113 real bills, so a non-four-digit ID is neither discarded nor trusted — it scores below `ingest.min_confidence` and goes to review. *§S180.*

### DECISIONS INDEX — D317–D319 (S181. Full text: Archive §S181.)

- **D317 — Deploy-by-kit over GitHub, one command a side.** Kits in `deploy_kits/`; PC publishes by one double-click (`push_kit.bat`); VPS installs by one pasted command (`vps_deploy.sh <KIT>`: SUMS + KIT_ID currency (F-88) → the kit's own gated installer: preflight → stage-from-kit-dir → backup → swap → python3 migration → smoke gate → restart on green → HONEST red). A re-issued kit takes a NEW name. Owner's explicit OK = running the command.
- **D318 — The clinic module's owner-directed shape.** Typed tender totals post (cash/upi/card/razorpay); per-stream truth is Docterz's, read-only beside the entry; strays carry mandatory narration; expenses reduce the drawer only; two-stage approval (verifier → settings-named final checker; verification a side-table fact, never a status rebuild; self-verify barred, D272); UPI reconciles against the bank alone — card/razorpay against their own rails.
- **D319 — The KB swap is the assistant's job.** At every EOS the assistant writes canonical docs directly into project knowledge (replace-in-place) + MD5SUMS; the owner does exactly two things: one double-click (KB git kit) and one download (cold kit). Phase 0 hash verification unchanged.

**Next free clinic decision: D320.** Asset-app decisions **A-D1–A-D24** are *sub-project scope* (next free A-D25) — indexed in `KB_Asset_Register` + Archive §S173–§S177, and never consume clinic D-numbers.

## RESERVED / OPEN DECISION NUMBERS
- **D83–D92** remain RESERVED for the pending lifecycle proposals P1–P10 (KB §55), still awaiting lock.
- **Next free decision number for new work: D317.** (**D314–D316 spent S180** — return storage shape; graded identity. **D313 spent S179** — the clinic-finance subsystem.) (**D213–D216 spent in S137** — seen-today template, §K wording, third-attempt rule, 3rd-strike template + snooze; see §S137.2.) (**D211–D212 spent in S136** — see §S136.6.) (**D206–D207 spent in S134** — trigger ownership and sign-out-via-flag; see §S134.6.) (**D205 spent in S133** on the seen-today WABA feature — see §S133.5; **D204 spent in S132** — see §S132.7.) (D189/D190 spent in S130; **D191–D201 spent in S131** on the AI review-layer design — see §S131.7; **D202 spent in S131** on the record itself — see §S131.14.) **D1–D120 are NOT in the index below and never have been (F-22). Fifteen are restored: D62, D66, D68, D69, D77, D78, D80, D81, D82, D97, D98 in §S131.13, and D112–D115 in §S131.16. The rest live only in the Session 1–62 runbooks.**

---


---

## FINDINGS — F-0 … F-95 (next free F-96).

> **S181 minted six. Full text: Fault_Action_Register v2.17 §7.1-successors / Archive §S181.**
> **F-90** (OPEN · owner decision) — the GitHub repo is PUBLIC, proven by anonymous clone; answers F-9's "visibility UNKNOWN". Recommend private + read-only deploy key.
> **F-91** (OPEN · behavioural) — UPI recorded as Cash at Docterz entry (₹17,900/6wk; invisible to any ledger-internal check; the typed daily tab is the reconciliation anchor).
> **F-92** (OPEN) — discount capture stopped 18 Jun 2026 (₹1,33,720 then zero; concessions still given, no longer valued; part of an 18–19 Jun regression cluster).
> **F-93** (OPEN) — the concession parser swallows the Docterz footer → three fake "patients" a day in the staff-facing sheet.
> **F-94** (CLOSED by D317's rules) — an installer's environment assumptions are part of its specification (the C1a/C1b/C1c red trilogy).
> **F-95** (CLOSED by rules) — a synthetic store proves logic, not life: smoke checks print what they saw; invariants asserted as invariants; enrich the offline store with live-shaped data before a first live gate.
> *Recorded unminted:* Drive modifiedTime as false freshness · Docterz export schema instability · the Lab ₹2,71,380 no-tender block · the medical broker-role guard bug · the canonical set's own unmasked patient numbers · the seed script's hard-coded path.

> **S180 raised five, and two are about how the session itself worked. Full text: `Fault_Register_append_F85_F89_S180.md` + Archive §S180.**
>
> - **F-85 (S180) — session-numbered artefacts were labelled with a forward number before the session that would carry it had opened.** `S180_Marg_Folder_Recon` was written during S179, before the S179 close-out; the next session's survey then inherited that label and called itself S181. Derived from artefacts rather than labels, the true number was 180. Kin to **D188** (a filename is not provenance). RULE: a session number is assigned by a close-out, not by anticipation.
> - **F-86 (S180, self-caught before install) — a reader built for a PHI source emitted full phone numbers because it was written against the source's shape, not the destination's rules.** `patient_ref` stores `phone_last4` and nothing more, and `ingest_column_map` has no phone field at all. The CSV now carries last-four only; the item CSV carries no patient identity at all; outputs were grepped for any 10-digit string. RULE: the destination's constraints are part of the spec, not a detail discovered at install.
> - **F-87 (S180) — a change was shipped to a test suite that could not be run offline, twice.** `finance_app.py`'s smoke is written against the real store (>100 filed days, approved/locked days, open exceptions, a legacy tail leaving cash negative), so it would not run here; that was treated as acceptable and the change shipped on reasoning alone. It broke two assertions on the box and the install gate rolled it back correctly. **This is F-84's own lesson — "the offline-testing shortcut was the vulnerability" — repeated after this project had already minted it.** Two concrete traps, now written into the code: `ingest_day` **supersedes** the day's previous batch and **deletes** what it produced, so any test that ingests destroys earlier setup (cost two debugging rounds in one session); and resolving a queued line **adds** a `sale_item` that an earlier check counts. **The remedy is an asset, not a resolution:** `dev_seed_smoke_db.py`, and the differential method (unmodified 163/173 vs modified 166/176 on identical seeded data — zero failures added) used before the third build shipped. **RULE: if a test suite cannot be run, making it runnable is the first task, not an optional one.**
> - **F-89 (S180) — the cold-backup cadence lapsed for nine sessions, and three canonical documents were lost as a direct result.** `END_OF_SESSION_PROMPT_v4 §E` calls for a full cold kit every three to five sessions. The newest on the owner's machine was **`DrManoj_Clinic_FULL_Handoff_Session171`**. The three documents that could not be recovered are **S177 and S178 outputs** — everything up to S171 was comfortably recoverable from disk, everything after depended on whatever happened to be downloaded loose. The loss was not caused by the S180 Phase 0 that found it; it was caused nine sessions earlier by a cold kit not taken. **RULE: the cold kit is not discretionary. It is a standing backlog item with a session count against it, and the count is checked at every close.** Restored at this close (`KB_S180_close.zip`); next due within three to five sessions.
> - **F-88 (S180) — a passing `md5sum -c` proves a kit is internally consistent, not that it is the intended kit.** Two install attempts ran an older download whose checksums matched its own files perfectly. Kin to **D188**. Fixed by having the installer carry the identity of the build it belongs to and refuse to run otherwise; the guard was tested against the superseded module before shipping. RULE: an install kit states which build it is, and a checksum proves integrity, never currency.

## FINDINGS — F-0 … F-84 (as at S179).

> **CURRENT #1 OPEN (flagged S178): F-82 (S172, OPEN · VENDOR)** — MyOperator WhatsApp API returns HTTP 500 on ALL authenticated calls (portal + tracker, same token; no-auth 401; inbound webhook healthy) → account-side at MyOperator; **WABA go-live blocked**, escalated to Khushi + Lokesh; when restored flip `PORTAL_WA_DRYRUN`→"0" + self-send, no code change. Full text: Fault Register / Archive §S172. **F-84 (S179, FIXED): three self-found security faults in the finance module, all the same shape — an offline-testing/dev convenience carried into production. (1) reads ungated → fail-closed `before_request` allow-list; (2) identity from spoofable `X-Clinic-*` headers in prod (`curl -H "X-Clinic-Role: checker"` = full control) → real SSO cookie authoritative + header auth opt-in only + *signed-in ≠ entitled* (no `unit_role` row = 403); (3) epoch never checked → read live + fail-closed on every request, `healthz` surfaces `sso_epoch_ok`, installer auto-rolls-back if false. THE LESSON: anything that grants identity for convenience must be opt-in; the production default must be closed. A fourth, smaller lesson — a test asserting an environment accident ("epoch unreadable here") rolled back a good install; tests must assert behaviour, not the machine's state. Extends F-63/F-68. Full text: `Fault_Register_append_F84_S179` + Archive §S179.** *F-83 (S176, asset-app located): the intake background Sarvam-OCR thread is fire-and-forget — dies on service restart and skips non-draft bills (why B-0001 arrived blank); mitigated by A-D23 (visible `ocr_status` + manual Re-read); durable queue/worker fix queued. Full text: Archive §S176 + the consolidated F-82+F-83 append (→ Fault Register v2.17).* *F-76 (S171, WITHDRAWN): SA sheet-write 403 — superseded by D306, scope NOT widened. F-77 (S171, closed): training CSV empty/Excel-hostile → UTF-8 BOM + route fix. F-78 (S171, closed): `build_no_shows` `[:10]` on DD-Mon-YYYY — due-vs-today + calls-since-due computed on the wrong format (correctness, not cosmetics); parse to ISO at build. F-79 (S171, closed): stale flex rule later in the stylesheet overrode the new grid — CSS cascade regressions are invisible to string assertions; gate on SERVED HTML incl. absence checks (D307c). F-80 (S171, closed): gspread 6.x `.client` lacks `open_by_key`; the AttributeError was swallowed → silent `found=False`; open via the base `gc`; never let a version-sensitive path fail silently. F-81 (S171, OPEN): duplicate call rows in the live log — suspected MyOperator reconcile double-insert; builder-side investigation owed. Full text: Fault Register v2.16 + Archive §S171.* *F-75 (S170): `portal_console.py --build` is window-scoped + atomic-from-scratch — a small `--days` cron silently destroys `call_agent` + the net-missed correction every fire (observed 1001→60 at the gate, BEFORE arming); scheduled job = ALWAYS the full 60-day build under `flock` (D303); RULE: dry-run the exact scheduled command and diff artefact invariants before arming any schedule. Full text: Fault Register v2.15 + Archive §S170.* *F-65–F-74 indexed in the v2.8–v2.14 Fault Registers / Archive §S162–§S168.* *F-64 (S161): `staff_ledger.py` **code** lives at `/root/staff_ledger.py` while its **data** dir is the separate `/root/staff_ledger/` — reusing the ledger's `compute_salary` from the register app required adding `/root` **and** `/root/portal` to `sys.path` (guarded); diagnosed via a `ModuleNotFoundError` surfaced by a temporary error-carrying module global. Full text: Fault Register v2.7 §7 + Archive §S161.* *F-62 (S160): “audit the artefact, not the label” — a doc filed Surgical Case Pack under “Website/SEO”, hiding that it is a local PHI store (bundles+consents+ledger, off-Drive by design); classify from the CODE, not the doc tag (kin D188/F-54). F-63 (S160): the portal `pc`-NameError shipped despite `py_compile` + isolated Jinja render passing — the wired route was never exercised; DELIVERY GATE for any live Flask change is now a Flask **test-client hit on the ACTUAL route** (200 + expected content), not just compile + isolated render.* *F-59 (S159): Chrome refuses ports 5060/5061 (SIP) as ERR_UNSAFE_PORT — curl/CLI ignore the list, so a server looks healthy while every browser fails; suspect it first when curl works but the browser won't open. F-60 (S159): the VPS filesystem is case-sensitive — `GMB.html` ≠ `gmb.html`; the filename's case must match what the code opens (kin of D188). F-61 (S159): pasting a fenced code block's language label (```python) into a live config put a bare `python` token in `portal_config.py` → NameError → whole config unreadable → portal “Setup needed” (secrets intact); paste only lines BETWEEN the fences, and diagnose a sudden “unconfigured” with `python -c "import portal_config"`.* Full text of all three: Fault Register v2.5 + Archive §S159. *F-57 (S158): scope a catch-up from the live target, not our own records (live Notion ended S147 vs claimed S150). F-58 (S158): Flask test client ignores a raw Cookie header — use its set_cookie jar for cookie-auth smoke.* *F-50–F-56 (S155–S157) are indexed in `Fault_Action_Register v2.3` §7 with full text in the Archive; S157 minted F-54 (App_Service_Register wore a 7-Aug date over S63 content), F-55 (partial GitHub JSON repo-dump), F-56 (uploaded zips carried secrets+PHI+F-31 — rotate the service-account key).* **F-49 (S154):** salary-bearing build output inside the git working tree — `build_staff_master.py` writes `staff_master.csv` beside itself in the repo's `attendance\` folder; one commit away from an F-31 breach. FIX before any commit: `.gitignore attendance/staff_master.csv`; RULE: salary-bearing generated files are git-ignored or produced outside the tree. **F-47 (S153):** biometric double-punch artefact — an accidental second punch minutes after arrival reads as a massive early departure; classify punch pairs (last−first ≤30 min = no real punch-out) before any money math. **F-48 (S153):** unobserved build-path write — a create_file race pre-applied a patch; rule: on any unobserved edit path, diff-audit against the last verified md5 before shipping. F-46 (S151): salary masking-by-detection failed twice → RULE: whitelist-only printing from salary-bearing files; never mask-by-exclusion. F-45 RESOLVED S149. (S152 minted none; wa_approve systemd conflict remains a verification task.)

Full text lives in the Archive session sections where each finding was raised/closed. Consolidated operational register: **Fault_Action_Register v2.16** (Tier 1; F-82+F-83 append owed → v2.17; **F-84 append owed — `Fault_Register_append_F84_S179.md`**).

---

## REGISTER VERSION LINEAGE (compact — replaces the prose CHANGELOG)

> The prose changelog was session-by-session narrative already held **verbatim in the Archive** (§S…). Only the Register's own version→session→date→headline lineage is provenance unique enough to keep; it lives here. **Full narrative for any version → Archive §S… · that version's own file-md5 → CANONICAL_MANIFEST §S… blocks.** (Pre-split v1.38–v1.72 were the old monolith's versions, now the Archive's content; carried here for continuity.)

| Register ver | session | date | headline |
|---|---|---|---|
| v5.3 | S181 | 16 Aug 2026 | the CLINIC module LIVE (six kits, five installs, final smoke 316/316 on the real store) via the NEW deploy chain (D317); owner redesign D318; KB-swap automation D319; housekeeping cleared (Fault Register v2.17 · Asset Register v1.11.0-R · first FULL cold kit since S171); UPI gap root-caused (F-91); F-90–F-95 |
| v5.2 | S180 | 15 Aug 2026 | the Marg pharmacy feed built offline end-to-end; sale returns made to reach the books; FOUR live installs (`finance_ingest` + `finance_app` replaced, 4 new modules, 1 view redefined, 1 table added, xlrd); D314–D316; F-85–F-89; four lost canonical docs recovered by hash, three closed as LOST; git kits committed |
| v5.1 | S179 | 15 Aug 2026 | one new live VPS subsystem: clinic-finance — Sanjeevni medical daily-revenue migrated off Google Forms, live + bank-reconciled; 121 legacy days imported; D313; F-84 (3 security faults fixed) |
| v5.0 | S178 | 14 Aug 2026 | COMPACTION — 752 → 500 lines zero-loss; three duplicated history forms cut; decisions index completed through D312; Asset KB refreshed v1.11.0; de-clutter to HISTORICAL |
| v4.6 | S177 | 14 Aug 2026 | Asset Register A-D24 wave LIVE v1.11.0 (smoke 342/0); housekeeping item 4 closed; … |
| v4.5 | S172 | 13 Aug 2026 | three portal subsystems BUILT & LIVE; go-live blocked vendor-side; D309–D312; F-82… |
| v4.4 | S171 | 12 Aug 2026 | the CONSOLE FINISHED: sweep signed off, nine installs across three files, Console … |
| v4.3 | S170 | 11 Aug 2026 | the rev5 punch-list EXECUTED: Items 1–8 + Track M all LIVE in one session; cron ar… |
| v4.2 | S169 | 11 Aug 2026 | Stage-2a agent attribution INSTALLED live in `console.db`; portal rev4 built + F-6… |
| v4.1 | S168 | 11 Aug 2026 | one live VPS file `portal.py` (D297 console page rev2 live, rev3 delivered) + one … |
| v4.0 | S167 | 11 Aug 2026 | one new live VPS builder `portal_console.py`; D297 Stage A A1·A2a·A2b·A3 built + p… |
| v3.4 | S161 | 09 Aug 2026 | two live VPS files: Staff Register onboarding features + Salary Engine Stage A; C-… |
| v3.3 | S160 | 09 Aug 2026 | one live VPS file `portal.py`; two design decisions): `portal.py` `679a0087…` → `8… |
| v3.2 | S159 | 08 Aug 2026 | one live VPS file `portal.py`; portal Group D + personal tiles + GMB moved to the … |
| v3.1 | S158 | 08 Aug 2026 | SSO portal built + rolled out LIVE end-to-end, Steps 1–6; Notion catch-up): Portal… |
| v3.0 | S157 | 07 Aug 2026 | documentation & design only; NO live code, config, trigger or property; no GitHub … |
| v2.9 | S156 | 07 Aug 2026 | backend salary automation built + live; F-51 UI safety; watchdog guards staff-ledg… |
| v2.8 | S155 | 07 Aug 2026 | Staff Ledger v2.4 (5 installs); D258 minted+EXECUTED; Darpan loan migrated live; r… |
| v2.7 | S154 | 07 Aug 2026 | new live VPS system (Staff Ledger) + service + OLS config; owner-side workbook v4;… |
| v2.6 | S153 | 07 Aug 2026 | attendance report layer rebuilt v2→v2.5 (six selftested versions), notice v6 shipp… |
| v2.5 | S152 | 06 Aug 2026 | no VPS/live code; one owner-side product file changed (the salary workbook gained … |
| v2.4 | S151 | 05 Aug 2026 | one NEW live VPS file `att_month_report.py`; `staff_master.csv` rebuilt; attendanc… |
| v1.72 | S146 | 14 Jul 2026 | one live VPS file `daily_digest.py` v1.5): Adds §S146, D246; no new finding (F-45 … |
| v1.71 | S145 | 14 Jul 2026 | two live VPS files replaced; the AI Verdict Layer Master written): Adds §S145, D24… |
| v1.70 | S144 | 13 Jul 2026 | one new live VPS file `flag_investigator.py` v1.1; two cron lines armed): Adds §S1… |
| v1.69 | S143 | 13 Jul 2026 | three live VPS files replaced (`verdict_review.py` v3, `call_verdict.py` F-40 fix,… |
| v1.68 | S142 | 13 Jul 2026 | one new VPS file `daily_digest.py` v1.2.1; crond restarted; `.env` +3 `DIGEST_` li… |
| v1.67 | S141 | 13 Jul 2026 | one VPS file changed: `call_verdict.py` v2.1): Adds §S141, D235–D237, findings F-3… |
| v1.66 | S140 | 12 Jul 2026 | Dashboard v18.28f, Callconsole v1.7, four VPS files + one systemd unit installed a… |
| v1.65 | S139 | 12 Jul 2026 | Dashboard v18.26→v18.27, Callconsole v1.6, relay v3, portal hotfix): Adds §S139, D… |
| v1.64 | S138 | 12 Jul 2026 | VPS code changed): Adds §S138, D217–D218, F-37, F-38. |
| v1.63 | S137 | 11 Jul 2026 | EOS-LIGHT — decisions + design only, NO code touched): Adds §S137, |
| v1.62 | S136 | 11 Jul 2026 | THREE Apps Script deploys v18.24/v18.25/+Callconsole v1.5, all |
| v1.61 | S135 | 11 Jul 2026 | two Apps Script deploys v18.22/v18.23, three PC files) |
| v1.60 | S134 | 11 Jul 2026 | two Apps Script files changed, deployed v18.21) |
| v1.59 | S133 | 11 Jul 2026 | one PC file changed, one VPS service installed, one repo commit) |
| v1.58 | S132 | 10 Jul 2026 | one live file changed: `Dashboard.html` → v18.20) |
| v1.57 | S131 | 09 Jul 2026 | consolidation pass 3 — still NO live code touched): Adds §S131.15–.17, D203, F-24,… |
| v1.56 | S131 | 09 Jul 2026 | EOS-light consolidation pass 2 — still NO live code touched): Adds §S131.12–.14, D… |
| v1.55 | S131 | 09 Jul 2026 | EOS-light consolidation — still NO live code touched): Adds §S131.11 and re-bases … |
| v1.54 | S131 | 09 Jul 2026 | NO live code touched): Adds §S131 and the companion AI Review Layer Design Specifi… |
| v1.53 | S130 | 09 Jul 2026 | one live Apps Script file changed: `WebApp.gs`): Adds §S130 and the companion Fron… |
| v1.52 | S129 | 09 Jul 2026 | EOS-LIGHT — no code changed, no file written, no trigger touched, no property set)… |
| v1.51 | S128 | 09 Jul 2026 | new live Apps Script file `Health.gs`; no VPS code, no `.env`, no restart): Adds §… |
| v1.50 | S128 | 09 Jul 2026 | EOS-LIGHT — no code changed, `.env` untouched, nothing restarted): Adds §S128. ⏸️ … |
| v1.49 | Ss125–127 | 09 Jul 2026 | `.env` written, service restarted, new VPS script): Folds in §S125 (dual-key recei… |
| v1.48 | S124 | 08 Jul 2026 | new VPS script + live dashboard file + live secret realigned): Added §124. Verdict… |
| v1.47 | S123 | 08 Jul 2026 | live VPS script replaced): Added §123. Stage-3 claim-match join REDESIGNED in `cal… |
| v1.46 | S122 | 07 Jul 2026 | new live VPS script + auth fix): Added §122. Stage-3 AI judge (`call_verdict.py`) … |
| v1.45 | Ss103–121 | 07 Jul 2026 | live PC-side code changed): Added §107 (S108 data-folder / Drive-sync evaluation —… |
| v1.43 | S101 | 07 Jul 2026 | EOS-light): Added §95–100 recording the S95–S100 |
| v1.42 | S95 | 07 Jul 2026 | EOS-light): FULL CONSOLIDATION. Folded v1.38 base + |
| v1.44 | S102 | 07 Jul 2026 | Added §102. FULL EOS — live PC-side code changed. Staff call-sheet de-duplication … |
| v1.41 | S94 | 07 Jul 2026 | Added §94. Two live fixes: call-webhook 403 outage |
| v1.40 | S93 | 06 Jul 2026 | Added §93. Track 1 Step 5 — PC-local Vitals & Plan |
| v1.39 | S75 | 05 Jul 2026 | Added §75. Track 1 Step 4 — PC-local write-path |
| v1.38 | S74 | 05 Jul 2026 | consolidation): Consolidated master. Carried the |
| v2.1 | S148 | 19 Jul 2026 | GitHub repo changed; canonical docs changed; no live/VPS code): Adds §S148 (full n… |
| v2.2 | S149 | 19 Jul 2026 | documentation only; no live/VPS code, no repo code): Register housekeeping complet… |
| v2.3 | S150 | 22 Jul 2026 | one Tier-2 frozen product changed under waiver; no VPS/live code): Adds D248; no n… |

*Post-split Register line = v2.0 (S147, the D247 split) → v5.0 (S178, compaction) → v5.1 (S179, finance subsystem) → v5.2 (S180, Marg feed + sale returns). v1.38–v1.72 = the pre-split monolith, now the KB History Archive.*


---

**END OF KB REGISTER v5.3 (S181). Current-state + index only; all session history is in KB History Archive v1.29 (§S65–§S180). If this end-marker or the CURRENT LIVE FILE VERSIONS table is absent, this file is truncated and must not be used as canonical.**
