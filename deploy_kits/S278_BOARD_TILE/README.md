# S278_BOARD_TILE — the board gets a place

## What it does

Adds **one tile** to the portal: **System Board**, the first tile in the Clinic
group, so it is the first thing on the page. It opens the Sanjeevni System Board.

Two insertions in `/root/portal/portal.py`, both additive:

- one entry at the head of `TILES`
- one entry in the `_TILE_GROUP` map

Nothing else changes. **No `tile_grants.json` change, no gate change, no database
work, no other file touched.**

## Who sees it

`roles: ["doctor"]` — the owner alone. Staff logins are untouched and never see
it, which is correct: the board is not a page they can open. When the board's
contents move inside the portal as the per-person banner, that is what staff get,
and this tile goes away.

## What it is honest about

The tile is a **link out** of the portal. It opens on claude.ai and needs the
owner to be signed in there in that browser. That is a real limitation and the
reason this is a tile rather than a page: the board lives outside the portal
today. It is the shortest path to "I can reach it whenever I want" without
building the banner first.

## The safety gate

- **Refuses** unless `/root/portal/portal.py` is exactly
  `dc8f363e389259130764219e01a6b42d` — its live pin, confirmed byte for byte
  against the box's own nightly bundle this session. A file that has moved on
  means the kit must be rebuilt, never forced.
- **Refuses** unless each anchor occurs exactly once.
- **Says "already installed"** and changes nothing when run a second time.
- Backs up to `portal.py.bak_S278_dc8f363e` **before** writing.
- **Compiles** the patched file before putting it in place.
- Restarts `clinic-portal`, then checks it is active — and if it is not,
  **restores the backup byte-identically**, restarts again, and says so.

## How it was proven

A live-shape walk against the real `portal.py` taken from the box's own nightly
bundle, not a stand-in:

| walk | result |
|---|---|
| install | `dc8f363e…` → `4974209b…`, compiles, tile renders first |
| run it again | "already installed", nothing changed, exit 0 |
| run against a drifted file | refused by fingerprint, nothing changed |
| restart forced to fail | rolled back to `dc8f363e…` exactly, said so |

## To undo, afterwards

```
\cp /root/portal/portal.py.bak_S278_dc8f363e /root/portal/portal.py && systemctl restart clinic-portal
```
