# S209_LEDGERMSG — F-246: the warning that kept accusing the owner

## The fault, in one sentence

`api_ledger_check` told the owner to *"record it as an owner transfer below"*, and
`api_transfer` writes to a different table — so doing exactly as instructed could never
clear the message, and it went on saying *"the transfer-out was never saved"* after he
had saved it correctly.

- the check counts rows in `cash_movement` (the day ledger)
- an owner transfer is written to `cash_custody_event` (the custody record) — **by
  design**; its own docstring says it records custody and never moves money

Both behaviours are right. Only the sentence is wrong.

## What this changes

**One insertion, inside the read-only reporting function only.** When custody events
exist for the date, that one sentence becomes:

> "No cash_movement row for 2026-08-27, so the day ledger still counts this cash in the
> drawer. Your override below records where it actually went — dated, signed, in the
> custody record."

**Corrected by the owner, S209:** an earlier draft said *"an owner transfer is a custody
record, not a day-ledger movement"*. He was right to reject it — **it IS a cash movement in
real life**, drawer to Dr Bhawna. The true statement is narrower: no row was written into
that day's ledger. The wording now says only that.

**With no custody event the original instruction is untouched** — it is correct there.
No other message is altered. No write path, no schema, no query changed.

## Safety

- anchored on one exact string; **refuses** if absent or if it appears twice
- already-patched is detected and skipped — safe to run twice
- timestamped backup before writing
- `py_compile` after writing, and **the original is restored automatically if it fails**

## Proof

- **selftest 10/10**, including: insertion lands before the anchor · the result compiles ·
  running twice is a no-op · a file without the anchor is refused rather than guessed at ·
  two anchors refused as ambiguous · **with a custody event the sentence is rewritten and
  names the date · with none the original survives · no other message is touched**
- **dry-run against BOTH live candidates** — `S208_CONSOLE`'s and `S208_LEDGER3`'s
  `darpan_app.py` — patched cleanly and parsed. Whichever is on the box, the anchor is
  there. If it is neither, the patch refuses and changes nothing.

## Install — VPS, one line at a time

```bash
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```bash
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S209_LEDGERMSG/patch_darpan_msg.py /root/finance/darpan_app.py
```
```bash
systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service
```

A restart IS needed here — this is Python the app holds in memory, unlike a page, which is
read from disk on every request.

*S209 · 30-Aug-2026 · live financial code: one message string, in a function that only reads.*
