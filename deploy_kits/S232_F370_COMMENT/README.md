# S232_F370_COMMENT — the comment that still stated a retired rule

**PREPARED, NOT APPLIED. NOTHING HERE IS INSTALLED, AND NOTHING SHOULD BE INSTALLED FOR THIS
ALONE.** There is no installer in this folder on purpose.

## What this is

`staff_ledger.py` — the live bytes, **v3.6-S225-LOANS-D374**, with **one comment block corrected**.

| | md5 |
|---|---|
| the LIVE file (`/root/staff_ledger.py`, kit `S225_LOANS_VIEW`) | `802577112e6db82bcf763d142efcd00c` |
| this file | `941524872d6add49ec16aebd0d56d370` |

## F-370 turned out to be TWO wrong statements, not one

The D331 header block above `advance_pct()` — **the block anyone reads to learn the rule** — carried
both of the errors that made the policy document wrong:

1. *"default 50; **Darpan 75, the owner's ruling**"* — **D352 (S204) retired that exception**, and
   **D425 (S232)** confirmed there is no grandfathering: 50% through August. D352's own lesson is
   the point — *an exception belongs in a settings row, never in a code fallback* — and this comment
   was the last place the retired exception still lived.
2. *"approval **refuses** until the signed written application … is uploaded"* — **amended by D374
   (S225)**: the checker may approve first and attach later, with `application_owed` on the row.
   **`decide()`, forty lines below, has carried the correct D374 note since S225.** The same file
   has said two different things for four sessions, and the wrong one is at the top.

**No behaviour was ever wrong.** The box has held `{"Darpan": 50}` throughout — that is how D352 was
able to measure the divergence in the first place. This is a records fault inside a code file.

## Proof that it changes nothing

- `diff` filtered to non-comment lines: **empty**. Every changed line begins with `#`.
- Both files compiled and their code objects compared — name, argcount, names, varnames and
  bytecode, walked recursively through all **312** code objects:

```
live  cc74f70bf96d7ab5bf937e74c65a6cd3
fixed cc74f70bf96d7ab5bf937e74c65a6cd3
IDENTICAL BEHAVIOUR
```

- `py_compile`: OK.

## How to use it

**This file becomes the new BASE.** The next kit that touches `staff_ledger.py` starts from
`deploy_kits\S232_F370_COMMENT\staff_ledger.py`, not from `deploy_kits\S225_LOANS_VIEW\staff_ledger.py`,
and its installer's currency gate keeps the LIVE pin `80257711…` as the expected before-value — the
live file has not moved and must not be assumed to have.

Installing this on its own would spend a VPS trip, a service restart and an owner action to change a
comment. **That is not worth it. It rides.**

---
*S232 · F-370 · prepared 08-Sep-2026. Recorded in `Staff_Advance_Policy_AS_BUILT_v1_S232` §10.*
