# HANDOFF RUNBOOK — 13 Jul 2026 · Session 142 · v80 (FULL EOS)

**Files changed this session:** `daily_digest.py` **v1.2.1-S142** (NEW, `/root/wa/recordings-archive/`,
live md5 `e6df21cce507bd2d4e60dd9c5644b008`, selftest 72/72) · `/root/wa/.env` +3 `DIGEST_` lines
(app password copied silently from `/root/att_config.py`) · crontab +2 lines (11:00 pulse, 21:30 digest)
· **crond restarted** (F-41 cure) · `Verdict_Review` redrawn (`--days 21` → 8,845 rows / 378 cards).
New canonical docs: KB **v1.68** · Umbrella **v1.54** · this runbook · START_HERE_SESSION_143 ·
`INCIDENT_2026-07-13_CRON_UTC_F41.md`. Deliverable: `D237_Referee_Set_S142.xlsx`.

---

## §0 — WHAT HAPPENED (Session 142, Mon clinic morning 13 Jul)

**§0.1 🟢 D236 DIGEST LAYER BUILT AND LIVE, in one morning.** `daily_digest.py`: reader of everything,
writer of nothing shared — `spreadsheets.readonly` scope and zero append calls, both selftested
assertions. Gate chain every install: md5 exact → COMPILE-OK → selftest on the VPS interpreter. Email
pipe proven end-to-end before anything was armed (the old test-draft gate was replaced by a stronger
fact: the clinic account already mails the owner's personal inbox daily; then `--test` + a live pulse
both landed on his phone). v1.0's **live dry-run caught three real defects** before any email went out:
the judged↔pending join used the wrong key shapes (verdict `Join Key` = `mobile10_epochSECONDS`;
`client_ref_id` = `mobile10-epoch+hex`), unpadded verdict times text-sorted 10:00 before 8:58, and
duration rows duplicate. v1.1 fixed all three. **Owner amendment (D238): the 11:00 pulse ALWAYS sends,
opening with ALL of the morning's calls.**

**§0.2 🔴 F-41 — the pulse's own no-show found a month-old system fault.** 11:00 came, no email, no log
file. Chain: OS timezone IST, but crond `ActiveEnterTimestamp` = 16 Jun — **a daemon keeps the timezone
it was born with**, and it predated the IST switch. Proof from artefacts: the "03:40" sweep's log
stamped 09:10 IST; the S140 08:45 write-probe's log **did not exist** (it never fired on schedule — its
PASS was the manual run); even `/var/log/cron`'s timestamps were UTC in local dress. Masked throughout
by the at-hangup worker doing the real work in minutes. Cure: `systemctl restart crond`; **proven by a
2-minute canary writing IST minute-boundary lines — never by the restart message** (D235). Pulse fired
manually the same minute. Tonight's 21:30 digest = first correctly-clocked cron run; tomorrow 08:45 =
the write-probe's first real scheduled firing.

**§0.3 Owner-directed, same day: the unjudged-call reason classifier (v1.2 → v1.2.1).** Every pending
call in the pulse now explains itself: not answered · too short (Ns talk) · in pipeline ·
transcribed—verdict due · **⚠ talked Ns, no recording**. Keyed on `customer_result` +
`customer_talk_duration`, values read from the live tab (the flags turned out to be "YES" not "TRUE" —
the digest's `truthy_flag` already accepted YES; only the session's ad-hoc grep had guessed). The ⚠
detector escalates into Needs Attention (v1.2.1: alerts sort FIRST so the 5-line cap can never cut one
— it had, on the first live send) and prefixes the 21:30 suggestion line when any exist.

**§0.4 🔴 F-42 (OPEN) — caught by the classifier's first production run.** 8287590248 (09:37+09:38,
40 s+27 s talk) and 6392367128 (11:07+11:09, 39 s+101 s): all four `status=missed` **+**
`customer_result=connected`, and no recording/transcript ever appeared (checked hours later). The
morning's judged incoming calls lack that combination. Hypothesis: answered on a leg MyOperator doesn't
record (reception mobile direct) → no retry will ever help; fix would be panel-side. S143 investigates
(hook logs, MyOperator Call API by session_id, possibly Lokesh).

**§0.5 D237 referee set built; refereeing parked (owner: Option B).** 41 calls from the 566
(seed `D237-S142`, reproducible): all 18 outcome codes × both directions × 3 confidence levels × all 6
flag types, 12 mismatches, 29-Jun→13-Jul. Delivered as `D237_Referee_Set_S142.xlsx` (listen links; red
= mismatch, amber = flagged). Enabling redraw `verdict_review.py --days 21` → 8,845 rows / 378 cards,
**sheet count verified equal to the script's claim** (an earlier check against a mid-write export was
correctly distrusted and re-run — F-39 discipline). **Gap:** 28/41 answerable — ai-only caps at 120
cards, and **MATCH calls render as lines with no answer cell**, which also means **the D236 daily
2-spot-checks have no landing cell today.** Owner chose Option B: the whole sitting waits for the S143
enhancement.

**§0.6 D239 — Flag Investigator approved (design only; S143 build).** Per ⚠ flag: ask MyOperator's
Call API (session_id) if a recording exists → YES = self-heal (re-trigger download→transcribe→judge);
NO = label "answered outside the recorded route" + pattern count; also check hook logs for the kick;
write findings to a VPS results file the digest READS. Owner defaults: self-heal ON · every 30 min
09:00–20:00 · ≥3 provider-never-recorded/week → digest says raise with Lokesh. ₹0, no new tabs.

**§0.7 Monday-list items proven incidentally:** K-1/K-2 staff taps live in production (a morning of
`k_` claims, first K-era incoming mismatches); verdict-in-minutes proven twice (9557703250 judged
between two pulse snapshots). **F-40 confirmed live** (banner "v1.3 (S124, D155)" on the owner's
screen), still unfixed — the day filled. **Repo drift confirmed by hash:** repo `call_verdict.py` is
still v1.0-S128 (`b7dc12613ae24afee41fdc8bd6910480`); the S141 v2.1 commit never happened;
`daily_digest.py` has no repo copy. Both owed.

---

## §1 — MENTAL MODELS (deltas only; v79 §1 still holds)

- **A dry-run against live data is the real gate.** COMPILE-OK and 50/50 selftests passed a file whose
  join could never match a single row. The dry-run caught it in one screen. Selftests prove the parts;
  only live data proves the joins.
- **A daemon keeps the timezone it was born with.** `timedatectl` saying IST proves the OS, not the
  services started before the switch. F-41's whole class: check the *process's* birth date, not the
  box's setting.
- **Detectors pay for themselves same-day.** The lost-conversation classifier was requested at 11:30
  and caught F-42 on its very first run at 11:31. Build the detector before investigating the anomaly
  — the detector *is* the investigation, automated.
- **An alert must outrank the cap that displays it.** The first live pulse cut its second ⚠ line at
  exactly 5 items. Severity ordering belongs in the code, not in the hope that there are few alerts.

---

## §2 — OPEN BACKLOG (ordered)

**A. Observe tonight/tomorrow (no action):** 21:30 digest arrives = first cron-fired one (check spam
once) · its suggestion line should carry the F-42 calls · 08:45 write-probe first real PASS tomorrow
(`/root/wa/call-hook/write_probe.log` must exist after) · 11:00 pulse fires by cron tomorrow.

**B. Session 143 build (owner-approved order):**
1. **`verdict_review.py` enhancement** — force-draw full answer cards for a supplied key list (and
   revisit the ai-only cap for supplied keys). Unblocks BOTH the 41-card D237 sitting (Option B) and
   the daily 2-spot-check landing cell. Then the owner referees the 41.
2. **Flag Investigator (D239) + F-42 investigation** — one build, they are the same work.
3. **F-40 three one-liners** ride along (verdict_review banner; v2.1 "F-21"→"F-39" comments).
4. **GitHub commits owed:** `call_verdict.py` v2.1 + `daily_digest.py` v1.2.1 (+ this session's docs).
5. Digest cosmetics queued: judged rows show Duration "-" (verdict Duration cell empty — cosmetic);
   sub-threshold wording already handled by the classifier.

**C. Standing (unchanged from v79):** CALLHOOK Steps 3–4 with Lokesh (Step 4 locked until Step 3) ·
service-account key rotation (Tier A1, Lokesh) · AKEY_14 · Hindi spellings in vitals_page.html ·
F-37 health-mail window · repo naming tidy · K toggle-removal watch · Docterz export migration (owner
decision pending) · then A8 / D223 gist tile (consumes digest metrics).
**Watch:** ai-only bucket day-over-day (K-adoption proof) · F-42 pattern count once the Investigator
runs.

**Session counter: 142 CLOSED (full EOS). Next session: 143.**
