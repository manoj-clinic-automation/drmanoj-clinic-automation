# S262_PAY_TILE — the Vendor payments dial

**What it does.** Adds ONE tile to the portal: **Vendor payments**, in
**Money & Accounts**, straight after **Marg Purchases** — because the two are read
together: what came in, and what is owed for it. It opens the page S261 built:

```
https://followup.dr-manoj.in/finance/purchase/page/pay
```

That address is the stable one. It always lands on the newest month; no date to type.

**Who sees it.** In `portal.py` the tile carries `roles: ["doctor"]` — the owner, always.
It is granted **by name** to **shavez** in `tile_grants.json` v17, and to nobody else.
So a lost or malformed grants file leaves the tile with the owner alone: fail closed for
staff, never locked out for the doctor. Every tile since S223 works this way.

**No second page was built for Shavez.** The page's own gate is the medical `unit_role`,
unchanged: a **viewer** sees the whole sheet read-only — he can read the NEFT list to
carry into the advice file and the cheque list to write out, but he cannot type a
carry-forward, cannot run the verification, and cannot lock the month. If he is ever
made a *maker* in the medical unit, that is the line to reconsider — not this one.

## The two files move together

A grant matches a tile **by name**. A new grants file beside an unpatched `portal.py`
grants nothing; a patched `portal.py` beside the old grants file shows the tile to the
owner alone. So the installer refuses unless **both** are at their from-pin, and rolls
**both** back byte-identically if anything fails.

| file | from | to |
|---|---|---|
| `/root/portal/portal.py` | `d0f126a3815a4c7e24960a15f1951857` | `dc8f363e389259130764219e01a6b42d` |
| `/root/portal/tile_grants.json` | `d7edf850a977c033448d6e14076490b4` | `2eb2f2714091d97ae8f53a80902c913f` |

## What is edited

**Not one existing line.** Two anchors, each matched exactly once:

1. the **Marg Purchases** tile block — the new tile is inserted after it;
2. the group-map row that already carries `Marg Purchases` and `Order Medicines` —
   one name is appended to it.

`tile_grants.json` is a full-file replacement, generated from v16 by appending one
name to `shavez.extra`, bumping the version and adding the ruling to `_note`. The
walk proves nobody else gained or lost a single tile.

## The walk — 23 checks, and what they actually check

The patched file is read back **and compared to the file it was patched from**, tile by
tile, before the service is restarted:

- exactly **one** tile was added (47 → 48), once, no duplicate name;
- it points at `/finance/purchase/page/pay`, is `live`, carries `roles: ["doctor"]`;
- it sits **straight after Marg Purchases** and is in **Money & Accounts**;
- **every other tile is unchanged** — same name, address, roles and order;
- **not one other tile changed section**; the section order is untouched;
- every tile maps to a known section — the rule `portal.py` itself enforces at import,
  so a miss here is a portal that will not start;
- the grants file is valid JSON, is **v17**, grants the tile to **shavez and nobody
  else**, masks it from nobody, names **no tile that does not exist**, and moves
  **nothing else for anybody**.

`TILES` carries real expressions (`bool(...)`, config names), so the walk reads each
value as a literal where it is one and as its own expression where it is not — which is
why the before/after comparison is exact rather than approximate.

Then, after the restart: the service is active, the portal answers, and **the tile's own
address answers** — a 404 there would mean the dial opens nothing, and rolls the install back.

Proven against a fixture root: clean install, **ALREADY INSTALLED** on re-run, and a
deliberately broken grants file (a tile name that does not exist) → 21 ok / 2 failed →
**both files restored byte-identically**, exit 1.

## Install — one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S262_PAY_TILE/install_S262_PAY_TILE.sh
```

## Files

| file | what it is |
|---|---|
| `patch_portal_pay_tile_s262.py` | the two anchored inserts into `portal.py` |
| `tile_grants.json` | v17, the full replacement |
| `walk_s262.py` | the 23 checks, run before the restart |
| `install_S262_PAY_TILE.sh` | pins, backups, patch, walk, restart, roll back |
