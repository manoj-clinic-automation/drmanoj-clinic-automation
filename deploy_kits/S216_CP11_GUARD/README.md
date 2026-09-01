# S216_CP11_GUARD — CP-1.1 step 1: the wrong-opening guard

**Page only.** `casepack_portal.py` is unchanged and is NOT installed; the copy
here is byte-identical to the live pin `3146bdbf…` and exists only so the
selftest can import it.

## What it fixes

At S215 the app printed the **elective** hip opening — *"कूल्हे में लंबे समय से
बहुत तकलीफ है… जोड़ काफी खराब हो चुका है"* — for a month-old **fracture neck of
femur**, while the polio module in the same document said *fracture neck of
femur*. Two contradictory clinical statements in one signed page.

Two causes, both in the page:

1. `cpGuessProc()` matches on the **estimate title only**. "Total Hip
   Replacement" contains neither *fracture* nor *neck*, so it returns `thr`.
2. `fmApplyOpening()` inserts fracture wording by rewriting the phrase
   `टूट गई है।` — which **no elective opening contains**. The fracture panel
   therefore had nothing to attach to. This is why the fracture could not be
   added at all.

Nothing cross-checked the two. 32 selftests and 17 render checks all passed —
the render test hand-picks `thrneck`, so it could never have seen it.

## What this kit adds

- A status strip above **Generate consent** that always says which opening is
  chosen and what the app is reading from the case.
- A **refusal**: if the case carries fracture-only signals and the chosen
  opening is a degenerative/elective one, the consent will not generate.
  The correct templates are offered as one-click buttons.
- An **override** — his choice always wins — written into `cs_change_note`
  as `[opening-guard overridden: <key>]`, so it can never be silent.

Fracture-only signals: open/compound · comminution · segmental · articular ·
additional fractures · a chosen fracture pathway · bone-loss · polytrauma ·
a fracture polio module · a bone reading *गर्दन*.
Deliberately **not** used: osteoporosis, geriatric, DVT/chest risk — all true
of many correct elective replacements. Proven by test E below.

**No consent wording is changed by this kit.** Tone, flow, transliteration and
the dropdown colours are steps 2–5, not this one.

## Proof

| gate | result |
|---|---|
| `selftest_casepack.py` | **32/32** — unchanged |
| `RENDER_TEST_casepack.py` | **17/17** — unchanged |
| `GUARD_WALK_cp11.py` (new) | **19/19** |
| `REVERSE_PROOF_cp11.py` on the **old** page | defect reproduced: consent generates with no objection, says *worn-out joint*, never says *broken* |

The guard walk includes false-positive controls (E) and a fracture-template
control (F): a correct elective THR, including one with osteoporosis and
geriatric ticked, is never blocked.

Playwright is not installed on the clinic PC or the VPS; both browser scripts
exit 2 (SKIP) there and the gate treats SKIP as not-a-FAIL. They were run in
the assistant's environment against these exact bytes.

## Install

    cd /root/deploy/repo && git pull && bash deploy_kits/S216_CP11_GUARD/install_cp11.sh

Base page `903b915e…` → new page `1e4d25d4… (full row in SUMS.md5)`.
