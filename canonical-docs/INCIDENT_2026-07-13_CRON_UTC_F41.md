# INCIDENT — 2026-07-13 — F-41: crond running on UTC since 16 Jun (every cron 5h30 late)

**Fault code:** F-41 · **Severity:** High (silent, systemic) · **Status:** RESOLVED same morning
**Detected:** 13 Jul 2026 ~11:11 IST (the D236 11:00 pulse did not arrive on its first armed day)
**Resolved:** 13 Jul 2026 11:16:58 IST (crond restart) · **Time to resolve:** ~6 minutes from detection
**Exposure window:** 16 Jun → 13 Jul 2026 (≈27 days)

## Timeline
- **16 Jun 22:03 IST** — crond (re)starts. The server's timezone is set to IST at some point AFTER this;
  the running daemon keeps the UTC environment it was born with. Nothing notices.
- **S140 (12 Jul)** — the 08:45 write-probe cron is armed. Its manual run PASSes; the scheduled run
  never fires (would-be first firing: 14:15 IST). No log file is ever created. Unnoticed.
- **S140–S142** — the "03:40" verdict sweep actually fires at **09:10 IST** daily. Masked: the
  at-hangup pipeline worker judges every call in minutes, so the sweep always finds ~0 to do and its
  mis-clocking is invisible in outcomes.
- **13 Jul 11:00 IST** — the newly armed D236 pulse does not arrive. `digest_cron.log` does not exist.
- **11:13** — `date` = IST, but `/var/log/cron`'s newest entry reads 05:42 and the 08:45 probe log is
  absent. Hypothesis: crond on UTC.
- **11:15** — proof: `timedatectl` shows IST at OS level; `verdict_cron.log` mtime **09:10 IST** today
  (= 03:40 UTC); `systemctl show crond -p ActiveEnterTimestamp` = **16 Jun** — pre-dating the timezone.
- **11:16:58** — `systemctl restart crond` (+rsyslog). Canary installed: `* * * * * date >> /tmp/...`.
- **11:17 / 11:18 / 11:19 IST** — three canary lines on IST minute boundaries. **Proof accepted from
  the canary's output, not from the restart message** (D235). Canary removed; crontab verified back to
  real contents. The 11:00 pulse fired manually at 11:19; received on the owner's phone.

## Root cause
A long-running crond inherits its timezone at process start. The daemon predated the box's IST
configuration, so every crontab time was interpreted as UTC (+5h30 in IST terms). The OS-level check
(`timedatectl`) was true and irrelevant — the process's birth date was the evidence that mattered.

## Impact
- Every clinic cron fired 5h30 late for up to 27 days: verdict sweep at 09:10 IST (harmless — the
  worker masked it), write-probe **never fired** (its daily PASS guarantee was fiction from S140 until
  today), and the new digest crons would have delivered the "morning" pulse at 16:30 and the "nightly"
  digest at 03:00.
- No data lost. No patient-facing effect. The damage was to *guarantees*, not to outcomes — the exact
  failure class Diagnostics exists for.

## Fix & verification
`systemctl restart crond` → daemon reborn under IST. Verified by a temporary every-minute canary
writing IST-stamped lines (3 observed), then removed. Follow-through checks: tonight's 21:30 digest is
the first correctly-clocked cron run; tomorrow's 08:45 write-probe log must exist.

## Lessons (into the canon)
1. **A daemon keeps the timezone it was born with.** Any future timezone change ⇒ restart every
   scheduler/service that reads wall-clock times.
2. **"Armed" is not "fired."** A cron's first *scheduled* firing must be observed (log mtime in the
   expected window) before its guarantee is claimed — the write-probe's PASS was a manual run wearing a
   schedule's clothes (same species as D174: a selftest is not a production verification).
3. The masking pattern repeats F-40's: a stale label (log timestamps in UTC dressed as local) made the
   fault look like normal data.

## Related
F-40 (stale banners — same camouflage species) · D235 (trust the artefact's own output, never the
success message) · D231 (worker = fast path, cron = floor — the floor was mis-clocked and the fast
path hid it) · F-42 (found the same morning by the new classifier; separate fault, separate note when
investigated).
