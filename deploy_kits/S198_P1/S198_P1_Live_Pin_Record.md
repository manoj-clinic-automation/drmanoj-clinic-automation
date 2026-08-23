# S198_P1 — live pin record (recorded AS IT MOVED, F-97)

**23-Aug-2026 · Session 198 · kit `S198_P1` (v2 payload, v3 installer) INSTALLED GREEN on the box.**

| file | was | now |
|---|---|---|
| `/root/portal/portal.py` | `ee749cd9f3ac1294aab0d13ce069efc1` (S196_HLT2) | **`dc093f1f83598b4e1927c2caee639fc7`** |

## What the kit is

The owner-approved (D307 preview, two rounds) portal HOME revamp: dark scheme kept (owner ruling
23-Aug — the warm-paper design language stays finance-side); Portal Health hero + 3 live chips
(doctor-only, fail-soft, reuses the checker-only `tile-summary` + `review-counts` fetches, no new
server route); compact half-height tiles, one screen on a PC; 46px floating back-to-top; tile order
ruled by the owner (Console+Tracker together · GMB up · Case Pack after the WhatsApp cluster —
gate-asserted on served bytes); NEW group **Staff** (Attendance→Register→Salary→Ledger with
relationship subtitles); Clinic-PC tools render as the migration-queue chip row (pc gating
unchanged); retired stale held tiles (Ayushman Finder + Surgical Estimate → live inside Case Pack;
WABA Send = Send WhatsApp; Nutrition/Physio folded into Vitals & Plan); renamed UPI Reconciliation →
**UPI Sheet** (lab + legacy; retires when the lab module lands); NEW tiles **Payment Register**
(capability URL `PAYMENT_REGISTER_URL` in portal_config.py — MANUAL until the owner pastes the
sheet URL) and **Forms & Downloads** (held; flips at A3). PAGE_HEAD untouched — login/console/
gist/digest/staff-report/users pages byte-identical.

## Proof chain

Gate `gate_S198_P1.py` **127/127 GREEN** offline AND on the box before the swap (five identities;
masks/grants/URLs proven against the live baseline; order + dark + toTop asserted on served HTML).
Negative controls: the gate refuses the old bytes; the installer's step-8 render check fails on the
old bytes (toTop + hero absent). `py_compile` + `pyflakes` clean. Backup
`/root/deploy/_backup_S198_P1_20260823_152820`.

## Candidate finding for the close (assistant's call per the S191 precedent)

**The v2 install went RED at its own probe step and rolled back cleanly — the fault was the
INSTALLER's, F-106 family:** step 7 gated on HTTP 200/302 from `http://127.0.0.1:8090/portal`, a
response shape never measured on this box, which answers **301** to plain-HTTP probes there for old
and new bytes alike (the S196_HLT2 installer received the same 301 and only printed it). Fixed in
installer v3: probes informational-only; the serves-the-new-page proof moved to the app's own
render path on the installed bytes. RULE: an installer probe's expected code is measured on the
box or it is printed, never judged.

## Owner residual (open)

Paste `PAYMENT_REGISTER_URL = "<sheet url>"` into `/root/portal/portal_config.py` + restart
`clinic-portal.service` → the Payment Register tile goes live (MANUAL until then).

*KB Register live-file table: update the `/root/portal/portal.py` row to `dc093f1f…` at the next
fold; `live_pins.txt` regeneration (A8) owed at the close. This record is filed to the repo kit
folder as well — the F-107 condition closed same-day.*
