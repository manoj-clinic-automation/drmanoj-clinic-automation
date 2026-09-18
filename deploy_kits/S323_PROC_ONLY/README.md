# S323_PROC_ONLY — the page gets shorter, and the names read like the clinic's

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S323_PROC_ONLY/install_S323_PROC_ONLY.sh
```

## His words, 19-Sep, after S322 landed

> "the xray section is done, no need on page, obstructs flow · in cast / slab side column - no need to
> turn it off · consumables are same and to be accepted as such · each one has a display with its
> abbreviation first, and name in brackets as in A/E (Above elbow) · and in xrays, ask side to be
> there where relevant"

## What changes

**The X-ray list comes off the page.** It is finished, and twenty lines above the procedures were in
his way. The page opens on the procedures, with one line saying where the X-rays went and a link that
still opens them — fully editable — when he wants them.

**An asked side is a statement, not a switch.** A cast, a slab or an injection is always one side, so
those rows now just read `R / L`. Only a row that does *not* ask carries a small button, so he can
switch one on.

**The consumables are read-only.** They still show under each procedure with the sizes and how each is
asked, but the remove buttons and the add box are gone.

**The names read the way the clinic says them:**

```
A/K (Above knee) fibre cast      A/K (Above knee) fibre slab
B/K (Below knee) fibre cast      B/K (Below knee) fibre slab
S/BK (Short below knee) …        H/BK (High below knee) …
CYL (Cylinder) …                 A/E (Above elbow) …
B/E (Below elbow) …              S/BE (Short below elbow) …
SPICA (Thumb spica) …            U fibre slab / U fibre cast
ILI (shoulder) · ILI (elbow) · ILI (thumb) · ILI (trigger finger) · ILI (heel, plantar fasciitis)
```

**And the side flag on the X-rays, which S322 did not manage to set.** S322 reported *"X-rays that now
ask a side: 0"*, and its own safety rule is why: it only flagged rows still marked as the seed's, and
by then he had approved the whole X-ray list, so every row counted as his. The flag changes no name,
no price and no approval, so this kit sets it regardless of who last touched the row — while a **name**
he typed himself is still never overwritten. Thirteen limb studies ask R / L; the spines, chest and
pelvis-both-hips do not.

## Proof

`walk_s323.py` — **29 checks**, seeded in the state his box is actually in (fibre names, every row
marked as his). It renders the page through Flask and POSTs every button the way a browser resolves
them, and asserts each of the four removals, every renamed line, the side flags landing despite his
approvals, and that no price or approval moved.

Four negative controls: words he typed himself are kept, a colliding rename refuses and writes
nothing, and the **unpatched** page is shown still carrying both the X-ray list and the remove/turn-off
buttons — so the removals are measured against something real.
