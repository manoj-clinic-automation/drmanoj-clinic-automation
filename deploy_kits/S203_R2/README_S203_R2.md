# S203_R2 — the pull tells the truth, and keeps a record

**Two files change, both on manojz.** Nothing on the medical PC. Nothing on the VPS.

## The two faults, which are one fault

**1. `-- ok` was written unconditionally.** It sits on a straight-line path with no error
test above it, so capture, routing, sending and the picture could all have failed and it
still said `ok`.

It is worse than a cosmetic lie. `pipeline_status.py:122` computes

    "ended_ok": any(l.startswith("END") and l.endswith("ok") for l in tail)

and posts that to the clinic server. **So the server was told the pipeline was healthy by a
word that was always written.** On 26-Aug the feed was dark for 8 hours 40 minutes and this
said `ok` every ten minutes throughout.

**2. The pull kept no log at all.** `PULL_HIDDEN.vbs` ran it hidden with nothing
redirected, so every line describing what happened — what was captured, what was routed,
what was sent, why a send failed — was destroyed, every ten minutes.

Together: **the pull could not tell you what it did, and asserted it went well.**

## What changes

| file | was | now |
|---|---|---|
| `PULL_FROM_MEDICAL.bat` | `92f03999d0a14d00b7f552dbb4d44c05` | **`cfb8b13d028a3bdc69a70701056392ec`** |
| `PULL_HIDDEN.vbs` | `9a3ba9ba3bb7376bd166f12624d282c3` | **`084fc4523b0e855c8d29b54c144bb60b`** |

- Every work step's exit code is captured — capture, rescan, send, picture.
- The END line is **earned**: `-- ok` only when all four are clean, otherwise
  `-- PROBLEM: capture=1 send=2`, naming what failed.
- One outcome line per run in `_logs\pull_YYYY-MM.log` — the first history this pull has
  ever had.
- The full console output goes to `_logs\pull_console_YYYY-MM.log`, one file per month.

**`pipeline_status.py` is deliberately NOT touched.** It stops reporting `ok` on its own,
because the word is no longer there. One change, both surfaces.

## A trap caught in my own edit, worth recording

The first draft ended a line with `%PROBLEMS%` immediately before `>>`. **A digit before
`>` is read by cmd as a stream number** — and the file already carries a comment saying
exactly that about its own START line. The redirect is now written first, as the original
does. *The warning was in the file; I nearly walked past it.*

Also found: **the live `.bat` has mixed line endings**, some CRLF and some LF. Assuming one
of them made three anchors silently fail to match. Every edit here was applied against the
ending the anchor actually uses.

## Proven before you install it

- **Reverse application on both files** — strip exactly what was inserted and the
  reconstructions hash to `92f03999…` and `9a3ba9ba…`, the live pins, exactly.
- **The installer proves it end to end rather than trusting the copy:** it runs a real pull
  in front of you and requires an `END` line, then **launches the hidden path and requires
  the console log to appear and be non-empty.** A malformed redirect in the `.vbs` would
  stop the pull running at all, silently — so it is not left installed unproven.
- Any gate fails → **both** originals go straight back.

## To install

Double-click, on **manojz**:

    D:\Downloads\margsync\_kits\S203_R2\INSTALL_S203_R2.bat

It takes about a minute, because two of those steps are real runs.

## One thing to know afterwards

The console log grows — roughly 10–15 MB a month, on a disk with 30 GB free. It rotates
monthly by itself. Delete old months whenever you like; nothing reads them but us.
