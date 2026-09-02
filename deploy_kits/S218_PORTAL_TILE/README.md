# S218_PORTAL_TILE v2 — Vaapsi Desk tile + Daily Sale retarget

v1 503'd the portal: the module asserts at import (portal.py line 383) that
EVERY tile is in _TILE_GROUP; the new tile was not, so gunicorn's worker failed
to boot. compile() cannot catch a runtime assert — the offline rehearsal passed
and the box still fell. v2 makes BOTH required edits together:
1. `Daily Sale` tile url `/finance/entry` (S218-retired) -> `/finance/daily`.
2. NEW `Vaapsi Desk` tile (roles: staff + doctor) AND its `_TILE_GROUP` entry
   ("Money & Accounts", beside Daily Sale/Sanjeevni).

PROVEN this time by IMPORT, not compile: the patched module was imported with
stubbed deps and ran its real grouping assert (line 383) clean through to line
3579 — v1's failure point is passed. Anchors are verbatim from the live bytes
(portal.py md5 24ea2c0b); the patch refuses on any drift, backs up, and
restores itself if compile fails.

Result: the owner sees the 📦 Vaapsi Desk tile; alisha, shivani, darpan, shavez
see it too; their Daily Sale tile lands on the live form. Each installs the PWA
from her own login. Rollback: the printed .bak_S218_tile_* file + restart.
