# HANDOFF RUNBOOK — v178 · S257 close · 14-Sep-2026

## §0 — WHAT HAPPENED

One attended chat, 14-Sep ~18:30 → ~22:30 IST. **Four kits: `S268` · `S269` · `S270` · `S271`.**
Two of them installed on the VPS by the owner from one line each, walked **21/21** and **25/25**,
every pin read back from the box.

The evening had three parts. **The dead `device_bash` was answered by removing the dependency** —
the Cowork manifest rebuild, owed at two closes, now runs in the Windows python on manojz and
nightly at 03:10. **The owner named a problem that was the assistant's to fix** — 375 working papers
on his PC, 193 of them cited nowhere, and no way for him to know which mattered; `PAPER_POLICY_v1.1`
and one shelf answer it. **The cheque register closed the half of D513 that was never built.**

**Six findings, all six the assistant's own:** F-479 … F-484. **New decision:** D521.
**No SOP change. Surveillance scope unchanged.**

## §1 — MENTAL MODELS

- **A tool that needs a broken thing is a debt; a tool that does not is a repair.** The manifest
  rebuild was owed at two closes because it needed a POSIX shell. It now needs nothing that can break
  the same way, and it runs without being asked.
- **A walk is code, and its claims go stale exactly as a document's do.** Three times in one evening
  a check — not the code — was what was wrong. A check inherited from the previous kit asserts the
  *previous* change.
- **A check must never pass on an error page.** Asserting the *absence* of a string succeeds against
  a 500 body. Every page read goes through a gate that fails loudly first.
- **A delivery is proven by reading the bytes back**, never by the tool reporting success (F-481).
- **The most useful state of a register is the one where money is owed and nothing has been written.**
  Build for that state first; it is the one a naive query hides.
- **A cheque is written after the month locks.** A record of something that has already happened is
  not a change to the thing it records.
- **Telling the owner a path he does not need is homework, not information.**

## §2 — THE LIVE BACKLOG

See `OWNER_TODO_LIVE.md`, refreshed at this close. ⭐1 opens on **Club C.4 (per-sender tokens,
folded into the owner's F-456 rotation)**, then the medical half of C.3, then the VPS-side OFF
switches, then **the PWA reorganisation — which he has said he wants to be part of, and which needs
him talking rather than pasting.**

## §3 — INSTALL DISCIPLINE

Unchanged, with four additions earned tonight:

- **A patched copy of an app must sit in the app's own folder.** `purchase_app.py` resolves
  `purchase_schema.sql` from beside itself; a copy in `/tmp` makes every page a 500. The walk now
  refuses a `--file` anywhere else.
- **A refusal is judged by what it says, not by the status code it rides on.** `_refuse()` returns
  403 on this box.
- **A block must never extend the page-wide stylesheet.** Four screens grew by exactly 1,287 bytes
  the one time it did; the patcher now refuses it outright.
- **Every `device_commit_files` is followed by a stage-back and a hash.** Standing practice.

**F-464 still stands:** every install line carries `cd /root/deploy/repo && git pull --ff-only &&`.
The walk runs against a **copy** of the live database and the live file is replaced only after it
passes — proven twice tonight, when it did not pass and nothing was touched.

## §4 — THE BOUNDARY

`device_bash` **failed to start for the fourth session running** — the 8-Sep Windows update; the
shell answers `no Plan9 drive shares mounted` and cannot see `D:` at all. Everything on manojz went
through the file-transfer tools. **"Does not mount" is not "unreachable", and neither is "the shell
is down" — but from this close the manifest no longer cares either way.**

Computer control on manojz resolves a terminal only in **click** mode: it can see and click, and
cannot type. It is not a route for running commands, and the one action per machine still belongs to
the owner.

The medical PC remains reachable only through the Drive kit channel, so `marg_push.py` and
`marg_watch.py` stay unhashed and are said to be so (F-443).
