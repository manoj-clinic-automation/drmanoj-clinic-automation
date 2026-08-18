# HANDOFF RUNBOOK — 10 July 2026 — Session 132 — v70
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: FULL EOS — one live file changed: `Dashboard.html` → v18.20. No `.gs` file. No D34 waiver. No VPS service edited. Supersedes v69.**

> **v70 — the button works.** **F-8 is CLOSED.** Fix B: the patient packet lives in a page-level map,
> the button carries a slot id. **F-14's two `JSON.parse` catches removed** — *including the one that
> would have reported F-8 and instead hid it.* **Block E's "stop embedding patient data in button
> markup" delivered.** Verified live on two known-patient tiles.
>
> **MyOperator is cleared.** `GET /chat/templates` 200 · `POST /chat/messages` 200 Accepted · template
> **delivered to the doctor's handset**. Outage 05 Jul 01:19 → recovered by 09 Jul 16:53, on a relay
> **unrestarted since 26 June**. Nothing on the clinic's side changed.
>
> **D204** answers **A-000**: D113 is intent, not fact. **No auto-responder exists and none is scheduled.**
>
> **Four assertions were made from unread artefacts and all four were wrong** (§0.7). **F-26 and F-28
> are WITHDRAWN.** New: **F-27, F-29, F-30, F-31.**

---

## §0 — WHAT HAPPENED THIS SESSION

### 0.1 Phase 0 — and the mirror that was not the project
Nine of ten canonical artefacts matched the opener's hash table exactly. The Runbook was missing from
the assistant's **file mirror** and was uploaded. Then the Umbrella vanished from the mirror while the
**project-knowledge search index still returned its contents.**

**The mirror is a snapshot taken at conversation start. The search index is live.** An absence asserted
from the mirror is an absence asserted from a stale disk — **D201, which already says the manifest is
one of the places you must exhaust.** The Umbrella was verified against the repo copy (`b1c6c414…`,
byte-identical). Repo `dashboard/WebApp.gs` re-hashed `276dc197…`: **F-17 confirmed open.**

### 0.2 F-8, killed
Eight anchored edits to `Dashboard.html`, every anchor asserted unique, **seventeen lines changed.**
`IN_PAT` map keyed by slot id · L912 stashes, does not stringify · L923 carries `(slotId, digits, bool)`
· **L1260 dead parse + catch deleted** (`pat` was never used) · **L1262 `dataset.pat` deleted** ·
**L1364 `inSave` reads the map** — the second catch dies. `catch(e){}` **16 → 14**; **L1128 is A-3's
entire remainder.**

**Proved, not asserted.** The escapers were re-implemented in node against `Ram D'Souza`: the browser
receives `inOpen('in_9812345678_0','9812345678',true,'{`, which does not compile — exactly as Audit v1.2
predicted in S129. `node --check` clean.

**Verified live.** `8218401104` (Neeta Agarwal) and `9411222492` both opened **straight to Reason →
Resolution**, skipping *"Who is this?"* — the `known===true` path, which had never executed.
`1409801539` (*"Not in patient list"*) still opens the identify-caller card. Nothing saved.
**D190's two `non_patient` rows are undisturbed.**

**Deployed as v18.20**, existing deployment → New version. `/exec` unchanged. Rollback = redeploy prior.

### 0.3 The tile still does not clear — and that is correct
**Nothing in this project has ever written `Callbacks_Today.Staff Status`.** A working button logs; it
does not remove. That is **D195**, and it is behind **A-1**.

### 0.4 MyOperator cleared, with a defensible timeline (D120)
Support asked for *"a screenshot of the error"* — of a server-to-server API call. Three token-guarded
probes were built (`waba_probe.sh`, `waba_template_test.py`, `waba_recovery_window.sh`; all read-only or
dry-run by default; the token is read from `.env`, used, never printed, and every output is scanned for
it before display).

| Fact | Evidence |
|---|---|
| `GET /chat/templates` → 200 | 10 Jul 18:46 IST, 14 templates |
| `POST /chat/messages` → 200 Accepted | 10 Jul 19:04 IST, `message_id c9130529-…` |
| Delivered to handset | 19:06 IST |
| Outage began | 05 Jul 01:19, `AuthorizerConfigurationException`, req `eb82db53…` |
| First success after | **09 Jul 16:53:05** (`http=200`) |
| `wa-send-api` last start | **26 Jun 20:56 — unrestarted throughout** |

9,115 journal lines exist from 05 Jul, so the gap is **absence verified by exhaustion**: no send was
attempted. `wa_approve.py` started 05 Jul **01:05**; the owner emailed support at **01:19**.
`waba.py` **is** the tracker's send arm and does call the public API. **The ticket's impact claim stands.**

### 0.5 The tracker reconciled against the repo
**38 of 40 code files byte-identical. Zero repo files absent from the PC.**
**`push_followups_today.py` identical across PC manifest, upload, and repo — 16,600 b · 428 l ·
`fc0a731d38482eb90b7d2def135c92b6`.** `Do_Not_Call` may be built on it.
The repo mirrors `followup-tracker/` honestly. It does **not** mirror `dashboard/` (F-17) or
`wa-send/` (F-27).

### 0.6 Findings
- **F-27** — repo `wa-send/wa_send_api.py` is not the deployed file. Live logs print `logged=True`;
  the repo file never emits it. Same class as F-17.
- **F-29** — **Runbook v69 §3 was never re-based.** It named KB v1.54, "this file, v66", Umbrella v1_41,
  and "next free D202" — all stale. §0 and §2 were correct. **Only the section that says where we
  stopped was wrong.** *This file's §3 is written to end that.*
- **F-30** — `watch_and_push_followups.py` (8,439 b), `start_followup_watcher.bat`, and
  `SETUP_followup_watcher_autostart.txt` exist **only** on the clinic PC. The morning push has no backup
  but one Windows disk. It already has an incident to its name (01 Jul).
- **F-31** — `attendance/att_config.py` is tracked in the **public** repo. `.gitignore` names it twice
  and says *"NEVER commit."* **Git ignores that rule for files it already tracks.** **Nothing is exposed
  today** — live `DASHBOARD_PASSWORD` (12 ch) ≠ repo's placeholder (20 ch, `# <-- CHANGE THIS`); live
  `SMTP_PASS` (16 ch) vs repo **empty**; live `SECRET_KEY` (64 ch) **absent from repo**. Compared by
  hashing **values**, never printing one. **The danger is prospective: the guard is disarmed for the day
  someone copies the live file in.** No `.env`, `*.csv`, or service-account key exists anywhere in the
  326 repo entries — verified against the published tarball, not against the rule.
- ⛔ **F-26 WITHDRAWN** — the relay logs every outcome; the grep looked for `" 200` against a file that
  writes `http=200`. ⛔ **F-28 WITHDRAWN** — `wa_approve.py` writes a CSV and to `wa_approve.out`.

### 0.7 The session's own failure mode, counted
**Four assertions from unread artefacts, all wrong:** F-26 (grep, not read) · F-28 (grep, not read) ·
`/root/wa/wa-send/wa_send.py` (**a repo folder name used as a disk path**) · F-31 first draft (the
*tracker's* two-line `.gitignore` characterised as the *repo's* eighty-two-line one).

**S131 made three lineage errors and wrote D190, D201, D202 about them. S132 opened by reciting the rule
and made four more.** No decision is minted — **the rules exist and were violated.**

> **A grep, a path, and a filename all feel like evidence. None of them is an artefact.**

---

## §1 — MENTAL MODELS

- **The judge proposes. The doctor disposes. The staff act.**
- **A false bounce costs one phone call. A false settle is invisible.**
- **Filing an outcome ≠ clearing a tile.** `Staff Status` has no writer and never has.
- **Stop passing data through markup.** `IN_PAT` is the pattern; F-10's other 23 sites should follow it.
- **The dashboard cannot act on the patient DB or the follow-up source.** A flag anywhere but
  `Do_Not_Call` is overwritten before breakfast.
- **No auto-responder exists (D204).** During an outage, read the journal.
- **A mirror is not the project. A repo path is not a disk path. A grep that cannot match is not a search.**
- Every rule from v69 §1 stands: expected values from the artefact, never memory (D172) · a filename is
  not provenance (D188) · presence by hashing, absence by exhaustion (D201) · a count without scope is a
  wall (D179) · a label states its contents (D178) · a check must be calibrated to its artefact (D177) ·
  an audit finds, it does not fix (D180) · `UNKNOWN` is valid (D166) · never write a command whose output
  is a secret (D176) · the `Call_Feed` publish URL and the live `/exec` URL never enter chat or a screenshot.

---

## §2 — BACKLOG

> **Rotation: PARKED.** Do not open with a status check. **Health check: zero commands** — `Health.gs`
> emails at 09:00 IST; its *absence* is the fault.

### 🔴 BLOCK A — gates (unchanged; ask before proposing work)
**A-00 — RECONCILE D78 AGAINST D195.** D78 (S53, Call Console §F): 3rd strike → bottom band, WABA
template, snooze X days, **cross-day miss counter**. D195 (S131): 3rd attempt → the doctor. **Both
designs. Neither built.** *Assistant's read: they answer different questions and can be merged — D78's
cross-day counter and band for a patient who cannot be reached, D195's escalation as the 4th strike,
WABA template deferred (needs Lokesh). **Owner's clinical call.***

**A-0 — TWO OWNER INPUTS GATE AXIS 3.** The **call script** (Hindi) and the **definition of a complete
closing**. Until they arrive, `script_not_followed` and `no_closing` are specified and **inoperable**
(D199, `UNKNOWN` per D166). *If no written script exists, that absence is the finding.*

**A-1 — THE D34 QUESTION.** `saveIncomingOutcome` (L1233), pending builder (L247), `getFollowups`
(L925+), `sendBackToStaff` (L1502), `getEscalations` (L1373) all live in `WebApp.gs`. **Nothing
server-side ships without this answer.** *Assistant's read: answer (a) in principle, then spend the
waiver one bounded edit at a time, each verified against a fresh export.*

### 🔴 BLOCK A′ — ships with no waiver, no owner input
1. **`Do_Not_Call` tab (D194).** One tab (`Phone · Reason · Set By · Set When · Note`) + one filter line
   in `push_followups_today.py` (**verified: `fc0a731d…`**). Closes `patient_deceased`, `number_invalid`,
   **F-20**. **A bereaved family can still be called tomorrow. This is the next build.**
2. **F-18** — `verdict_review.py` must stop printing overturned **D153** and excusing 19 incoming calls.
   No count from that layer is trustworthy until it does.
3. **A-3 remainder** — the L1128 `openThread` catch. *(L1260, L1364 closed S132.)*
4. **A-5** — close `removeTriggers` (`Main.gs`) + `removeHealthTrigger` (`Health.gs`).
5. **A-4** — Sign out; strip `?k=` from the address bar (**F-11** — cheapest security return on the list).
6. **A-6** — classify F-2's **sixteen** server `catch (e) {}` individually. **Never one commit (D180).**
7. **A-7** — the Triggers screenshot. Ten seconds.

### 🔵 REPO / RECORD HYGIENE (next git session)
8. **F-31** — `git rm --cached attendance/att_config.py`; rename the template `att_config.example.py`.
9. **F-30** — commit `watch_and_push_followups.py`, `start_followup_watcher.bat`,
   `SETUP_followup_watcher_autostart.txt`. **They exist on one disk.**
10. **F-17** — repo `dashboard/WebApp.gs` → the deployed file; pre-fix copy renamed
    `WebApp_PRECHANGE_ROLLBACK.gs`. Fix `CallField.gs.gs` / `Probe.gs.gs`.
11. **F-27** — commit the deployed `wa_send_api.py`.
12. **`wa_approve` → a systemd unit.** It is a bare `nohup` PID, up since 05 Jul 01:05. **It dies on
    reboot, and `Health.gs` does not watch it because it is not a service.**

### 🟠 BLOCK A″ — the AI review layer (after A-0 and A-1)
13. PROVISION columns on `Call_Verdicts` (a provenance column **not** named `Source`). 14. Stable case
identity (D196). 15. Tile-removal contract (D195). 16. `AUDIT_SHEET_ID` + `Doctor_Verdicts` writer flip
(D193). 17. Doctor's review section, **Phase 1 only** (D191). 18. Phase 2 stays shut until 100 refereed
cards clear the bar.

### 🟠 BLOCK C — make it cheap (precedes Block D, D185)
19. One clock (server `todayIST`; closes F-5, F-13). 20. Stop whole-tab reads (F-6). 21. Bundle the five
follow-up calls (F-12). 22. `CacheService`, 30–60 s. 23. Quota headroom into `Health.gs`.

### 🟢 BLOCK D / E
24. The **D80 scope change** (ex-F-19): the receiver stops skipping non-OBD calls. **Amends a decision;
does not fix a bug.** 25. Delete `Probe.gs` (closes F-15's OAuth scope). 26. Retire the dead ungated
surface.

### Longer-running
Service-account key rotation (**Tier A1, Lokesh**) · AKEY_14 rotation · WABA authorizer fault
(**D120 — cleared today; watch for recurrence**) · Stage 4 doctor portal · Track-1 Hindi spelling in
`vitals_page.html` · **venv Python 3.9 is past end-of-life** (google-auth warns on every run) ·
Referee the 32 cards in `Verdict_Review` — **or let D191's dashboard clicks build the ledger instead.**

---

## §3 — DOCUMENT STATE *(re-based this session; F-29 exists because this section was not)*

| Document | Version | Bytes | Lines | md5 |
|---|---|---|---|---|
| `Clinic_Master_KB_SystemsRegister_v1_58.md` | **v1.58** | 290,945 | 2,927 | `523a26312c9edd26d5498b1f73cff287` |
| `HANDOFF_RUNBOOK_2026-07-10_Session132_v70.md` | **v70** | *this file* | — | *stamped in the kit manifest* |
| `Dr_Manoj_Clinic_Umbrella_Architecture_v1_44.md` | **v1.44** | 65,400 | 696 | `cda6b327e5d544f36d62924620d511a4` |
| `Clinic_Callback_Tracker_AppsScript_Audit_v1_4.md` | **v1.4** | 31,542 | 331 | `7131df6075a65ea03459f39d1b087e08` |
| `Fault_Action_Register_v2_1.md` | **v2.1** | 19,797 | 289 | `fde74c496a00826b504dc77b0c0c6cf6` |
| `Diagnostics_Surveillance_System_Spec_v2_1.md` | **v2.1** | 53,441 | 871 | `7a9e83b436c39fde08118437acbbfafe` |
| `Call_Console_Evolution_Spec_v2_0.md` | v2.0 *(unchanged)* | 55,148 | 737 | `81e73349bb1318bea2df4cadaaeb6c47` |
| `AI_Review_Layer_Design_Spec_v1_1_S131.md` | v1.1 *(unchanged)* | 28,249 | 505 | `ad45a3af65188ed41391dca36175ce91` |
| `INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md` | v5 *(unchanged)* | 42,301 | 503 | `dc8d134fa8011aa3707d112f906342e6` |
| `Frontend_Dashboard_Documentation_v1_S130.md` | v1 *(unchanged)* | 20,850 | — | — |

**Live artefacts.** `Dashboard.html` **v18.20**, md5 `a442bab52eab7898d1b2e692403f987b`, 157,703 b,
2,741 l, CR 0 — built from export `034529a1…`. **`WebApp.gs` untouched: `5173c3c7…`.**
Apps Script export `4.json` `449f3fe6981c2b75dfac0437126ece59` is now the **pre-Fix-B** snapshot.
**A fresh export is owed at the next Apps Script session.**

**Next free decision number: D205.**

---

## §4 — THE ROTATION PROCEDURE (D162) — PARKED
Unchanged from v69 §4. Steps 1–2 done; steps 3–4 parked; both keys burned; resume needs a **third** key.
**Do not raise unless the owner does.**

---

## §5 — SESSION HYGIENE NOTES

- Secrets are never displayed. The `Call_Feed` publish URL, the live `/exec` URL and the WABA bearer
  token never enter chat, doc, or screenshot. `.env` backups are mode-600 secrets; do not delete.
- **Credentials were compared this session by hashing their VALUES, never printing them.** A value hash
  answers *"are these the same secret?"* and tells nobody what the secret is. **This is the pattern.**
- **One masking failure occurred.** A `journalctl … | head -1` was issued without the `sed` mask used on
  the line above it, and printed one patient's full mobile number to the terminal. Caught immediately and
  flagged to the owner. **Every command that touches a log must carry the mask, not most of them.**
- Three new read-only scripts live in `/root/wa`: `waba_probe.sh`, `waba_template_test.py`,
  `waba_recovery_window.sh`. **`waba_template_test.py` sends a real WhatsApp when given `--send`.**
  It is dry-run by default and its only destination is the owner's own number.
- **`AUDIT_SHEET_ID` will be a new script property.** An ID, not a credential — but the Call Audit sheet
  carries full patient numbers (D152). Treat it like `PATIENT_SHEET_ID`.

---

**END OF RUNBOOK v70 — §5 is the last section. If §5 is absent, this file is truncated.**
