# HANDOFF RUNBOOK — 11 July 2026 — Session 133 — v71
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: FULL EOS — one PC file changed (`push_followups_today.py` → D194 build), one VPS service installed (`wa-approve.service`), one repo commit (`84831b0`) pushed and hash-verified. No `.gs` file. No `Dashboard.html`. No D34 waiver. Supersedes v70.**

> **v71 — the bereaved family cannot be called tomorrow.** **D194 is BUILT, TESTED and LIVE**: the
> `Do_Not_Call` tab is the single enforcement point, the push script filters against it, and the live
> test removed exactly one real patient (122→121) and restored her (122). **F-20, `patient_deceased`,
> `number_invalid` CLOSED.**
>
> **The repo is an honest mirror again.** Commit `84831b0` closed **F-17, F-27, F-30, F-31** in one
> pass, every result verified from the published GitHub tarball by hash — F-17 turned out to be pure
> renames (the deployed content was already in the repo as `WebApp_v19_D189.gs`).
>
> **The last bare nohup is dead.** `wa_approve` runs under systemd (gunicorn, port 8101,
> `--timeout 300` for full LIVE batches), enabled, active, page verified through the proxy.
>
> **A-7 done — and it paid**: 15 installed triggers, `runIntradayDigest` ≈8×, `runSummaryEmail` 3×
> (**F-32**, duplication) and `runMorningReport` at **14.29% error rate** (**F-33**). Recorded, not
> fixed (D180).
>
> Owner directive all session: **AI-review-layer work parked** — A-00, A-0, A-1 never raised; **F-18
> parked with the layer.** New decision **D205** (seen-today WABA = session-start design, not an
> add-on). Correction: **the daily Docterz CSV is exported by the owner, not Shavez.**

---

## §0 — WHAT HAPPENED THIS SESSION

### 0.1 Phase 0/1 — nine matches, and the stale-export item closed by the owner
All nine canonical docs matched the S133 opener's hash table exactly (CR 0, end-markers, stale versions
absent). Mid-session the owner replaced `4.json`: the fresh export
(`Clinic_Callback_Tracker__4_.json`, **`523ddcbecc34cfe2c9a7ed6c7b3179ed`**, 15 files) carries
`WebApp` **`5173c3c7…`** and `Dashboard` **`a442bab5…`** — the deployed hashes. Every repo dashboard
file was byte-compared against it: 14/15 identical, `Health.gs` off by one trailing newline (fixed in
the commit below).

### 0.2 D194 — built from the verified artefact, proven on live data
Five guarded anchor edits on the triple-verified `fc0a731d…` source produced
**`push_followups_today.py` 19,497 b · 489 l · `7693a29a98dddbbdf01846fd139f5649`** (py_compile clean
on the PC, certutil-verified in place, rollback `push_followups_today_OLD_S133.py` beside it).
Safety contract: **tab missing → loud warning, push continues** (auto-creation was deliberately
rejected — a renamed tab must fail visibly, not be papered over); **tab unreadable → push refuses**;
unusable rows reported masked. Filter applies to `Followups_Today` only. Preview stays credential-free.
Live test: one real Due-Today patient in the tab → `--push` removed exactly her → row deleted → next
push restored the full 122. **Staff rule from today: deceased / wrong number / asked-not-to-call → one
row in `Do_Not_Call`. Nothing else to do.**

### 0.3 The repo hygiene commit — guarded batch, hash-verified from GitHub
`update_repo_S133.bat`: existence checks on every input; `att_config.py` renamed only after the
`CHANGE THIS` placeholder was proven present; the D194 file staged only after certutil matched
`7693a29a…`; the VPS-fetched `wa_send_api.py` accepted only after the live-only `logged=` marker was
found (F-27's own evidence, used as the check); review pause before commit. Git came from **GitHub
Desktop's bundled binary** (`%LOCALAPPDATA%\GitHubDesktop\app-3.6.2\resources\app\git\cmd`) — there is
no system git on the clinic PC.

Verified from the published tarball afterwards: **F-31** untracked + example template with placeholder
intact · **F-17** `WebApp.gs` = `5173c3c7…`, pre-change kept as `WebApp_PRECHANGE_ROLLBACK.gs`,
`.gs.gs` names fixed · **F-30** three watcher files in (`watch_and_push_followups.py`
`8561f3d75f986daf2fae1002e0e16856`) · **F-27** deployed `wa_send_api.py` in (`bc76e5cb…`) ·
`Health.gs` `9461d01b…` · D194 file in.

### 0.4 `wa_approve` — a service at last
Artefact facts first: bare `python3 wa_approve.py` since 05 Jul (PID 696717); port **8101** / host
127.0.0.1 pulled by **targeted grep** (never the whole env file — it holds `WA_APPROVE_KEY`); deployed
file = repo file (`c650f4c2…`, no drift). Unit **`e18048b2…`** (672 b) modelled on `wa-send-api`:
gunicorn `-w 1 -b 127.0.0.1:8101 --timeout 300` — **the 300 is load-bearing** (a LIVE batch may fire up
to `WA_DAILY_CAP` sends in one POST; a 30 s default would kill it mid-batch). The app self-loads
`wa_approve.env`; no `EnvironmentFile=` needed. Installed, enabled, **active, gunicorn on 8101**, page
verified through the OLS proxy with the day's file. Two operator notes proved out: `…/wa-approve/send`
answers *Method Not Allowed* to a typed URL (correct — POST-only); the keyed page URL was recovered
from browser history, never pasted to chat.

### 0.5 A-7 — the trigger inventory (F-32, F-33)
15 triggers, all time-based, all Head: `runIntradayDigest` ≈8× · `runSummaryEmail` 3× ·
`rebuildCallFeed`, `sendFollowupSummary`, `checkFollowupListFresh`, `runMorningReport`,
`dailyHealthReport` 1× each. **F-32** — duplication burns quota (Block C's currency) and may duplicate
digest emails; dedupe belongs beside A-5, whose functions (`removeTriggers`/`removeHealthTrigger`) are
the exact instrument. **F-33** — `runMorningReport` error rate **14.29%**, all others 0%;
the executions log names the exception at the next Apps Script session.

### 0.6 Decisions, corrections, re-scopes
- **D205** — patient-facing WABA features are designed at session start, never as late-session add-ons;
  the **seen-today section** of `wa_approve` is designed backlog (source = **the owner's** daily
  Docterz CSV; template + opt-out + dedupe + TEST wiring at design time). Nothing is broken — the page
  reads only the Call Sheet's five mapped buckets; seen-today patients were never in its design.
- **Correction to the working record:** the daily Docterz CSV export is done **by the owner, not
  Shavez**.
- **Index header corrected:** it still said *"Next free: D204"* after S132 spent D204. Now **D206**.
- **A-4 re-scoped:** F-11's fix is `Dashboard.html` **code** (sign-out button; strip `?k=`; clear
  `clinicDashKey`) → next Apps Script pass. The interim shared-device history-hygiene step was
  **parked by the owner to next session**.

---

## §1 — MENTAL MODELS

- **The `Do_Not_Call` tab is the only place suppression exists.** A flag anywhere else is overwritten
  before breakfast. Humans write it; code only reads it; a missing tab screams and a broken read stops
  the push.
- **A guard that can abort is worth ten instructions.** The S133 batch refused to run on a missing
  input, a missing placeholder, a wrong hash, a wrong file — and the owner typed almost nothing.
- **The deployed content may already be in the repo under the wrong name.** F-17 was renames, not
  uploads. Hash the candidates before shipping bytes.
- **Timeouts are sized to the workload, not the default.** `--timeout 300` exists because one POST can
  carry a hundred sends.
- **A ten-second screenshot can out-earn an hour of code.** A-7 produced F-32 and F-33.
- Every rule from v70 §1 stands: the judge proposes, the doctor disposes, the staff act · filing an
  outcome ≠ clearing a tile (`Staff Status` still has no writer) · no auto-responder exists (D204) ·
  a mirror is not the project · a repo path is not a disk path · expected values from the artefact
  (D172) · a filename is not provenance (D188) · presence by hashing, absence by exhaustion (D201) ·
  never write a command whose output is a secret (D176) · the `Call_Feed` publish URL and live `/exec`
  URL never enter chat.

---

## §2 — BACKLOG

> **Rotation: PARKED.** Do not open with a status check. **Health check: zero commands** — `Health.gs`
> emails at 09:00 IST; its *absence* is the fault. **AI review layer: PARKED by owner (S133)** — A-00,
> A-0, A-1, F-18 and all of Block A″ stay down until the owner re-opens them.

### 🔴 NEXT BUILD — one Apps Script pass, from the fresh export (no D34 waiver)
1. **A-3 remainder** — the L1128 `openThread` catch in `Dashboard.html`.
2. **A-5** — close `removeTriggers` (`Main.gs`) + `removeHealthTrigger` (`Health.gs`).
3. **F-32** — dedupe the 15 triggers (`runIntradayDigest` ≈8×, `runSummaryEmail` 3×) — same tools as
   A-5; do them together.
4. **F-33** — read the executions log for `runMorningReport`'s 14.29% error; classify before fixing.
5. **F-11 / A-4** — sign-out button; strip `?k=` after reading; clear `clinicDashKey`; optional expiry.
   Client-side only. *(Owner's interim step, parked to this session: clear `script.google.com` from
   shared-device browser history.)*
6. **A-6** — classify F-2's **sixteen** server `catch (e) {}` individually. Analysis only (D180).

### 🔵 REPO / RECORD (next git session — small)
7. Commit `wa-approve.service` into `wa-approve/` (only unit file of the set not in the repo).
8. **F-29's cure applies here too:** Frontend_Dashboard_Documentation **v2 is owed** (v1 describes
   pre-Fix-B `Dashboard.html`: `dataset.pat`, four-arg `inOpen`, packet-in-markup — all gone).

### 🟠 DESIGN (session-start, half-session)
9. **D205 — seen-today WABA section** on `wa_approve`: source = owner's daily Docterz CSV; template
   choice; opt-out + dedupe + send-log + TEST wiring equal to existing sections.

### 🟠 PARKED BY OWNER (do not raise; owner re-opens)
A-00 (D78 vs D195) · A-0 (call script + closing definition) · A-1 (the D34 question) · F-18
(`verdict_review.py`) · all Block A″ items (D191–D196, D193 writer flip, doctor's review section) ·
the 32 referee cards.

### 🟠 BLOCK C — make it cheap (precedes Block D, D185)
One clock (F-5, F-13) · stop whole-tab reads (F-6) · bundle the five follow-up calls (F-12) ·
`CacheService` 30–60 s · quota headroom into `Health.gs`. **F-32's dedupe is a down-payment on this.**

### 🟢 BLOCK D / E
D80 scope change (receiver stops skipping non-OBD) · delete `Probe.gs` (closes F-15's OAuth scope) ·
retire the dead ungated surface.

### Longer-running
Service-account key rotation (**Tier A1, Lokesh**) · AKEY_14 rotation · WABA authorizer recurrence
watch (D120, ticket 653584) · Stage 4 doctor portal · Track-1 Hindi spellings in `vitals_page.html` ·
venv Python 3.9 past EOL.

---

## §3 — DOCUMENT STATE *(re-based this session, per F-29's rule)*

| Document | Version | Bytes | Lines | md5 |
|---|---|---|---|---|
| `Clinic_Master_KB_SystemsRegister_v1_59.md` | **v1.59** | 304,272 | 3,082 | `ff4e917a5126a25ac0eac29ec5bb51e6` |
| `HANDOFF_RUNBOOK_2026-07-11_Session133_v71.md` | **v71** | *this file* | — | *stamped in the kit manifest* |
| `Dr_Manoj_Clinic_Umbrella_Architecture_v1_45.md` | **v1.45** | *see kit* | — | *stamped in the kit manifest* |
| `Clinic_Callback_Tracker_AppsScript_Audit_v1_4.md` | v1.4 *(unchanged)* | 31,542 | 331 | `7131df6075a65ea03459f39d1b087e08` |
| `Fault_Action_Register_v2_1.md` | v2.1 *(unchanged)* | 19,797 | 289 | `fde74c496a00826b504dc77b0c0c6cf6` |
| `Diagnostics_Surveillance_System_Spec_v2_1.md` | v2.1 *(unchanged)* | 53,441 | 871 | `7a9e83b436c39fde08118437acbbfafe` |
| `Call_Console_Evolution_Spec_v2_0.md` | v2.0 *(unchanged)* | 55,148 | 737 | `81e73349bb1318bea2df4cadaaeb6c47` |
| `AI_Review_Layer_Design_Spec_v1_1_S131.md` | v1.1 *(unchanged)* | 28,249 | 505 | `ad45a3af65188ed41391dca36175ce91` |
| `INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md` | v5 *(unchanged)* | 42,301 | 503 | `dc8d134fa8011aa3707d112f906342e6` |
| `Frontend_Dashboard_Documentation_v1_S130.md` | v1 *(one version behind — v2 owed)* | 20,850 | — | — |

**Live artefacts.**
- Apps Script export `Clinic_Callback_Tracker__4_.json` **`523ddcbecc34cfe2c9a7ed6c7b3179ed`**, 15
  files — `WebApp` `5173c3c7…` · `Dashboard` `a442bab5…` (v18.20). **Current with the deployment.**
- PC `push_followups_today.py` **19,497 b · 489 l · `7693a29a98dddbbdf01846fd139f5649`** (D194);
  rollback `push_followups_today_OLD_S133.py`.
- Sheet: **`Do_Not_Call`** tab live (`Phone · Reason · Set By · Set When · Note`), human-maintained.
- VPS `/etc/systemd/system/wa-approve.service` **`e18048b2b4901c2e182063b2f8f7d649`** — enabled,
  active, gunicorn `127.0.0.1:8101`. Deployed `wa_approve.py` = repo (`c650f4c2…`).
- Repo `main` head after S133: commit **`84831b0`** (11 files), contents verified by tarball hash.

**Next free decision number: D206. Next free finding number: F-34.**

---

## §4 — THE ROTATION PROCEDURE (D162) — PARKED
Unchanged from v70 §4. Steps 1–2 done; steps 3–4 parked; both keys burned; resume needs a **third**
key. **Do not raise unless the owner does.**

---

## §5 — SESSION HYGIENE NOTES

- No secret entered chat this session. The `wa_approve.env` read was a **targeted grep for
  PORT/HOST lines only** — the pattern for reading any file that also holds a credential.
- The wa-approve page key was recovered from the owner's **browser history**, used in the owner's own
  browser, and never typed into chat. It should now live in the owner's Apple Note beside the
  dashboard key.
- All phone numbers in every console output and every chat paste this session were masked to last-4 by
  the tools themselves (`mask_phone` in the push script; `mask` in `wa_approve`).
- The one *new* secret-adjacent artefact is `AUDIT_SHEET_ID` (future, Block A″) — unchanged note from
  v70: treat like `PATIENT_SHEET_ID`.
- `update_repo_S133.bat` and the S133 `Health.gs` extraction remain in `D:\Downloads` on the clinic
  PC; both are inert (the batch is single-purpose and re-runs safely — every step is skip-if-done).

---

**END OF RUNBOOK v71 — §5 is the last section. If §5 is absent, this file is truncated.**
