# S447_RATE_GROUPS — session 288 · 02-Oct-2026 · F-681

**The owner, 02-Oct:** *"cast slab is coming at three places"* on the X-rays & procedures tile.

**The fault (read on the live page and in the code).** `/finance/clinic/sheets` built its procedure groups by adjacency, while `services()` hands the rows over sorted by name. So *Cast / slab* broke wherever *Dressing* and the *ILI* lines sort in between: **Cast / slab 11 · Dressing 1 · Cast / slab 2 · Injection (ILI) 5 · Cast / slab 8 · Other 1**. The table itself is clean — 28 procedure lines, no line twice. The parent's own fault, visible since S441 made the groups fold.

**The change.** One anchored edit in `_section_html` of `/root/finance/owner_sheets.py` (`6a04071d` → `8b1aea31fc1d7dd231fbb45f87c2c6d2`): one block per group wherever its rows sort — *Cast / slab*, *Injection (ILI)*, *Dressing*, any other group by name, *Other* last; inside a block a line waiting for his call first, then by name, so each site's cast sits directly above its slab. No row, price, status or route changes; the X-ray section and the staff parchi's list (by id) are untouched.

**Proof.** `walk_s447.py` — 19 checks on the 28 live lines in `services()`'s own order (23 with the real database, read-only); the negative control inside it shows the original page's three blocks, and the installer also refuses if the walk passes the unpatched file.

## Install — one line on the VPS
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S447_RATE_GROUPS/install_S447_RATE_GROUPS.sh
```
Restarts `clinic-finance`. Backup `owner_sheets.py.bak_S447_6a04071d`; anything red after placing restores it.

**Not in this kit:** which cast / slab lines the owner wants removed — that is *Reject* on his own page (no code), on the list as he sees it once it is one block.
