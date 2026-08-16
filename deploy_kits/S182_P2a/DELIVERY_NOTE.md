# S182_P2a — F-98: the portal must not assume "doctor"

**One file changes: `/root/portal/portal.py`. No tiles move — the gate proves the tile
set is byte-identical to what is live now. Auth behaviour only.**

---

## The fault

`_is_doctor()` carried this, in its own words:

> *"Mirror home(): a trusted device with no SSO user is treated as the doctor."*

`_authed()` accepts a valid SSO cookie **or** `_is_trusted()` — the legacy PIN-era
device cookie, kept for the SSO transition. Put together: a browser still holding that
old device cookie, with **no SSO session at all**, was authenticated *and* treated as
the doctor. Not just tiles — every `@doctor_required` route: the Clinic Gist, the Call
Console, the per-staff coaching report. Patient-data surfaces.

The most likely browser in that state is the clinic PC, which reception shares.

This is **F-84's pattern** — *anything that grants identity for convenience must be
opt-in; the production default must be closed* — which you minted on the finance app at
S179 and fixed there. It was still sitting in the SSO broker, which is the front door to
everything else.

It also explains the missing tiles: with no identity, `USER_TILE_EXTRA` had no username
to match, so **every grant-only tile vanished** — the two new clinic tiles *and* "Manage
Users", which has been grant-only since S164. The tiles were never broken. The page
simply did not know who was asking.

## The fix, and why it cannot lock you out

Identity is now **proven, never assumed** — but the new behaviour keys off
`_sso_ready()`, not off the cookie:

- **Broker mode available** (today): an unidentified caller is sent to sign in, and
  `_is_doctor()` requires a verified SSO user with `role=doctor`.
- **Broker mode unavailable** (portal secret unreadable, or a pre-SSO estate): the
  legacy device-trust path is **untouched**.

That second branch is deliberate. **D264** requires a verify-shim to be inert on
failure — no edit may remove existing access. A naive fail-closed change would lock you
out of your own portal the first time `portal_config` broke. This one degrades to the
old behaviour instead.

**What you will notice:** anyone still relying on a legacy device cookie has to sign in
once. That is the intended effect. "Forget all devices" in the portal footer forces it
deliberately if you want a clean sweep.

## The gate — 48 checks, and it was proven to bite

Run **before** anything is touched, under the same venv interpreter gunicorn uses.

- **Identity matrix** — all four combinations of (broker ready?, SSO user?) asserted
  against `_is_doctor()`, including the D264 branch: *broker down + no SSO user → still
  doctor*, so the inert-on-failure guarantee is itself a test.
- **Served HTML (D307c)** — the portal page is genuinely rendered for manoj, bhawna,
  shavez, alisha, shivani and darpan, and the tiles are read out of the HTML each would
  receive, presence **and absence**. This is the block that was missing when we could
  not explain your empty portal; it now answers that question mechanically.
- **Regression** — the tile list must be byte-identical to live.

Proven by running it against the current live file: it fails on exactly two checks —
`_is_doctor` returning True with no SSO user, and `/portal` serving 200 instead of
redirecting. A gate that cannot fail is not a gate.

Two of my own assertions were wrong on the first run and the gate caught them: a bare
`">Clinic<"` match also hit the **section header** "Clinic", and I had wrongly expected
Darpan to see Sanjeevni Medicos (he is `staff`; that tile is `doctor`). Both were my
errors, not the code's — worth knowing, because the tile named **"Clinic"** does collide
with the section named **"Clinic"** for a human reader too. Say the word and I will
rename it.

---

## To install

```
bash /root/deploy/vps_deploy.sh S182_P2a
```

Refuses unless live `portal.py` is `410388da…`. Rollback at
`/root/portal/portal.py.bak_S182P2`; a red install restores it, restarts, and re-checks
health before reporting.

---

*Kit built S182 · gate 48/48 offline · candidate `2784b1cb…` · built on live `410388da…`*
