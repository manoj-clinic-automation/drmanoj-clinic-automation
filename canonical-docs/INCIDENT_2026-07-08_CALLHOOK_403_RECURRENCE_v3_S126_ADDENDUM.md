# INCIDENT — CALLHOOK 403 RECURRENCE — v3 (Session 126 addendum)

**Append to `INCIDENT_2026-07-08_CALLHOOK_403_RECURRENCE_v2.md` after its closing note.
v2 is intact (verified: reaches `## 9.` and its closing section). This is additive; nothing in v2 is deleted.**

---

## 10. **[S126]** THE SECOND RETRACTION — AND WHY THERE MUST NOT BE A THIRD

v1 of this report said the 61-character `CALLHOOK_SECRET` line was created by `sed -i '17s'` running past its closing delimiter. **Retracted in S125:** that `sed` was Session 94's *repair*; it removed the run-on.

v2 (and S125's correction throughout the project record) said the line was created by a **lost newline** merging `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment. **Retracted in S126.**

The forensic backup was opened and read — by name and value length, never by value:

```
/root/wa/.env.bak_20260707_162509   (1327 bytes, 29 lines, mode 600, mtime 07 Jul 16:25:09)

  CALLHOOK_SECRET          len=61
  FU_UPLOAD_SECRET         len=32
```

**`FU_UPLOAD_SECRET` is present, on its own intact line.**

A lost newline *merges* two lines: it consumes the second. That line survived. Therefore the 61 characters did not arrive by deletion of a newline. **They arrived by duplication — text inserted, nothing removed.**

### What is settled

The composition. `12 (the @ key) + 17 ("FU_UPLOAD_SECRET=") + 32 (the alnum value) = 61`, and the non-alphanumeric characters fall out in exactly the observed order `@ _ _ =`. `strip()` changes nothing. Not whitespace, not a third key.

### What is not settled

**The mechanism.** "Duplication" is a *class*, not a cause. A `sed` overrun, a stray append, a text editor, a botched heredoc paste — every one of them inserts without deleting. **The evidence distinguishes none of them.**

### Why this matters more than the answer would have

Three explanations have now been recorded for these 61 characters. Two were wrong. Both were plausible. Both were written with confidence, into an incident report and into a knowledge base. Both survived — one of them for two sessions and one incident report — **because nobody opened the file.**

The file was on the VPS the whole time. Reading it took thirty seconds.

**Recorded as D166: no cause is recorded unless the evidence distinguishes it from its rivals. `UNKNOWN` is a valid entry, and writing it takes more discipline than writing a guess.**

---

## 11. **[S126]** WINDOW 2 — NEARLY SETTLED, DELIBERATELY LEFT OPEN

`journalctl -u call-hook.service --no-pager | grep -i "secret gate" | tail -3` returned exactly three startup lines:

```
Jul 07 16:28:04   [call_hook_capture] secret gate: ON
Jul 08 10:28:33   [call_hook_capture] secret gate: ON
Jul 08 14:49:13   [call_hook_capture] secret gate: ON  current=key_db8972  previous=(unset) …
```

**Window 2 (07 Jul ~16:35 → 08 Jul 10:28) sits entirely inside the gap between the first two.**

`gunicorn -w 1`, no `--preload`: the worker reads `.env` once, at import. Across the whole of Window 2 the worker held **one secret in memory, unchanged**. `.env` could have been rewritten a hundred times and the worker would never have known.

Therefore **the VPS side could not have changed during Window 2.**

The four deliveries that returned 200 at 16:28–16:35 prove the worker's key matched what the panel was sending. The 403s that begin at ~16:35 prove it stopped matching. **The worker did not move. Something at the other end did.**

This is the strongest evidence yet for the panel-reverted hypothesis — and **it is not proof.**

- `tail -3` truncated the list. No respawn *appears* between `16:28:04` and `10:28:33`. None was *ruled out*.
- `grep "secret gate"` only catches respawns that printed that string. The v1 startup line is shorter, and it has not been established that it printed on every start path.

**Do not close §4's root-cause question on this.** It is an argument, not a demonstration, and it is one read-only command away from being either.

That command — widening the journal window and counting *every* service start, not only the ones matching a string — is now the cheapest route to an answer. It does **not** require the watchdog's coverage guard, and it does **not** depend on access-log retention. It was the expensive path in v2 §8 and it is no longer.

---

## 12. **[S126]** CORRECTIONS TO THIS REPORT'S OWN FACTS

- **The live `call_hook_capture.py` was 30,749 bytes, not 30,750.** Off by one, repeated across sessions. 690 lines. Final byte confirmed `\n` by `od -c`, so nothing was missing from the end — **the record was simply wrong.** The repo figure `31,100` came from the same record, so the long-quoted 350-byte delta was unverified in both directions. Measured: **351 bytes, 5 lines.**
- **`.env` and the running worker provably agreed throughout S126.** `cp -a` preserved the mtime: `.env` last written `08 Jul 10:28`; worker respawned `10:28:33`; `last 403` at `10:28:02`. One deliberate act. Confirmed three independent ways (startup label, wire label, mtime).
- **The 115-vs-114 raw-log gap is bounded.** At 21:20 it was **133 accepted / 132 lines**. Eighteen further deliveries, eighteen further lines, **offset still exactly one.** An ongoing defect widens; this did not. **One historical event, not a running mechanism.** Reclassify from "the receiver is silently dropping data" to "one anomalous 200 on 08 Jul, unexplained, low priority."
- **An unrecorded secret was in `.env` during the incident.** `ANTHROPIC_API_KEY len=111`, absent from the 07-Jul backup, therefore written between `07 Jul 16:25` and `08 Jul 10:28` — **inside the outage window** — by something nobody has identified. It is loaded into the environment of the gunicorn worker that serves this webhook. Mode 600. **Rotate; relocate; find the writer.** Whether it is related to this incident is unknown; that it appeared during it, unrecorded, in the file at the centre of it, is a fact worth staring at.
- **Six bytes between `.env` (1416) and the forensic backup (1327) are unaccounted** after `ANTHROPIC_API_KEY` (+130), two blank lines (+2), and `CALLHOOK_SECRET` 61→12 (−49) = +83. Probably line termination. Logged.

---

## 13. **[S126]** A LATENT FAULT OF THE SAME CLASS, FOUND ELSEWHERE

The clinic PC had **`core.autocrlf = true`**, with `.gitattributes` reading only `* text=auto`.

LF in the repository. **CRLF written into the working tree on every checkout.**

`git clone`, then a WinSCP upload in **Binary** mode — precisely what D164 mandates — would have delivered **701 carriage returns** into a `.py` on the VPS. Binary mode stops WinSCP from *adding* `\r`. It is powerless against `\r` that git wrote before WinSCP ever saw the file.

This never fired only because the working copy had arrived by some route other than a checkout.

**The rule was correct and insufficient.** Closed at source: `core.autocrlf false` (repo-local) and `*.py text eol=lf` in `.gitattributes`, which travels with the repo and overrides any user's configuration. Recorded as **D167: a control that guards one path into a hazard is not a control on the hazard.**

The same sentence describes the original incident. A gate that refuses silently is indistinguishable from a world that never called; a transfer rule that guards one tool is indistinguishable from safety, until a second tool writes the same byte.

---

## 14. **[S126]** STATUS

**The rotation has not started.** `.env` was not written. Nothing was restarted. `previous=(unset)`.

`call_hook_capture.py` on disk was replaced at 21:55 (31,490 bytes, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43 selftest on the installed file), by candidate path and atomic `mv`, never by overwriting the live file (**D168**). **The running worker still executes the pre-21:55 bytes.** The new file loads at the next respawn, which is rotation step 1 — the same dormancy that caused this incident, this time induced deliberately, understood, and with a chosen resolution time.

The 12-character `@` key remains exposed in a chat transcript. **That is why rotation is item 1.**

---

**END OF INCIDENT ADDENDUM v3 (S126). §14 is the last section. If §14 is absent, this file is truncated.**
