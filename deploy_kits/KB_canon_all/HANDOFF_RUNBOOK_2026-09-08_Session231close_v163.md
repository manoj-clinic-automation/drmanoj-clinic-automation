# HANDOFF RUNBOOK — v163 · Session 231 close · 08-Sep-2026

*Supersedes v162 (S230 close). Tier 0.*

---

## §0 · WHAT HAPPENED

A morning that began as records housekeeping and became a credential session.

**Phase 0.** `D:\Downloads` was **not connected** — named, requested, granted. Manifest **406/406**
from inside `KB_canon_all`. Marg pull alive. **The four S230 VPS pins, recorded as PREDICTIONS and
DECLARED-PENDING, were read back from the box and all four matched.** The freshness cron was found
correctly registered at `5 8 * * *` on an IST box, so the absent 08:05 line was expected, not a
finding.

**F-363 answered, and the S230 diagnosis was wrong.** There was no transliteration — the disk copy
keeps every `·`, `—`, `⭐` and `§`. All eighteen bytes were accounted for exactly: `→` rendered as
the **word "to"**, and as "," and ", then", and a parenthetical dropped. **No tool does that. The
copy was retyped by hand.** A 56-document sweep across both stores found 54 identical and 2
differing the other way. **A single-file event.**

**Then the owner found what the sweep structurally cannot see.** The corrected staff advance policy
document was written back — and he said it is *still* wrong: the 50% capping and the
waive-the-application-as-pending path are both live and absent from it. **Both stored copies agree
with each other, the newer one says SIGNED AND EXECUTED, and both are wrong about what runs.**

**F-358 closed, and the record had understated it eightfold.** Not "two copies in the repository" —
**sixteen files, two topics, five live places**, in a repository confirmed **public**. The topic name
is the whole credential. Rotated in three self-gating kits, config written before any default was
removed, and the proof taken from `/proc/<pid>/environ` rather than `is-active`.

**F-365 — the finding of the session.** A **live** MyOperator/WABA Bearer token, with the company ID,
phone-number ID and a real mobile number, in `followup-tracker/python test_send.py` — a filename with
a literal space, an accidental save — **public for 84 days.** Confirmed live by matching the masked
hint in the project's own reference card.

**New fault codes:** F-364 … F-368. **Decisions:** D419 … D424. **No SOP change. No
surveillance-scope change.**

---

## §1 · MENTAL MODELS — what changed in how to think about this system

**1 · A count in a record is a claim, not a measurement.** The record was wrong twice in one morning
— "two copies" of a topic that was in sixteen files, and "flattened to ASCII" for a document nobody
had flattened. Both were corrected only by going and measuring. **Re-measure before acting on any
number a record gives you.**

**2 · Two stores agreeing is not correctness.** A byte sweep can only catch stores that DISAGREE. A
document that agrees with itself everywhere and has been overtaken by reality is invisible to it.
**Only the owner or the live code can catch that.** He did, in one sentence, on a document that had
just been "corrected".

**3 · A rotation's blast radius includes people, not just files.** Rotating one shared topic darkened
four devices and stopped reception being nudged, with no error anywhere. **Enumerate who consumes a
secret and on what device, before touching it.**

**4 · Search by VALUE, never by the shape the value takes.** The first scan looked for
`https://ntfy.sh/<topic>` and walked straight past the notifier, which stores the same topic as a
bare name in a unit file. That would have been a half-rotation — the worst outcome, because the owner
would have believed he had moved.

**5 · A secret in code is a secret nobody rotates.** This is why the Apps Script MyOperator values
have never been rotated, and why `freshness.py` needed no code change at all while three hard-coded
copies each did. **Configuration, not code (D417/D423).**

**6 · The gate is worth more than the fix.** The 84-day leak was not a design failure — the codebase
is disciplined, 69 candidates had empty defaults. It was an accident nothing was watching for. **The
durable answer is a pre-publish secret gate, not a rotation.**

**7 · `is-active` is not proof.** A unit that starts with no topic looks exactly like success. Read
the running process, or read the log line the code itself prints.

---

## §2 · THE LIVE BACKLOG — what S232 picks up

**⭐1 · THE SECRET GATE IN THE PUBLISH.** F-365's durable fix, and the first build. Refuse a
`Bearer <literal>`, a `-----BEGIN` block, a bare 10-digit number, and secret-shaped assignments with
a literal value — distinguishing them from `os.environ.get("X", "")`, which is correct and must not
be flagged. **The F-185 phone gate already exists; this is that machinery, one pattern wider.**

**⭐2 · The F-363 repair, as ONE atomic step** — `HANDOFF_RUNBOOK…v161` restored to its full 7,607
bytes, its `MD5SUMS_ALL` row and its manifest row moving together. Done separately, Phase 0 halts.

**⭐3 · The staff advance policy document rebuilt** from `staff_ledger.py` and the D331 → D332 →
later trail. **Neither stored copy is to be trusted.** Owner-surfaced.

**⭐4 · The WABA rotation** — blocked on Ms. Khushi Jain's answer to one question: do old and new
tokens overlap? That answer decides whether this is a calm staged job or a timed change to four
places with patient messaging down between them. Inventory:
`claude/S231_WABA_TOKEN_ROTATION_INVENTORY.md`.

**⭐5 · F-368 hygiene** — six stale `.env` copies and three stale code copies in live folders on the
VPS. Not urgent; not to be touched mid-rotation.

**⭐6 · 1.7 the self-advancing renewals register** (F-360) — its clock is gone, both entries ruled by
D422, so this is now tidiness rather than rescue. Then the eight missing technical vendors,
Tailscale first.

**⭐7 · 1.9 the medical PC capture chain** (F-362) — still prepared, not applied.

**Also standing:** the Bitwarden consolidation (D421) after the rotation · the Apps Script MyOperator
values moved into Script Properties · the `_Infrastructure\Credentials\` plaintext folder · Phase 2.

---

## §3 · INSTALL DISCIPLINE — what this session adds

**Config before code, always.** Every kit this session wrote the new configuration BEFORE removing
the old default, so there was never a moment when a publisher had no value to use. Reverse that order
and you get a silent outage.

**Prove at the deepest layer available.** `is-active` proves a process started. `/proc/<pid>/environ`
proves it has what it needs. A log line the code prints itself proves it took the branch you wanted.
The full-message installer used all three, and the third is the one that would have caught a silent
fallback to name-only pushes.

**Refuse on drift, never overwrite it.** The full-message installer compares the live file against
the repository's pre-change bytes and stops if they differ, because copying over an unrecorded edit
destroys it silently.

**Never import a module from inside the repository.** `py_compile` is already forbidden there; import
does the same thing and leaves the same `__pycache__`. **It happened again this session** and the
publish gate caught it. Set `PYTHONDONTWRITEBYTECODE=1`.

---

## §4 · THE BOUNDARY — what is live, what is not

**LIVE on the VPS:** the rotated ntfy topics in `/root/wa/.env` (mode 600, the only store) ·
`clinic_watchdog.py` and `clinic_health_report.py` patched to read them · `freshness.conf` on the
system topic · `wa-notifier.service` carrying `EnvironmentFile` and no topic · `notifier_wa.py`
`08219ae8…` pushing the full message text.

**LIVE, unchanged, and deliberately untouched:** the staff ledger's ntfy path (its unit declares no
environment, so its `ntfy()` never publishes — nothing to rotate) · the ICICI bank ingest · the
callback tracker.

**NOT live:** `diagnostics-vps/clinic_timer_freshness.py` — scrubbed in the repository, but not
deployed on the box at all; superseded by the S230 freshness layer.

**OPEN AND NOT CLOSED:** **F-365.** The WABA token is contained, not revoked. **The published token
keeps working until MyOperator revokes it.** Everything else about that finding is preparation.

**Owed to the owner:** nothing that requires him to investigate. Four small actions, all in
`OWNER_TODO_LIVE`.
