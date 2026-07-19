# HANDOFF RUNBOOK — 08 July 2026 — Session 126 — v60
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: BUILD (live code changed; no restart, no key touched). Supersedes v59.**

---

## §0 — WHAT HAPPENED THIS SESSION

Session 126 was convened to rotate `CALLHOOK_SECRET`. **The key was not touched.** Not one byte of `.env` was written. Nothing was restarted.

Instead, the session did the housekeeping that Runbook v59 placed before the rotation — and the housekeeping kept finding that the written record was wrong. Six data-safety measures were run before any file moved. Five recorded facts failed against the disk. One secret nobody had mentioned turned up in `.env`. One latent trap, of exactly the class D164 exists to prevent, was found armed inside the git configuration of the machine that uploads code to the VPS.

The rotation is unstarted, the clinic is healthy, and the box is in a better state than it was at 21:00.

### The opening integrity check — and a fifth truncated document

Session 125's close-out is known to have shipped four truncated documents. Session 126 checked the three it was told to read.

- `HANDOFF_RUNBOOK_2026-07-08_Session125_v59.md` — **intact.** Reaches §7, last bullet present.
- `INCIDENT_2026-07-08_CALLHOOK_403_RECURRENCE_v2.md` — **intact.** Reaches `## 9.` and its closing note.
- `KB_APPEND_Session125.md` — **TRUNCATED.** Ends mid-sentence inside §3, at *"…it currently reports 'MyOperator is not delivering at all' for any date"*. Missing: the third §12 replacement, the one §12 addition, and the changelog line. **A fifth casualty.**

§1 (the §S125 section) and §2 (D162–D165) are complete, so the D-series is safe and **the next free decision number was correctly D166.** The procedure was NOT reconstructed from memory. The KB was NOT bumped to v1.49. The truncated block is quarantined.

**A numbering gap was found.** `Clinic_Master_KB_SystemsRegister_v1.48.md` carries decisions **D121–D160** and states *"next free decision number for new work: D161."* `KB_APPEND_Session125.md` §2 is headed *"append after D161."* **D161 exists in neither document.** Either it was minted in S125 and lost, or "append after D161" is an off-by-one. Unresolved. Does not block anything.

### The six data-safety measures, and what each one broke

**DS-1 · Baseline, read-only.** Watchdog at 21:20 IST: `133 accepted (200) / 635 rejected (403)`, last 403 still `10:28:02`, `keys seen : key_271f88` — **one label**, wire format. No new rejections in eleven hours. WARN `CALLHOOK_403_EARLIER_TODAY`, `exit=1`, which is the expected signature of a fault already fixed.

Journal: `secret gate: ON  current=key_db8972  previous=(unset)`. Literal-format label. `.env` and the running worker agree.

**The 115-vs-114 gap resolved into something smaller.** At 14:11 it was 115 accepted / 114 raw-log lines. At 21:20 it is **133 accepted / 132 lines. The offset is still exactly one.** Eighteen further deliveries, eighteen further lines. A mechanism that was still running would have widened the gap. **It is one historical event, not an ongoing defect.** Bounded. Still unexplained, but it drops from "the receiver is silently dropping data" to "one anomalous 200 on 08 Jul."

**DS-2 · `.env` backed up.** `/root/wa/.env.bak_s126_20260708_212316`, 1416 bytes, mode 600, `cmp` silent, `CR = 0`.

`cp -a` preserved the mtime: **`08 Jul 10:28`**. The worker respawned at `10:28:33`. The 10:28 edit and the 10:28:33 restart were one deliberate act — the S124 repair — and `last 403 : 10:28:02` stops thirty-one seconds before it. **`.env` has not been written since.** Disk and worker memory provably agree, now established three independent ways: the startup label, the wire label, and the mtime.

**DS-3 · The live `call_hook_capture.py` backed up — and the record failed.**

Runbook v59 §7 warns that the S125 `.bak` was taken *after* v2 replaced v1, so it is a copy of v2 and "not a rollback point." True as far as it goes. The practical consequence is better: it is a **valid rollback point to v2**, just not to v1. Verified by `cmp`: `call_hook_capture.py.bak_20260708_144241` and `call_hook_capture.py.LIVE_v2_s126_20260708_212453` are **byte-identical**. Two rollback points to v2. Zero to v1 on the box; v1 lives in GitHub and the cold kit.

**The live file is 30,749 bytes, not the 30,750 carried in every document.** `wc -l` = 690. Final byte confirmed `\n` by `od -c`, so the file terminates properly and the missing-newline hypothesis is dead. **The record was simply wrong by one, and had been repeated for sessions.** Because the repo's `31,100` came from the same record, the claimed 350-byte delta was unverified in both directions. It was measured, not trusted. **The true delta is 351.**

**DS-4 · The forensic `.env` backup — and the "lost newline" explanation died.**

`/root/wa/.env.bak_20260707_162509`: present, `mode=600` (tightened), **1327 bytes, 29 lines**, mtime `2026-07-07 16:25:09`. Genuinely pre-repair. All three `.env`-family files are 600; no world-readable secrets.

Key names and value lengths were printed — never values. The file shows:

```
CALLHOOK_SECRET          len=61
FU_UPLOAD_SECRET         len=32
```

**`FU_UPLOAD_SECRET` is present, on its own intact line.** A lost newline *merges* two lines; it consumes the second. That line survived. **Therefore the 61 characters arrived by DUPLICATION — text inserted, nothing deleted.**

- **Settled:** the composition. `12 (@ key) + 17 ("FU_UPLOAD_SECRET=") + 32 (alnum value) = 61`, non-alphanumerics `@ _ _ =` in exactly that order.
- **Unknown:** the mechanism. A `sed` overrun, a stray append, an editor, a botched heredoc paste — all produce insertion-without-deletion. **The evidence distinguishes none of them.**

This is the **third** explanation offered for these 61 characters. Incident report v1 said `sed` caused it (retracted, S125). S125 said a lost newline caused it (retracted, S126). Both were asserted without anyone opening the file. **Record no third cause.** See D166.

**A prediction failed, and is recorded rather than dropped.** This assistant predicted the forensic file at ~1465 bytes, larger than the live 1416. It is 1327 — *smaller*, by 89. The sign was wrong: a lost newline removes a byte, it does not add bulk. The deeper error was comparing the sizes of two files that differ in more than one place and attributing the difference to the one line under discussion. The `12+17+32=61` reconstruction rests on the *value's* length and character order, not on file size, and is unaffected.

**`ANTHROPIC_API_KEY len=111` is in the live `.env`.** Absent from the 07-Jul backup, so it was added between `07 Jul 16:25` and `08 Jul 10:28` — **inside the outage window.** Mode 600, so not an emergency. But something appended to `.env` during the incident and it is recorded nowhere; the gunicorn call-webhook worker now loads an Anthropic credential it has no use for; and it belongs on the rotation backlog.

**Six bytes unaccounted.** `1416 − 1327 = +89`. The new `ANTHROPIC_API_KEY` line (+130), its two blank lines (+2), and `CALLHOOK_SECRET` shrinking 61→12 (−49) give **+83**. Every other key name and value length is identical across both files. **Six bytes remain unexplained** — probably line termination. Logged, not waved off.

**DS-5 · The repo copy measured on the PC before it moved.** `31100` bytes · `CR = 0` · `LF = 695` · final byte `\n` · tail identical to the live file's tail. Whole, and clean LF.

**DS-6 · Installed via candidate path, not by overwriting.**

The plan in v59 was to overwrite the live file and then check it. That was reversed. The candidate was uploaded to a **separate filename**, diffed against the running code on the VPS, compiled, selftested, and only then swapped in with an atomic `mv` — with the byte-identical DS-3 backup validated by `cmp` **immediately before** the `mv` destroyed the file it would roll back to. See D168.

**The diff was read, hunk by hunk, for the first time in this project's history.** Three hunks: a docstring, one `log()` string, one trailing blank line. `2→12` lines, `2→2` lines, `+1`. `690 + 11 = 701`. `30749 + 741 = 31490`. Nothing unexplained, nothing hidden. **The claim "executing code is identical" is now verified, not asserted.**

**And the upload was stopped, because the repo's docstring was also wrong.** The candidate's header read *"run onto the end of it by a lost newline"* — the explanation disproven forty minutes earlier. The live header read *"the exact signature of a `sed -i` line-number edit"* — disproven in S125. Runbook v59 §2 states the rotation procedure is *"documented in the header of `call_hook_capture.py`"*: that header is a canonical document. Installing the candidate would have swapped one retracted causal story for another, in the canonical document, on the live box, on the evening the second one was disproven.

A corrected full file was written instead. Docstring states composition and says **MECHANISM UNKNOWN**. The repo's improved WARN string was kept — it instructs (`awk`+ENVIRON or `printf`, never `sed -i`) without claiming a cause.

**Installed 21:55 IST.** `31,490` bytes · `701` lines · `CR = 0` · final byte `\n` · md5 `beafccafbf7e81aa5f2736be939b2bbb` · `py_compile` clean on VPS Python 3.9 · **43/43 selftest on the installed file**, not merely on the candidate. Last section asserted by reading it.

**The running worker still executes the old code.** It read the file once, at import, at `14:49:13`. It will not notice the swap. The new header becomes real at the next respawn — which is **rotation step 1**. This is the same dormancy that took the clinic down on 06-Jul, deliberately induced, known, and with a chosen resolution time.

### The git trap — found armed

The clinic PC had **`core.autocrlf = true`**, and `.gitattributes` said only `* text=auto`.

LF in the repository, CRLF in the working tree. So `git clone` or `git checkout -- call-hook/call_hook_capture.py` on that machine would have written a `.py` with 701 carriage returns. Dragged into WinSCP in **Binary** mode — which D164 correctly mandates — every `\r` arrives intact on the VPS.

**Binary mode prevents WinSCP from *adding* carriage returns. It does nothing about carriage returns git already wrote.** The runbook's rule is necessary and insufficient, and it has been insufficient the whole time. Unfired only because the working copy had arrived by some route other than a checkout.

Closed both ways: `core.autocrlf false` (repo-local, clinic PC) and `*.py text eol=lf` appended to `.gitattributes` (travels with the repo, survives a fresh clone, immune to any user's config). See D167.

### The Window-2 inference — suggestive, NOT proven

`journalctl -u call-hook.service | grep -i "secret gate" | tail -3` returned exactly three startup lines: `Jul 07 16:28:04`, `Jul 08 10:28:33`, `Jul 08 14:49:13`.

Window 2 (07 Jul ~16:35 → 08 Jul 10:28) sits **entirely inside the gap** between the first two. The worker held one secret in memory, unchanged, across the whole of it. `.env` could have been rewritten a hundred times; the worker read it once, at import. **Therefore the VPS side could not have changed during Window 2.** The four 200s at 16:28–16:35 prove the worker's key matched what the panel sent; the 403s from ~16:35 prove it stopped matching; the worker did not move. **This points hard at the panel.**

Two reasons it is **not** recorded as settled. `tail -3` truncated the list — no respawn between those timestamps *appears*, but none was ruled out. And `grep "secret gate"` only catches respawns that printed that string; v1's line is shorter and it is not established that it printed on every start path.

Both are answerable by one read-only command, on the box, tonight or any night. That is backlog item 5, and it is now much cheaper than "re-read the 06–07 Jul access logs after fixing the watchdog's coverage guard."

**Do not close S94's panel question on this evidence.** It is the best evidence anyone has produced, and it is still one `tail` away from being an argument rather than a proof.

---

## §1 — STATE / MENTAL MODELS

### Track 2 live systems

- **`call_hook_capture.py` v2 — LIVE**, file replaced 08-Jul **21:55**, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 31,490 bytes, 701 lines. **The running worker still executes the pre-21:55 bytes** (imported 14:49:13). Dual-key gate armed but idle: `previous=(unset)`, **no rotation started**. Still serving the **old 12-char `@` secret**, literal label `key_db8972`, wire label `key_271f88`.
- **Rollback points (both v2, byte-identical):** `call_hook_capture.py.bak_20260708_144241` (644) and `call_hook_capture.py.LIVE_v2_s126_20260708_212453` (600). v1 exists only in GitHub and the cold kit.
- **`callhook_watchdog.py` v1.0** — VPS, manual runs only. Two known defects (§2). Trust today's output; do not trust `--date` on past days.
- `call-hook.service` — LIVE, gunicorn `-w 1`, no `--preload`, `127.0.0.1:8098`.
- `verdict_review.py` (Stage 3b) — LIVE, on demand. md5 `af6622e4edc3f454cf0bfed128c4f76b`.
- `call_verdict.py` (Stage 3 judge) — LIVE, unchanged. md5 `8c8ae1656056d8d1b2dec1b4776fe5c9`. Carries the D158 join defect.
- `Dashboard.html` v18.19 — LIVE (D156). Gate fails open on couldn't-measure.
- Stage 1 (02:00) + Stage 2 (03:00) LIVE + healthy; Drive OAuth token fresh.
- WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup; key rotations still overdue.

**`.env`:** 1416 bytes, 32 lines, mode 600, last written `08 Jul 10:28`. Contains `CALLHOOK_SECRET len=12`, `FU_UPLOAD_SECRET len=32`, and **`ANTHROPIC_API_KEY len=111`** (unaccounted, see §2).

**Clinic PC git:** `core.autocrlf=false` (repo-local); `.gitattributes` pins `*.py text eol=lf`. Git is **bundled inside GitHub Desktop** (`%LOCALAPPDATA%\GitHubDesktop\app-3.6.1\resources\app\git\cmd\git.exe`) — there is no standalone install and `git` is not on PATH.

**Track 1 / PC-local:** `processor.py` at D148 (md5 `171a090645da130a4f4cbb0c0b102f22`); Vitals & Plan Step 5 complete; Step 7 not started; Hindi spelling task open.

### Mental models — new or reinforced this session

**A cause is not a story that fits. It is a story the evidence prefers over its rivals.** Three explanations have been recorded for the 61-character `.env` value. Two were wrong. Both were plausible, both were written down confidently, both survived because nobody opened the file. The third — "duplication" — is not a mechanism, it is a *class* of mechanisms, and that is all the evidence supports. **The correct entry in a knowledge base is sometimes `UNKNOWN`, and writing it takes more discipline than writing a guess.** (D166.)

**A rule can be correct, necessary, and still not sufficient.** "WinSCP transfers must be Binary" is right. It also would not have saved you: `core.autocrlf=true` puts the carriage returns in before WinSCP ever sees the file, and Binary mode then delivers them perfectly. A control that addresses one path into a hazard is not a control on the hazard. (D167.)

**Verify the rollback point before you destroy the thing it rolls back to.** The `cmp -s "$B" "$L"` immediately before the `mv` is the whole of DS-6's safety. A backup you have not compared *at the moment of use* is a belief about the past.

**Never overwrite the live file to test it.** Upload to a candidate path; diff, compile, selftest against the *running* code; then atomic `mv`. Every failure mode ends with the clinic untouched. (D168.)

**Read the diff. Somebody has to, once.** "The difference is a docstring and one WARN string" was true — and had never been checked, in any session, by anyone. It cost thirty seconds. It caught a retracted causal claim about to be installed into a canonical document.

**A constant offset is not a rate.** 115/114 looked like a receiver silently dropping deliveries. 133/132, eighteen deliveries later, says one historical event. The same number, measured twice, changes what it means.

**The record is not the disk, and the record loses.** Five recorded facts failed tonight against direct observation, including a byte count repeated across sessions. Every finding came from looking. Not one came from reasoning about what should be true.

**Carried, all still true:** the worker reads `.env` once at import, so a disagreement is dormant until respawn · absence of coverage is not absence of events · two labels of the same key can disagree and both be right (wire vs literal, D165) · test the alarming hypothesis before you act on it *and before you reassure* · restart at a moment you choose · a dormant fault has no cause you can see · one successful call does not verify a fix · **the runbook is not evidence** · a safety flag is a clinical signal about a patient, never a statement about staff accuracy · 0 cards refereed, so every accuracy claim is agreement, not accuracy.

---

## §2 — BACKLOG (what to pick up next)

### 🔴 TOP — the reason Session 126 existed, and it is still undone

1. **Rotate `CALLHOOK_SECRET`.** Housekeeping is complete; the four-step procedure in §5 is unchanged and now runs against a verified file. The key is exposed in a chat transcript. **Steps 1 and 2 are zero-downtime and may be done at any hour. Step 3 (the panel) requires a clinic day with hours in front of it** — one real call AND a re-check at least an hour later on the same day. An incident is closed by a successful re-test, not a successful test.

2. **`ANTHROPIC_API_KEY` in `.env`.** 111 characters. Added inside the outage window; recorded nowhere. Loaded into the environment of a gunicorn worker that has no use for it. **Rotate it, and move it out of the call-hook worker's `.env` if nothing there needs it.** Find out what wrote it.

3. **Fix the two watchdog defects.** (a) **Coverage guard:** refuse to judge a date the access log does not span — zero lines currently reads as zero traffic and reports CRITICAL *"MyOperator is not delivering at all"*, a confident wrong diagnosis pointing away from the real cause. Bail with exit 3. (b) **`unquote()` before hashing** in `mask_key()`, consistently, so labels compare across sources (D165). Until (a) lands, `--date` on past days is untrustworthy.

4. **Schedule the watchdog.** Only after item 3. It exits 1 on WARN, so a naive `OnFailure` fires all day on already-fixed 403s.

### 🟠 OPEN QUESTIONS — cheaper than they were

5. **What changed in Window 2 — one read-only command away.** The journal shows no worker respawn between `07 Jul 16:28:04` and `08 Jul 10:28:33`, which would mean the VPS side could not have changed and the panel must have. **Not proven:** `tail -3` did not rule out an unprinted respawn, and it is not established that v1 printed `secret gate` on every start path. Widen the journal window and count *every* start, not just those matching that string. If it holds, S94's panel question is answered — and it no longer depends on the watchdog's coverage guard or on log retention.

6. **115 vs 114, now 133 vs 132.** Offset constant at exactly one across 18 further deliveries. **One historical event, not an ongoing defect.** Benign explanations exist (a health probe; a line counted before it was flushed). Bounded, unexplained, low priority.

7. **Six unexplained bytes** between `.env` (1416) and `.env.bak_20260707_162509` (1327), after accounting for `ANTHROPIC_API_KEY` (+130), two blank lines (+2), and `CALLHOOK_SECRET` 61→12 (−49) = +83. Probably line termination. Trivial, logged.

8. **D161 is unaccounted for.** KB v1.48 runs D121–D160 and says "next free: D161." The S125 append is headed "append after D161." It exists in neither.

### OWNER TASK (no build, ~20 min) — everything downstream depends on it

9. **Referee the 32 cards in `Verdict_Review`.** Zero are done. This is the only thing that converts "the AI agrees with staff 80% of the time" into "the AI is right N% of the time", and it is the ground truth for the autonomous judge and the voice-bot KB.

### STAGE-3 FOLLOW-THROUGH

10. **Fix `call_verdict.py`: agent + Clinic ID from the CALL record, not the claim.** 21/27 cards say "(not recorded)" — including a conduct complaint against the doctor. Clinic ID is blank on 100% of rows, which **blocks the doctor console entirely**.
11. **Fix the D158 join defect** — an incoming call must never absorb a later outgoing call's claim.
12. **Systemd timer** for `call_verdict.py` (~03:30 IST) + `verdict_review.py` (~03:45 IST).
13. **`verdict_review.py` v1.1** — the de-identified `Verdict_Training_KB` export. Needs the Stage-4 de-identifier (unbuilt) and refereed rows (item 9).

### THE STAFF-FACING PROGRAMME (designed S124, not built)

14. **Reduce the staff vocabulary to 4–5 "what next" choices**; the AI supplies the 11-code "what happened" from the transcript. Owner to supply the wording (Hindi where it helps).
15. **Ask at hang-up, one tap, optional note.**
16. **Never show staff the AI.** Corrective action reaches them from the doctor, about the patient.
17. **Measure staff on completion, never on accuracy.** (15 of 36 outgoing calls — 42% — got no outcome at all.)
18. **Background reconciler** (claim → call, the reverse join). Must read `Call_Feed`, NOT `Call_Recordings`. Three verdicts that must never be collapsed: *no attempt* · *attempt, not connected* (**blameless**) · *connected but nothing asked*.
19. **Doctor-only review console.** Blocked on item 10 (Clinic ID). `WebApp.gs` stays sealed.
20. **Diarisation (Stage 2).** Sarvam includes it at ₹30/hour. Cheapest high-leverage change.
21. **Voicemail outcome code** — dissolves if item 14 lands first.

### Track 2 live backlog (carried)

🔴 WABA authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate `WA_APPROVE_KEY` · 🔴 service-account key rotation (Lokesh) · AKEY_14 · **arm the timer-freshness checker** · maintenance jobs · `clinic_health_report.py` UTC→IST fix · courtesy-rotate `FU_UPLOAD_SECRET` (D145) · **empty-transcript guard** (3 empty on 06-Jul; they land in Unclear looking like AI failures) · **VPS Python 3.9 is past EOL** (google-auth warns on every run).

### Track 1 backlog (unchanged)

Hindi SPELLING corrections in `vitals_page.html` LIB strings · Step 7 new-patient reconciliation · Living Clinic Data Map (§66.6).

### Documentation

- **DONE this EOS:** Runbook v60 · `KB_APPEND_Session126.md` (complete; last section asserted) · incident report v3 addendum · cold kit · git kit (structured) · Notion updated live · next-session prompt.
- **`KB_APPEND_Session125.md` is QUARANTINED** — truncated. Do not paste it. Its §1 and §2 (D162–D165) are intact and are re-carried, in full, inside `KB_APPEND_Session126.md` §1A so that nothing is lost.
- **KB v1.49 was NOT re-emitted as a full file.** See §6.

---

## §3 — KEY PATHS / FACTS (Session-126 additions in **bold**)

- **Call webhook receiver:** `/root/wa/call-hook/call_hook_capture.py` — **v2, dual-key, 31,490 bytes, 701 lines, md5 `beafccafbf7e81aa5f2736be939b2bbb`, installed 21:55 on 08-Jul.** gunicorn `-w 1` (no `--preload`) on `127.0.0.1:8098`, unit **`call-hook.service`**, route `POST /mo-callhook?key=…`, proxied by `followup.dr-manoj.in` (`/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf:126`).
- **The worker reads `.env` once, at import.** A change to `.env` — or to the `.py` — takes effect at the next respawn, not at the edit. This is the mechanism of the whole incident, and as of 21:55 it is *deliberately* in effect: the file on disk and the code in memory differ, knowingly, until rotation step 1.
- **The pre-21:55 live file was 30,749 bytes, 690 lines — NOT 30,750.** The record was off by one for several sessions. Final byte was `\n`, confirmed by `od -c`. Repo copy was `31,100`. **True delta: 351 bytes, 5 lines** (docstring `2→12`, WARN string `2→2`, one trailing blank).
- **Rollback points, both v2 and byte-identical (`cmp` verified):** `/root/wa/call-hook/call_hook_capture.py.bak_20260708_144241` (30,749, mode 644) · `/root/wa/call-hook/call_hook_capture.py.LIVE_v2_s126_20260708_212453` (30,749, mode 600). **v1 is not on the box** — GitHub and the cold kit only.
- **`.env`: 1416 bytes, 32 lines, mode 600, mtime `08 Jul 10:28`.** Worker respawned `10:28:33`. Not written since.
- **`.env` inventory (names and value lengths only, never values):** `CALLHOOK_SECRET len=12` · `FU_UPLOAD_SECRET len=32` · **`ANTHROPIC_API_KEY len=111`** · `WA_WEBHOOK_SECRET 48` · `SEND_API_SECRET 32` · `CALL_API_SECRET 48` · `MYOP_OBD_SECRET 66` · `MYOP_OBD_XAPIKEY 42` · `MYOP_LOGS_TOKEN 34` · `MYOP_AUTH_TOKEN 42` · `SARVAM_API_KEY 36` · `WA_SA_KEY 32` · `WATCHDOG_SMTP_PASS 16` (+ non-secret settings).
  Print it safely with:
  `awk '/^[A-Za-z_][A-Za-z0-9_]*=/ { n=index($0,"="); printf "  %-24s len=%d\n", substr($0,1,n-1), length($0)-n }' /root/wa/.env`
- **Forensic backup: `/root/wa/.env.bak_20260707_162509`** — 1327 bytes, 29 lines, **mode 600**, mtime `07 Jul 16:25:09`. The only surviving artefact of the §94.1 corruption. It holds `CALLHOOK_SECRET len=61` **and** `FU_UPLOAD_SECRET len=32` on its own intact line. **Contains a real (old) key. Do not delete. Treat as a secret.**
- **The 61-character value: composition settled, mechanism UNKNOWN.** `12 + 17 + 32 = 61`, non-alphanumerics `@ _ _ =` in that order. It was a **duplication** (insertion), not a lost newline (which would have consumed the `FU_UPLOAD_SECRET` line) and not `sed` (`sed -i '17s'` was the S94 repair). **Two wrong causes are already on the record. Do not write a third.**
- **Reject log: `/root/wa/call-hook/call_hook_rejects/YYYY-MM-DD.jsonl`** (dir 700, files 600). Metadata only. Throttle: full detail for the first 500 refusals per day, then 1 in 100. Env override `CALLHOOK_REJECT_DIR`.
- **Watchdog: `/root/wa/call-hook/callhook_watchdog.py`** (25,042 bytes). `--selftest` (37/37, offline) · bare run (today) · `--json` · `--date YYYY-MM-DD` (**untrustworthy until the coverage guard lands**) · `--state <path>` (the only thing it ever writes). Exit 0 OK / 1 WARN / 2 CRITICAL / 3 could-not-run.
- **Key labels are md5[:6], prefixed `key_`.** The watchdog hashes the **wire** form (`%40`), the receiver hashes the **literal** form (`@`). The same key is `key_271f88` in the access log and `key_db8972` in `.env`. **Compare like with like.** `urllib.parse.quote()` bridges them. **A selftest WARN naming `key_96e7ef` is a test fixture, not your key.**
- **Current secret:** 12 characters, contains one `@`. **Exposed in a chat transcript. Rotate.**
- **Access-log forensics** (the only place a 403 storm is visible), glob `/home/*/logs/*access*`:
  `grep -h "mo-callhook" /home/*/logs/*access* | sed -E 's/key=[^& ]+/key=<masked>/g' | tail -20`
- **Startup lines, verified against the source, not the runbook** (`call_hook_capture.py` lines ~540–558):
  - `secret gate: ON  current=%s  previous=SAME AS CURRENT (rotation not started; harmless)`
  - `secret gate: ON  current=%s  previous=%s  -> ROTATION IN PROGRESS. Clear CALLHOOK_SECRET_PREV when the panel is updated and the WARN lines stop.`
  - `secret gate: ON  current=%s  previous=(unset)  -> single-key. A panel/.env mismatch will refuse every delivery. Set CALLHOOK_SECRET_PREV before rotating.`
  - `secret gate: ON  current=(unset!)  previous=%s  -> CALLHOOK_SECRET is empty. …almost certainly a mistake.`
- **VPS python is `/root/wa/venv/bin/python3`** (3.9, past EOL — google-auth warns on every run). System `python3` lacks gspread.
- **`grep -c` exits 1 when the count is 0.** Never chain it with `&&` — it will silently truncate the rest of your verification. Use `;`. (Cost this session one incomplete check.)
- **Git on the clinic PC is bundled inside GitHub Desktop:** `C:\Users\Dr Manoj Agarwal\AppData\Local\GitHubDesktop\app-3.6.1\resources\app\git\cmd\git.exe`. Not on PATH. No standalone install. Invoke from PowerShell with `& $git -C <repo> …`.
- **Local repo:** `D:\dr-manoj-git\drmanoj-clinic-automation`. **`core.autocrlf` is now `false` (repo-local); `.gitattributes` pins `*.py text eol=lf`.**
- **WinSCP transfers of `.py` and `.env` must be Binary, not Text — AND the file must be LF before it is sent.** Binary stops WinSCP adding `\r`; it does not remove `\r` that git wrote. Verify after any upload: `file <path>` says `ASCII text`, not `with CRLF line terminators`; `grep -c $'\r' <path>` is `0`.
- **Bracketed paste:** pasting a multi-line block into this shell can leak `[200~` and swallow the command. One line at a time, or `printf '\e[?2004l'` once.

---

## §4 — DECISIONS ADDED THIS SESSION (D166 · D167 · D168 · D169)

**D166 — No cause is recorded unless the evidence distinguishes it from its rivals. `UNKNOWN` is a valid, and sometimes the only honest, entry.**
The 61-character `.env` value has now had three explanations. `sed` overrunning its delimiter (incident report v1 — retracted S125). A lost newline (S125 — retracted S126, because the `FU_UPLOAD_SECRET` line survives intact in the backup, and a lost newline consumes the line it merges). And "a duplication," which is not a mechanism but a *class* of them: a `sed` overrun, a stray append, an editor, a botched heredoc paste all fit equally. **The evidence chooses none.** Both retracted causes were plausible, were written down with confidence, and survived because nobody opened the file. A knowledge base that cannot say `UNKNOWN` will fill the gap with the most recent guess and then defend it. Composition (`12 + 17 + 32 = 61`) is settled and may be recorded; mechanism may not.

**D167 — A control that guards one path into a hazard is not a control on the hazard.**
D164 mandates WinSCP **Binary** transfers for `.py` and `.env`, to stop WinSCP appending `\r`. Correct, and insufficient. The clinic PC had `core.autocrlf=true` with `.gitattributes` set to `* text=auto`: LF in the repository, **CRLF written into the working tree at every checkout**. A `git clone` followed by a Binary upload — the procedure the runbook prescribes — would have delivered 701 carriage returns to the VPS, faithfully. Binary mode prevents WinSCP from *adding* CRs; it does nothing about CRs git already wrote. **Fixed at source:** `core.autocrlf false` (repo-local) and `*.py text eol=lf` in `.gitattributes`, which travels with the repo and overrides any user's config. Generalises: when a rule names a *tool*, ask what else can produce the same byte.

**D168 — Live code is never overwritten to be tested. Candidate path → diff → compile → selftest → atomic `mv`.**
Upload to a distinct filename beside the live file. `diff` it against the *running* code and read every hunk. `py_compile` and `--selftest` on the VPS interpreter. Validate the rollback point with `cmp` **immediately before** the `mv` that destroys the file it would roll back to. `mv` on one filesystem is atomic; there is no instant of a half-written file. Every failure mode ends with the clinic untouched and nothing to undo. Then re-verify the *installed* file — compiling the candidate and installing something are two different acts. **And verify by reading the file's last section. Never by hash alone: a hash proves two files match; it cannot prove either is complete.**

**D169 — Secrets are inventoried by name and value length, never by value.**
`awk '/^[A-Za-z_][A-Za-z0-9_]*=/ { n=index($0,"="); printf "%-24s len=%d\n", substr($0,1,n-1), length($0)-n }' <envfile>` prints a complete census with nothing secret on the screen, in a transcript, or in a scrollback buffer. Run it against `.env` and against every `.env.bak_*` at each EOS. It is how `ANTHROPIC_API_KEY len=111` was found sitting unrecorded in the call-webhook worker's environment, added during the outage window by something nobody has identified. It is how `CALLHOOK_SECRET len=61` was confirmed against `FU_UPLOAD_SECRET len=32` on its own surviving line, which is what killed the lost-newline theory. **An unknown secret in a live process's environment is a fault, whether or not it has caused one yet.**

---

## §5 — THE ROTATION PROCEDURE (D162) — read before touching `.env`

Four steps, four restarts, no downtime possible. At no point can a mismatch stop the clinic.

**Generate the new key ON THE VPS.** `openssl rand -hex 12` → 24 hex characters. No `@`. Nothing that percent-encodes. That removes the D165 encoding trap at source, and it was the right instinct in S94 — only the execution was wrong. **The key must never enter a chat transcript.** Masked `key_<md5[:6]>` labels only.

1. Copy the **current** key into `CALLHOOK_SECRET_PREV` as well, by appending a line with `printf` (or `awk`+ENVIRON), never `sed`. Restart. Nothing changes — both variables hold the same value, both are accepted. The startup line will say `previous=SAME AS CURRENT (rotation not started; harmless)`.
   *This restart is also what loads the 21:55 file into the worker for the first time.*
2. Put the **new** key into `CALLHOOK_SECRET`. Restart. Deliveries keep arriving on the old key, each one logging `WARN: request accepted on the PREVIOUS key (key_…)`. The startup line will say `ROTATION IN PROGRESS`.
3. Update the **MyOperator panel** to the new key. **No restart in this step** — the signal is *negative*: the WARN lines stop. Verify per the S124 hardened standard: one real call **and** a re-check at least an hour later, **on the same clinic day.** An incident is closed by a successful re-test, not a successful test.
4. Clear `CALLHOOK_SECRET_PREV`. Restart. Rotation complete. Startup line returns to `previous=(unset)`.

**Before every restart:** `file` · `grep -c $'\r'` (must be `0`; chain with `;` not `&&`) · `py_compile` · `--selftest` (43/43).
**After every restart:** read the startup line and confirm the key label is the one you intended. **A fix verified by probing the server with the key you just wrote to it proves nothing** — that is how S94 died in seven minutes.

**Steps 1 and 2 are safe at any hour. Step 3 needs a clinic day with hours in front of it.**

---

## §6 — A NOTE ON THE MASTER KB

`Clinic_Master_KB_SystemsRegister_v1.48.md` is 107 KB. It was **not** re-emitted as a full file this session either, and the reason is now stronger than it was in S125.

The project protocol is *full-file replacements, never diffs to hand-edit* — a rule written for **code**, where a partial file is a broken program. For a 107 KB canonical document the calculus inverts: re-emitting it from a summary risks silent, unnoticeable loss of material that has no other home, which is a worse failure than a paste. **S125 attempted close-out artefacts at scale and shipped five truncated documents.** That is not a hypothetical.

There is a second, decisive reason this session. The KB is reachable only through the assistant's read interface, **not through the shell**. A full rewrite therefore could not be mechanically diffed against its source, byte-counted before and after, or verified by any means except reading it — which is exactly the verification that failed five times in S125. **A file I cannot verify is a file I should not emit.**

`KB_APPEND_Session126.md` is therefore an **append-ready block**, and it does one thing more than S125's: **it re-carries S125's §S125 section and D162–D165 in full**, because the S125 append block is truncated and must never be pasted. Paste the Session-126 block and the KB reaches v1.49 with nothing from S125 lost.

If you want a true full-file v1.49, say so at the start of Session 127 **and provide the v1.48 source in a shell-reachable location** (the uploads folder). It will then be built from the source directly, with a byte count and a last-section assertion before and after.

---

## §7 — SESSION HYGIENE NOTES

- **`KB_APPEND_Session125.md` is truncated. Quarantine it.** Move it to `_QUARANTINE_TRUNCATED_S125\` beside the other four. Its intact §1 and §2 are re-carried inside `KB_APPEND_Session126.md` §1A. **Nobody should ever paste the S125 block.**
- **`call_hook_capture.py.CANDIDATE_s126` was deleted from the VPS.** It was 31,100 bytes, passed every mechanical check, and carried the retracted "lost newline" docstring. Left lying in the directory it was live ammunition — the sort of file that gets installed six weeks later by someone tidying up.
- **`__pycache__` was removed** from `/root/wa/call-hook/` after `py_compile`. gunicorn imports this module; a stale `.pyc` is one more thing that can be out of step with its source, and this project has lost three clinic days to *"a file and the thing reading it disagreed and nothing said so."*
- **Both `.bak` files in `call-hook/` are copies of v2 and are byte-identical to each other.** Neither is a route back to v1. v1 (15,617 bytes, 03-Jul) exists in the cold kit and in GitHub.
- **`/root/wa/.env.bak_20260707_162509` is forensically irreplaceable and now mode 600.** Its `CALLHOOK_SECRET` line contains a real (old) key. Do not delete it. Treat the file as a secret.
- **`/root/wa/.env.bak_s126_20260708_212316`** (this session's `.env` backup, mode 600) also contains the live key. Same rules.
- The current key appears in a chat transcript. **That is the reason rotation is item 1, not item 9.**
- **This session touched no secret, wrote nothing to `.env`, and restarted nothing.**

---

**END OF RUNBOOK v60 — §7 is the last section. If §7 is absent, this file is truncated.**
