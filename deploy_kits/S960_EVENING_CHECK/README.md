# S960_EVENING_CHECK — the evening check (the parent · S527 · 26-Nov-2026 · D1080, the Morning Match kit A · Opus)

His "ok" 12:58 IST 26-Nov on the Morning Match mock-up v2.1 (artboard 2). His words 12:21 / 12:30: reception AND Shavez told in the
least time — "15 minutes is too much at closing" — and "a all good notification also if 1st export has no issues".

| file | from → to |
|---|---|
| `/root/finance/docterz_pickup.py` | a6cbdb8b (S868) → see `TO_PINS.md5` (one hook) |
| `/root/finance/parchi_desk.py` | 10532553 (S844) → see `TO_PINS.md5` (the box at the top of today's desk; its two doors) |
| `/root/finance/evening_check.py` | NEW |
| crontab | + one line `# S960_EVENING_PICKUP` (the Drive pickup every minute 19:00–22:59 Mon–Sat, then the sweep; the */15 line stays) |

**What changes.**
1. **At once, either road.** When `docterz_pickup.take()` takes a consultation report as the CURRENT one — from the reception PC's
   direct upload or from Drive — it starts `evening_check.py` in its own detached process and returns (the take never waits; nothing
   there can fail it). The check reads the stored export itself, never through the tracker's 180-second quiet and the half-hour chain.
2. **The rules are his list's rules** (`not_in_docterz.rows`): an OPD slip whose clinic ID has no row; an X-ray / procedure slip whose
   clinic ID has no row of that kind (X-ray = Laboratory + Radiology, procedure = amount or discount, as the tracker's `revenue.py`);
   state ok, digits ID, no radd, no name-only slip, a free line left out, a rejected chhoot at full rate; a slip already answered on
   `nid_mark` left out. The walk proves the same slips and amounts as his list on the same export.
3. **One push per export**, through the call-back clock's own road (`callback_clock.send`: Web Push; ntfy only for a login with no
   device when a staff topic is set), to `EVCHK_TO` (shavez, reception): missing → "N parchi Docterz mein nahi" + names; the first
   export clean → "✓ 26-Nov: sab parchi Docterz mein — PC band kar sakte hain"; a later export clearing a named list → "✓ Sab parchi
   Docterz mein — kaam poora"; another clean one after that → nothing. Shavez's tap opens the desk; reception's the portal.
   Only TODAY's export taken from 17:00 (Sunday 12:00) is judged; a morning catch-up or an afternoon export is left alone.
   "PC band kar sakte hain" only after the closing (20:30; Sunday 14:30). One check at a time (a lock beside the database): two
   exports close together are judged in turn, and a check whose export is replaced while it works pushes nothing.
   A walk or rehearsal on any database but the live one records its answer and pushes nothing.
4. **The desk** (`/finance/slips/desk`, today only): the list at the top — name, ID, slip, what, amount — each with "Paise nahi liye"
   (the answer 'free' on the same `nid_mark` row his list uses; audited). It re-reads itself every 30 seconds, so it clears about a
   minute after a corrected export. His English view says "Money not taken".
5. **The pickup** from Drive every minute at closing (a second cron line on the same lock), then `evening_check.py --sweep`: an
   evening export no check judged (a failed start, or a check that died after its claim) is judged then, under the same lock. Silent otherwise.

**Decisions made in the build (stated, not asked):** the evening starts at 17:00 (Sunday 12:00) — `EVCHK_FROM`, `EVCHK_SUN_FROM`;
every live answer on `nid_mark` (not only free / wrong) keeps a slip off the evening list; reception's tap lands on the portal (the
desk does not admit that login); the desk's box is always today's and shows only while the desk's day picker is on today;
`EVCHK_ON=0` turns the pushes off, `EVCHK_SPAWN=0` the start from the take; the check's log is a few lines a day, not rotated. Kit C (the morning) will
word a staff 'free' answer as the staff's, not "(Dr Manoj)".

**Proof.** `walk_s960.py` (made-up database and exports): **T** the take starts the check in its own process (a real push from it),
returns in under 3 s, starts nothing when off / dry / the file absent / a follow-up log · **R** the reader and the rules, the same
answer as `not_in_docterz.rows` · **P** once per export: before 17:00, missing, the same export twice, corrected, clean again, not
current, the first clean (before and after the closing), not the live database, off, unreadable, the logins setting, an earlier day,
Sunday · **X** a newer export landing during a check (nothing pushed; the newer one judged), the lock · **W** the sweep: nothing to
do, an unjudged export, again, a check at work holding the lock (the sweep waits, then does nothing), a check that died · **C** the LIVE
`callback_clock.py`'s real `send()` with a stub pusher · **K** the desk: no box before an export, the box, English, the two doors
mounted by `parchi_desk.init`, "Paise nahi liye" writes and refuses twice, his list sees it, gate 403, the desk page carries the box
today and not on an earlier day, a fault leaves the desk as it was. CONTROL: the walk on the live code as it is goes red at T1.
`make_s960.py` remakes the two changed files from the live bytes. `probe_s960.py`: on the box, read-only, counts only — the last six
exported days, the evening check beside his list; **a slip the evening check would name that his list does not stops the install, and so does a probe that read no day**. `rehearse_s960.sh` (22 paths on a made-up root): dry · install · again · undo ·
undo twice · re-install · red at 4 and 5 · killed · healthz 502 · door 404 · a Traceback · drift · the file already there · lock ·
corrupt kit · the cron line already there · no S443 line · the crontab changed while the kit checked · the probe red · the probe read nothing · the probe agreeing.

**Cold review:** 2 MUST built in (SUMS after the last README edit; the mount proof — the finance gate answers 302 to any unsigned
path, so a failed mount is now printed and caught in the log) and 8 SHOULD: built in — the race (lock + the superseded re-check), the
sweep, the parity walk written by hand + the probe gating, the reader aligned with revenue.py (UID-shaped rows; X-ray by amount), the
desk's day picker, the crontab re-read before writing, the closing wording; noted — the log's size (a few lines a day).
**Second look:** 1 MUST built in (the box was hidden for its first 30 seconds: the page fills its day picker after the box's
script runs — an empty picker now hides nothing, and the box re-checks when the page has loaded); 2 SHOULD built in (the sweep
works under the checks' lock — no second push from a check still at work; the probe must have read a day).

**On the box, at any hour** (clinic-finance restarts for a few seconds). One line:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s960kit && cp -rp /root/deploy/repo/deploy_kits/S960_EVENING_CHECK /tmp/s960kit && bash /tmp/s960kit/install_S960_EVENING_CHECK.sh
```
Undo: `bash /tmp/s960kit/install_S960_EVENING_CHECK.sh --undo` (backups `*.bak_S960_<from>`, 0600; `crontab.bak_S960`; the table
`evening_check_push` and any answers kept).
