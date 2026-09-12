# S242_DOCTERZ_COLLECTION_TILE

**What changes:** `/root/portal/tile_grants.json` only. v10 `812cbbc6dbab6598bb861124129b0493`
-> v11 `710f13bd14ebfdf8108372c81414db1e`.

**Who gains the tile:** `shavez`, `shivani`, `alisha` -- appended to each one's `extra` list.
`manoj` and `bhawna` already held it; `darpan`, `amir` and the rest are untouched.

**The tile:** name `Docterz daily collection`, icon 📒, section *Money & Accounts*,
url `/finance/clinic/register` -- reception's own day totals, nine boxes, cash / UPI / card,
plus the end-of-day note count and the three-records comparison.

**Why it is safe:**

- `tile_grants.json` decides what a person is SHOWN. It grants no access.
- The page's own gate is unchanged: `_require("maker", "checker", unit="clinic")` in
  `clinic_register.py`. Shavez, Shivani and Alisha are clinic maker/checker by construction --
  the same gate already lets them open `Docterz Revenue` (`/finance/clinic/day`), which they
  have held since S239 v9.
- No code file is edited. No service restart.

**History:** the tile was withdrawn from staff at **S239 v9** because `finance.db` held zero
register entries to 07-Sep. That was a reading of usage, not of fit: reception is who fills this
screen, so an empty page is the argument for granting it, not against. The owner's ask reverses
that one line of S239 v9 and nothing else.

**Install:** one line, `INSTALL_ONE_LINE.txt`, run on the VPS. It refuses unless the live file is
still v10, takes a timestamped-named backup, and prints the new md5 -- which must read
`710f13bd14ebfdf8108372c81414db1e`.

**Verify after:** open the portal as any of the three; the tile appears under *Money & Accounts*
between `Docterz Revenue` and the rest. Or on the box:
`/root/wa/venv/bin/python3 -c "import json;print(json.load(open('/root/portal/tile_grants.json'))['version'])"`
