# HANDOFF RUNBOOK — v177 · S256 close · 14-Sep-2026

## §0 — WHAT HAPPENED

One attended chat, 14-Sep ~06:00 → ~12:15 IST. **Nine kits built, walked and installed: `S259` …
`S267`.** Every install was preceded by a walk that ran the real thing against a copy of the clinic's
own database, and every pin was read back from the box by the owner.

The morning closed Club C.2 (OFF switches) and Club C.3's manojz half (one settings file per
machine). The afternoon built the vendor payment chapter end to end. **Two findings were about the
record rather than the code** — F-472, a predicted pin recorded as live, and F-473, the assistant as
the faulty link in a byte relay — and **two were corrections the assistant made to its own work in
public**, F-477 (a bank account number written into a kit) and F-478 (formatting prettier than the
source).

**New fault codes:** F-472 … F-478. **New decisions:** D511 … D520. **No SOP change.**
**Surveillance scope unchanged.**

## §1 — MENTAL MODELS

- **The payment sheet is prepared first; the statement checks it.** The supplier-wise export is a
  verification step with a kept history of runs, not a gate (D514).
- **One account, one row, a pointer.** The bank's name and the bill's name are different strings;
  `purchase_vendor_alias` links them and nothing is copied (F-475).
- **The advice, the letter and the file are one artefact in three forms.** All three come off the
  locked sheet; the letter refuses an amount from the browser (D519).
- **A switch is per job.** Capture is never covered by "all" — an uncaptured Marg export is gone
  (D511).
- **A number never enters the repository.** It rides the install line into the database (F-477).

## §2 — THE LIVE BACKLOG

See `OWNER_TODO_LIVE.md`, refreshed at this close. ⭐1 opens on **Club C.4 (per-sender tokens,
folded into the owner's F-456 rotation)**, then the medical half of C.3, then the VPS-side OFF
switches, then the cheque register's own screen.

## §3 — INSTALL DISCIPLINE

Unchanged, with three additions this session:

- **F-474 — confirm the kit is in the publish that actually ran** before naming an install line. The
  publish output lists what it carried; a kit absent from it is a kit the VPS cannot see.
- **F-464 still stands**: every install line carries `cd /root/deploy/repo && git pull --ff-only &&`.
- **A kit that writes data seeds the walk's COPY first and the live database only after the walk has
  passed.** Proved by a deliberate wrong link at S263: 24 ok / 4 failed, file restored
  byte-identically, **database never touched**.

## §4 — THE BOUNDARY

`device_bash` was **unavailable all session** — the local Linux workspace failed to start (a Windows
update of 8-Sep is named in the error). Everything on manojz was done with the file-transfer tools
instead, which worked throughout. **"Does not mount" is not "unreachable" (S209) — and neither is
"the shell is down".** The medical PC remains reachable only through the Drive kit channel; the
Tailscale share is read-only.
