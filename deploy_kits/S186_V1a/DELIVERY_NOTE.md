# Kit S186_V1a — the live-pin checker learns to distrust its own source

**Session 186 · tooling only · read-only on the box · nothing live touched · no service restarted**

## What went wrong (F-110)

`/root/deploy/live_pins.txt` — the list this box has been held to since S183 — declares in its
own header:

```
# source: KB_Register_v5_5_S183.md
# source_md5: ff509b01dd175d38753728b5afd16baa
```

**The canonical v5.5 is `3cad79e6…`, and no file anywhere in the repo hashes to `ff509b01…`.**
The list was generated mid-session from an intermediate draft that never became canonical, and it
still carried the pre-S183 values for two Marg files.

So at the S186 open the checker reported three DRIFT reds and **two of them were false**: canonical
v5.5 already records `marg_report.py` = `829f4344…` and `marg_backfill.py` = `fa33ec8a…`, exactly
what the box reports. The record was right. The checker was behind it.

The tool printed that `source_md5` in every run, for three sessions. Nothing compared it to
anything. **Reporting is not enforcing** — and this is F-107's absence-blindness a third time, now
inside the tool built to close F-97.

## What went wrong again (F-111) — found while fixing the first

The pin list had not been regenerated since S183, so three later changes to the Register's
live-file table were never tested against the tool that consumes it. All three were latent:

1. The two `*(applied marker; no file md5)*` migration rows added at S185 **halt the generator
   outright.** Register v5.6 could not have produced a pin list at all.
2. The `*(superseded)*` rollback row added at v5.6 was read as a **second live pin for the same
   path** — `finance_app.py` held to two hashes at once, one of which could only ever be DRIFT.
   A red that can never go green is the halt that gets waved through (D316).
3. Nothing refused two pins for one path.

**A generated artefact that is not regenerated every session is not a check, it is a souvenir.**

## What this kit changes

**`verify_live_pins.py` v1.0 → v1.1** — the pin list must now carry an attestation:

| header | behaviour |
|---|---|
| `register_pin_verified: yes` | normal run |
| `register_pin_verified: pending: <reason>` | runs, loud banner, **verdict AMBER — never GREEN** |
| absent, or anything else | **refuses to run, exit 2** (`--accept-unattested-pins` overrides) |

**`gen_live_pins.py` v1.0 → v1.1** — fails closed on its own source:

- `--manifest CANONICAL_MANIFEST.md` → refuses unless the Register you hand it hashes to the md5
  the manifest pins as **CURRENT**. A draft cannot become a pin list by accident any more.
- `--allow-unpinned-register "reason"` → the only other way in, and it costs you a written reason
  that is stamped into the list and downgrades every later verdict to AMBER.
- `*(superseded)*` rows are **dropped, loudly** — printed every run, never silently skipped.
- two pins for one path **halt the run**.
- a row may declare *no file md5* **in words** (applied migrations → BLIND); a **silent** omission
  still halts (D166 — UNKNOWN is a correct entry, but it has to be written down as UNKNOWN).

**`live_pins.txt`** — regenerated from **KB Register v5.7**. Diff against the list on the box:

```
- VPS 86382f62…  /root/finance/finance_app.py      + VPS c66bec2b9e…  (completed from the box, F-109)
- VPS 28b47d44…  /root/finance/marg_report.py      + VPS 829f4344…    (false red, record was right)
- VPS e101c595…  /root/finance/marg_backfill.py    + VPS fa33ec8a…    (false red, record was right)
                                                   + VPS ce36dbf1…→ea3677b9…  the checker itself
                                                   + BLIND × 3        migration markers
                                                   - the duplicate finance_app pin (F-111)
```

40 VPS rows · 8 BLIND · 1 superseded row dropped.

## Expect AMBER on the first run — that is the tool being honest

Register v5.7 is authored this session; its manifest row does not exist until the S186 close. The
list is therefore stamped `pending` and v1.1 will refuse to say GREEN. It flips to GREEN when the
list is regenerated with `--manifest` after the close rebuilds the manifest.

## Safety

- Read-only on every live file: hashed, never opened for writing. No service restarted.
- **Currency gate (F-97):** refuses unless the live checker is `ce36dbf10e…` (v1.0).
- Both selftests (29/29 and 19/19) run **before** anything is placed.
- Previous checker, generator and pin list are kept as `*.bak_S186_V1a`.
- Nothing to roll back — but if you want the old state, copy the three `.bak_S186_V1a` files back.

## Install

```
cd /root/kits/S186_V1a && bash install_v1a.sh
```

Send the output back whatever colour it comes out.
