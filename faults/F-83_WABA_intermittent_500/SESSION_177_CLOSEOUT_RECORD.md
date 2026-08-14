# SESSION 177 — CLOSE-OUT RECORD (full EOS; ONE-OFF WABA INCIDENT SESSION)

**Date:** 14 Aug 2026 · **Type:** WABA/F-82 incident diagnosis + hardening (one-off; NOT the dev track).
**Scope note (owner-directed):** this session is closed as a **distinct standalone incident session**.
The main development track (Asset Register / S176 backlog and the three ideated S176 features) was
**not touched** and resumes at the next session exactly where S176 left it. As with S173–S176, this
record seeds the §S177 entries for the KB Register, KB History Archive, and Fault Register at the
**next full Phase-0 fold** (the S173→S177 doc-fold owed grows by one section). No clinic Tier-0/Tier-2
doc was edited this session.

---

## ⬛ EOS FINAL STATE
- **F-82 ROOT CAUSE PROVEN (evidence, not theory): MyOperator `/chat/messages` is INTERMITTENTLY
  faulty vendor-side.** Same server (93.127.195.49), same token, same payload: vendor Postman test
  SUCCESS 16:37 IST → our sends 9/9 SUCCESS ~19:15 IST (3 transports × 3 trials, incl. the ORIGINAL
  un-patched code) → **every send FAILS from 19:49 IST onward** (19:49 / 20:05 / 20:34 runs, plus a
  **different recipient** at ~20:12) — HTTP 500, body `{"message":null}`. The weeks of "persistent 500"
  behind F-82 were this intermittency caught in bad windows.
- **Panel-vs-API contradiction documented (owner-verified ~20:30 IST):** wallet balance sufficient ·
  template `drmanoj_post_visit` approved/active · WhatsApp number 9358008080 quality **HIGH** ·
  service **live** — while the API 500s. Account side fully exonerated.
- **Code hardening SHIPPED (the one change the evidence supports):** `waba.py` retry-on-5xx.
  `ceeb0e2361a1f7ca5bc337e10ebb06f1` → **`031b46429c08832922d7a08d3a33a87f` LIVE**; 7-line guarded
  edit inside `send_template()`'s HTTPError branch; fatal CHAT-codes still raise instantly, 4xx not
  retried, success path unchanged. Built from an md5-proven byte-identical reconstruction of the live
  original (D160/D188 honoured); 5/5 mocked behaviour tests passed offline; VPS `py_compile` OK;
  `wa-approve.service` restarted, active.
  *(An interim User-Agent patch `5961f9b7…`, made on a disproven theory, was REVERTED to the canonical
  original before the real fix — canon never carried an unjustified line.)*
- **NEW permanent instrument: `/root/wa/waba_diag.py`** (`b560d12d0385cef39de347ddd62bffef`).
  One command = config check → N live trials through the REAL code path → verdict
  (HEALTHY / DEGRADED / DOWN / FATAL / CONFIG) → ready-to-forward **escalation pack** (timestamps,
  IP, IDs, masked token, per-failure bodies, reference payload). Exit codes 0/1/2. Proved itself on
  first run by catching the live 19:49 DOWN window. This is the standing SOP: **check swiftly →
  rectify if ours → escalate with complete context.**
- **Escalation sent:** full evidence email (timeline + cross-recipient proof + panel contradiction +
  gateway-log request for 19:49–20:35 IST + the `{"message":null}` no-error-code defect called out)
  from owner's personal email to Khushi, CC Lokesh.

## 0. What happened (compressed narrative)
1. Khushi (MyOperator) supplied a working Postman curl for `/chat/messages` → reproduced 200 from our
   VPS. 2. Live `waba.py` path returned 500 → three single-shot theories chased in turn (stale token /
   header case-mangling / User-Agent) — **each disproven**: token proved byte-identical via heredoc
   file compare (shell-paste corruption produced one false comparison first); `http.client` verbatim
   headers got 200 once, but 3. the **repeated-trials certainty harness** (3 transports × 3 trials,
   sandbox-tested with mocks before shipping) returned **9/9 including the untouched original code**
   → verdict: vendor-intermittent, all single-shot theories were sampling noise. 4. UA patch reverted;
   retry-on-5xx built offline from provenance-proven source, unit-tested, installed, service
   restarted. 5. `waba_diag.py` built (5 verdict paths mock-tested), installed — first live run caught
   a real DOWN window (19:49); still DOWN 20:05, 20:34. 6. Cross-recipient test (owner's number) also
   500 → ruled out per-recipient throttle from the day's ~15 test sends. 7. Owner panel-verified
   wallet/template/quality/service all green. 8. Evidence email assembled + sent.

## 1. Decisions minted (clinic scope; full text to Archive §S177 at fold; next-free after = **D315**)
- **D313 — Repeated-trials rule for vendor-API faults.** No code change may be justified by a
  single-shot success/failure against a vendor API suspected of intermittency; require an N-trial
  harness across candidate configurations (include the UNCHANGED baseline as control) before touching
  canon. Rationale: three plausible root-causes were "confirmed" by single shots today and all were
  noise; the original code was never broken.
- **D314 — `waba_diag.py` is the standing WABA health/escalation SOP.** Any WABA misbehaviour: run
  `/root/wa/venv/bin/python3 /root/wa/waba_diag.py` first. HEALTHY → blip (retry layer rides it).
  FATAL → account issue (panel/Khushi). DOWN/DEGRADED → forward the printed pack to Khushi/Lokesh.
  `--dry` = config-only; `--trials N` = deeper. Each live trial sends a real WhatsApp to the test
  number — rotate/confirm the test number with Lokesh if running bursts.

## 2. Findings minted (to Fault Register at fold; next-free after = **F-85**)
- **F-83 — MyOperator `/chat/messages` intermittent 500 `{"message":null}` (vendor).** Identical
  request succeeds/fails purely by time window; documented up→down cycle 19:15→19:49 IST 14 Aug.
  Sub-defect: gateway strips its own CHAT_xxxx error codes in these failures (null body), which
  (a) blinded our fatal-code detection and (b) turned a diagnosable fault into weeks of F-82 mystery.
  Reported to vendor in the escalation email. **F-82 remains OPEN** (go-live still vendor-blocked)
  but is now correctly characterised: intermittent, not persistent; account state green.
- **F-84 — Shell paste is not a data channel for secrets/comparisons.** A quoted `VAR='token'` paste
  silently truncated to 23/42 chars and produced a false "tokens differ" result; heredoc-to-file was
  required for a trustworthy compare. Extends the WinSCP-paste-corruption lesson to interactive shell
  arguments: transfer or heredoc, never inline paste, for anything whose bytes matter.

## 3. PENDENCY / carry-forwards (open at S177 close)
- **F-82 OPEN — go-live still vendor-blocked**, now with the vendor holding a precise evidence pack.
  Await Khushi/Lokesh root-cause reply. **Morning check:** run `waba_diag.py`; if DOWN, forward the
  fresh pack (keeps pressure with zero effort). If HEALTHY across a few days → go-live steps resume
  (DRYRUN→"0", self-send) per S172 plan.
- **⚠ TOKEN ROTATION (elevated):** the current WABA Authentication token (…wWHn) was exposed in
  plaintext in WhatsApp (by vendor) and in this chat. **Rotate with Lokesh** once sends are stable —
  never unilaterally (rotation breaks panel automations ~24 h; standing rule).
- **`wa_send_api.py` (port 8096) NOT yet hardened** — separate sender, own POST path (already uses
  numbered body); assess retry-on-5xx parity next time that flow matters.
- **Repo commit owed grows:** `waba.py` (retry) + `waba_diag.py` (new) join the S162–S176 commit
  backlog (both env-driven, no secrets — safe to track). §5 has the message.
- **Courtesy:** Lokesh's number received ~15 test messages today (incl. a 9-message burst) — a
  one-line apology/heads-up in the escalation thread is good vendor hygiene.
- **Unchanged carry-forwards:** asset-app git kit + `/api/due` token rotation (owner actions);
  service-account key rotation (Tier A, overdue); doc-fold §S173→**§S177** owed at next full Phase 0;
  the S176 dev backlog (Asset Phase B remainder + three ideated features + four open decisions).

## 4. Live-file ledger (this session)
| File | Before | After | State |
|---|---|---|---|
| `/root/wa/waba.py` | `ceeb0e23…` (canonical) | **`031b46429c08832922d7a08d3a33a87f`** | LIVE (retry-on-5xx); interim `5961f9b7…` reverted; `.bak.20260814_172324` = original |
| `/root/wa/waba_diag.py` | — | **`b560d12d0385cef39de347ddd62bffef`** | NEW, LIVE |
| `/root/wa/waba_certainty.py` | — | `aa0734986b12ab8d63edbf44bfc698a0` | one-off harness; superseded by waba_diag; may delete |
| `wa-approve.service` | — | — | restarted, active |

## 5. Repo commit message (owner pastes, GitHub Desktop; pull both files off VPS via WinSCP first)
```
Session 177 (one-off): WABA F-82 root-caused as vendor-intermittent; retry + diagnostics

- wa/waba.py: retry-on-5xx with backoff in send_template() (proven transient
  vendor 500s, {"message":null}); fatal CHAT-codes still raise instantly;
  4xx and success paths unchanged. ceeb0e23 -> 031b4642.
- wa/waba_diag.py: NEW one-command WABA health check -> verdict -> ready-to-send
  escalation pack (timestamps, masked token, per-failure bodies). Standing SOP D314.
- Docs: SESSION_177_CLOSEOUT_RECORD + incident report (D313/D314, F-83/F-84);
  Register/Archive/manifest fold owed at next Phase 0 (S173-S177).
```

## 6. Provenance / integrity
- Every edit built from md5-proven sources: `waba.py` reconstructed byte-identical to the live
  original (`ceeb0e23…` match) before patching; assert-once anchors on every replacement; offline
  `py_compile` + mocked behaviour tests (5/5 retry cases; 5/5 diag verdict paths) before any install;
  VPS md5 verified after every transfer (one WinSCP re-drag caught by a missing-file check).
- Secrets: token never printed by any tool (len+last-4 only); the plaintext exposures were vendor-
  and paste-side, logged above for rotation. No PHI touched; test sends used staff/vendor numbers only.
- Wrong turns are recorded, not erased: three disproven single-shot theories and one interim reverted
  patch are part of the narrative — they are exactly why D313 exists.

**END OF SESSION 177 CLOSE-OUT RECORD.**
