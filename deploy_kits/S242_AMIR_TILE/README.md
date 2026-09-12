# S242_AMIR_TILE — Amir's page gets a door, and it is his only one

**The owner, 12-Sep-2026:** *"allow him only the one u made today, forms and dnloads not needed for
him, Marg Purchases · Order Medicines · Stock Check · Scan Purchase is not for him for now, so park
these too, will decide these later."*

## What was wrong

`/finance/amir` — Amir's seven steps — went live at S241 and had **no tile anywhere in the portal**.
It could only be reached by typing the address. Measured, not assumed: the owner's own portal was
read live, and the owner's portal shows every tile there is.

## What changes

**One tile is added.** `Amir ka kaam` 🧭 → `/finance/amir`, *"Aaj ka kaam — 1 se 7 tak"*, section
*Money & Accounts*, `roles: ["doctor"]` like every other granted tile — so a lost or malformed
grants file leaves it with the doctor and nobody else.

**Amir's grants become one line.** `extra: ["Amir ka kaam"]`, and
`mask: ["Attendance", "Staff Register", "Forms & Downloads", "Scan Purchase"]`. Stock Check, Marg
Purchases and Order Medicines leave his `extra`; the two staff-role tiles come off by mask. He is
left with **exactly one tile**.

**PARKED, NOT REMOVED.** Every one of the five stays in `portal.py` with its roles unchanged, and
every other person's screen is byte-for-byte what it was. Bringing any of them back for Amir is one
line in `tile_grants.json`. The pages' own gates — the medical `unit_role` above all — are
untouched and still decide what he may *reach*; this file only decides what he is *shown*.

## Pins — two files, and they move together

| file | from | to |
|---|---|---|
| `/root/portal/portal.py` | `ed558b3663c3dd100a24f58aafc32363` | **`d08721f69bc7c3e3a79a50192b20affb`** |
| `/root/portal/tile_grants.json` | `710f13bd14ebfdf8108372c81414db1e` (v11) | **`7e7445a37ace9ea7c8218d598a05b81d`** (v12) |

A grant matches a tile by **name**. A grant with no tile shows nothing; a tile with no grant reaches
nobody but the doctor. The installer gates both and restores both.

## Proof

**`EVIDENCE_portal_reconstruction_S242.txt`** — the repository holds no full copy of the live
`portal.py`, so the chain was replayed from the S204 base through twelve anchored patchers.
**Twelve declared pins, twelve exact reproductions**, landing on the pin the S239 kit declares for
the live file. That is why this kit can gate on a hash instead of asking the owner to read one.

**`EVIDENCE_walk_S242_AMIR.txt`** — not a reading of the JSON: `portal.py` itself is imported (its
own "every tile is grouped" assert is check 0) and **portal's own `_visible_sections`** is asked
what each person is shown, with the v12 file beside it. Twenty-six checks, all green:

- Amir sees exactly `['Amir ka kaam']`, and it points at `/finance/amir`
- all five parked tiles are gone for him
- all five are **still defined with their roles unchanged**
- Shavez, Shivani, Alisha, Darpan and a bare staff login are unchanged, tile for tile
- the doctor keeps everything, the new tile included
- **fail closed:** with no grants file at all, Amir loses the tile and the doctor keeps it

The same walk runs **again on the box**, against a copy of the box's own `portal.py`, before a real
file is touched — and the copy must hash to `d08721f6` first.

## Install — one line on the VPS, after the publish

```
bash /root/deploy/vps_deploy.sh S242_AMIR_TILE
```

Reverse is printed by the installer: both backups, one line.
