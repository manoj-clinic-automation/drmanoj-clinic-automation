# S195 — ToMedical delivery pipe: BROKEN by design, needs a medical-side puller

**Confirmed 23-Aug by live probe.** The Drive→medical delivery leg cannot work as built:

```
23-08 06:50  leg reached, DRIVE=H:\My Drive\Clinic Data Archive
23-08 06:50  ToMedical folder VISIBLE
robocopy  H:\...\ToMedical  ->  \\100.119.151.40\DDrive\SendToClinic\FROM_CLINIC
2026/08/23 06:50:05 ERROR 5 (0x00000005) ... Access is denied.
```

## Root cause

The medical PC's share (`\\100.119.151.40\DDrive`) is **read-only from manojz** — by
design: the whole margsync architecture is manojz *reading* medical (the pull). So
**manojz can never write to medical.** This is the same wall that blocked the owner's
manual `Copy-Item` today, and it means:

- The `ToMedical` Drive folder + the pull-bat delivery leg (added earlier this session)
  **never delivered anything** and never could.
- Anything that must reach the medical PC — the correction workbook for Amir, Sanjeevni
  bank statements, the watcher kit — **cannot be pushed from manojz or from Drive-via-manojz.**

## What was done now

The futile delivery leg was **removed** from `PULL_FROM_MEDICAL.bat` (it was returning
ERROR 5 every 10 minutes). Backup: `.before_S195_captured`. A comment in the bat records
why. The `ToMedical` Drive folder is harmless and left in place for the future puller.

## The fix (not built — backlog)

Delivery TO the medical PC must be a **medical-side PULL**, since medical→internet and
medical→Drive both work (the medical PC already POSTs to the VPS via GUARD_AND_SEND).
Options, cheapest first:
1. A tiny scheduled task ON the medical PC that pulls new files from the `ToMedical` Drive
   folder (via a share-link download, `rclone`, or Drive-for-Desktop if installed).
2. Serve them from the VPS finance app behind the SSO cookie; the medical PC fetches on a
   schedule (heavier, but reuses the existing medical→VPS trust).

**Consequence for the statement chain (`S195_Bank_Statement_Chain.md`):** the
`Bank_Statement_Filer` copies Sanjeevni statements to `ToMedical` expecting they reach
Amir. **They currently do NOT reach the medical PC** — they sit in Drive. Amir's copies
wait on the medical-side puller. The accountant email leg and the archive leg are
unaffected and working.

**Flagged to the Auditor** (slice 4, recovery/SPOF): manojz is a single machine that can
only *read* medical; the one-directional trust means every "deliver to medical" feature
built this session assumed a push that the OS forbids. Worth a systematic check of what
else assumes it.
