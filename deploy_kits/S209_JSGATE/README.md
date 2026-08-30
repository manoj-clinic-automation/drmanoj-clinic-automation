# S209_JSGATE — refuse a page whose JavaScript does not parse

**Raised by the S209 incident: the owner's money console sat on "loading" in every
section for a day, because of one apostrophe.**

`finance_approvals.html` contained `h+='... the same patient's own earlier sale bill ...';`
— an English possessive inside a single-quoted JS string. The string ends at `patient`;
the rest is a syntax error; and a syntax error anywhere in a `<script>` block stops the
**whole block** from running. So no section failed — none of them ever started.

## Why no existing gate caught it

- the kit's `SUMS.md5` passed — the file **was** delivered intact. Intact is not valid.
- the finance smoke suite passed, 721 checks — it tests routes and payloads, not pages.
- the close recorded the console live and verified — by hash, which is exactly right and
  exactly blind to this.

**Nothing in the toolchain has ever parsed a page's JavaScript.**

## Files

| file | what it is |
|---|---|
| `js_gate.py` | the gate. Extracts inline `<script>` blocks (skips `src=`), runs `node --check` on each. |
| `SWEEP_LIVE_PAGES.sh` | read-only sweep of a served page directory on the VPS. |
| `finance_approvals.FIXED.html` | the corrected console page, md5 `da82366c43efe43935fa5781e3bcb5ab` — **what is live since 30-Aug-2026.** |

## Exit codes — three, not two

    0  every block parsed
    1  a block FAILED -- refuse the install
    2  the gate COULD NOT RUN (no node) -- UNKNOWN, never a pass

The third exists because of **F-119**: a gate that exits on a warning is a silent pass.
A gate that cannot run must not look green.

## How to use it

Before installing any page:

    python3 js_gate.py path/to/page.html    # exit 1 = do not install

Wired into an installer, one line beside the existing `md5sum -c`:

    python3 "$HERE/js_gate.py" "$HERE/page.html" || { echo "!! refusing"; exit 1; }

## Proofs (run 30-Aug-2026, all landing)

- selftest **6/6**, including the real S209 fault reproduced verbatim and caught
- the actual broken file → **REFUSED**, exit 1, naming the block
- the fixed file → **PASS**, exit 0
- sweep of all 36 pages in `deploy_kits` carrying inline script (42 blocks): **exactly one
  failure — this one.** No other page is silently broken.

## ⚠ `S208_CONSOLE` STILL CARRIES THE BROKEN PAGE

`deploy_kits/S208_CONSOLE/finance_approvals.html` (`c5fd0e78…`) is the un-fixed file.
**Re-running `install_console.sh` would put the outage back.** It has NOT been repaired
here: repairing a published kit's contents is an owner ruling, not a tidy-up (the
established rule for the six red kit gates). Use `finance_approvals.FIXED.html` above,
or rule that S208_CONSOLE be corrected and re-hashed at the close.

*S209 · 30-Aug-2026 · nothing in this kit is installed; it is a gate and a record.*
