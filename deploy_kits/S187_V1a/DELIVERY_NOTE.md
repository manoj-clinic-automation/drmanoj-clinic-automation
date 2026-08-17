# Kit S187_V1a — verify_live_pins v1.2 + gen_live_pins v1.2 (F-117 closed structurally; F-122)

**Session 187 · 17 Aug 2026 · Runbook v121 item 0, executed — and the fault it names fired live first.**

## What this fixes

**F-117 / F-122.** The v1.1 checker printed `source : VERIFIED against the manifest … (md5 …)` on the
strength of the word `yes` — hashing nothing. The md5 it displayed, `78881ddd…`, matches **no file in
any of the repo's 157 commits** (V1b's `04eff42c…` is the same). Cause, structural: the manifest's
self-row is *"recomputed last, each EOS"*, so the whole-file hash the generator computed at generation
time described a transient PC-side state, edited again before every push. **Every `--manifest`
generation minted a phantom.**

## What ships

| file | md5 | what |
|---|---|---|
| `verify_live_pins.py` | `b4da75ec19f8c7fa613fb9962a272a1a` | **v1.2** — proves the attestation ON THE BOX from `/root/deploy/repo`: hash-hunt for the pinned Register in the canon folder (D188), parse the manifest beside it, confirm its CURRENT row pins that hash. VERIFIED only after proof; otherwise the reason, and AMBER. Selftest 43/43. |
| `gen_live_pins.py` | `9c402c366e7c902f27047a2014062107` | **v1.2** — never writes the manifest's whole-file md5 again; writes `manifest_current_register_pin`, the stable value that IS the claim. Selftest 22/22. |
| `live_pins.txt` | `b2ccf4e140b27f2f331c778972cfb959` | regenerated from **Register v5.13** (in this kit). Exactly ONE row differs from the list the box holds: the checker's own pin, moved to its v1.2 hash. Stamped `pending` — the manifest row lands at the S187 close. |
| `KB_Register_v5_13_S187.md` | `3f1c46d8148586decccd77816df7e3de` | the draft Register this list was generated from, shipped for provenance so its `source_md5` is findable in the repo — no more `ff509b01…` mysteries. Canonical at the S187 close. |

## Expect after install

**match 42 · drift 0 · missing 0 · VERDICT: AMBER (pending)** — by design, the `S186_V1a` precedent.
GREEN returns at the S187 close, when the manifest pins v5.13 and the list is regenerated with
`--manifest` — and from then on every GREEN is **proved on the box**, not attested.

## Rehearsed offline before delivery

Installer run three ways against throwaway targets holding the box's exact current bytes
(`ea3677b9…` / `bf300632…` / `63d4d9ce…`): normal install (all gates pass, `*.bak_S187_V1a` kept,
files placed) · tampered target (currency gate RED, exit 1, **nothing changed**) · re-run
(idempotent). New checker proved against the **real** repo clone: the real manifest parses to exactly
`1da5b0c4…` despite its two "(pre-…)" quirk rows; the V1c list verifies; F-110's draft hash refuses.

## Install

```
bash /root/deploy/vps_deploy.sh S187_V1a
```
