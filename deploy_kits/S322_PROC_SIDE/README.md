# S322_PROC_SIDE — the procedures, section wise

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S322_PROC_SIDE/install_S322_PROC_SIDE.sh
```

## What he asked for, 19-Sep

> "NOW GIVE ONLY THE PROCEDURES, SECTION WISE, WITH FIBRE WORD IN ALL CAST AND SLABS, AND EACH
> VARIANT IN PLASTERS SHD HAVE CAST AND SLAB, AS BOTH CARRY DIFFERENT CHARGE, AND THE ILI SECTION
> SHD HAVE RIGHT / LEFT SIDE OPTION, AND SO SHD BE FOR THE XRAYS WHEREVER APPLICABLE"

## What it does

**Cast / slab — ten sites become twenty lines**, each with the word *fibre*, so the two forms can
carry their own charges:

```
Above knee fibre cast        Above knee fibre slab
Below knee fibre cast        Below knee fibre slab
Short below knee fibre cast  Short below knee fibre slab
High below knee fibre cast   High below knee fibre slab
Cylinder fibre cast          Cylinder fibre slab
Above elbow fibre cast       Above elbow fibre slab
Below elbow fibre cast       Below elbow fibre slab
Short below elbow fibre cast Short below elbow fibre slab
U fibre slab                 U fibre cast
Thumb spica fibre cast       Thumb spica fibre slab
```

The seeded line is **renamed** (never replaced) and its twin is **added**, with the same consumables
copied across, so his fibrecast / roller / padding / stockinette rulings hold for both forms.
Clavicle bandage, the five ILI lines and Dressing stay one line each.

**Right / left is a marker, not two more rows.** A left and a right knee cast are the same line at the
same charge, and which side it was belongs to the visit — so each line carries "asks R / L", he can
flip it on any row from the page, and the chamber screen asks at the time. Turned on for all ten
plaster sites (twenty lines), the five ILI lines, and the limb X-rays — knee, K/S, ankle, foot,
shoulder, wrist, elbow, leg, hand, toes, thumb, forearm, clavicle. **Not** the spines, chest or
pelvis-both-hips: there is no side to ask.

**Procedure prices are left empty.** He has not stated them and an invented number would be worse
than a blank he fills; the page already counts a blank as waiting for him.

## Proof

`walk_s322.py` — **30 checks** on a copy of the live module and scratch databases. It asserts each of
his three rules (fibre in every cast and slab · every site present as both · side on the right lines
and not on the wrong ones), that the new slab line inherited the consumables, that no price was
invented, that nothing was deleted, and — following S321's lesson — it **renders the page through
Flask and POSTs every button the way a browser resolves it**, including the new Side toggle, which it
turns on and off again.

Four negative controls: a line he renamed himself survives untouched, a line he touched is not
re-flagged, a name collision refuses and writes nothing, and a database without the new column is
refused with a plain reason instead of a crash.
