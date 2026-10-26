# S663_PORTAL_CONSOLIDATE — the portal's whole read, settled · the parent · session 358 · 26-Oct-2026

**For the owner, in two lines.** Nobody's tiles move. Dr Bhawna's top row sits on one line again (the Expiry watch box now really hides on her screen), two of your folder faces say what is inside them now, and the Call Console's Staff tab stops running eight database queries it never showed.

## Why
`/root/portal/portal.py` had been patched five times since it was last read whole (drift 5, Fault §7.110; START_HERE_SESSION_358 §0 B). S358 read **fe9cc368 whole** — its live bytes rebuilt from the 26-Oct bundle's 844166b1 through `make_s657.py` and `make_s660.py`, the md5 equal to the live pin — and checked every finding against its consumers before it counted.

## File — FROM (S660's TO) → TO
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/portal/portal.py` | **the parent** | fe9cc368 | 1e0c6548 | **E1** CROSSED (S657): `.chipbox[hidden]{display:none}` — the Expiry watch box set `hidden` on a refused login but `.chipbox{display:block}` outranked it; the strip, squeezed to three columns by the same code, wrapped. **E2** CROSSED (S383): `#gReports[hidden]{display:none!important}` on the Clinic Gist page. **E3** two folded faces: Patients *Records · parchi desk · procedures · reports*, System *Board · users · clinic PCs · WhatsApp approvals*. **E4** DEAD: `_query_staff` (eight queries, three of them inside `_agent_names`) and its one call (the Staff tab draws from `_staff_week` since S171; the template never reads `staff` — proven with jinja2's own parser) |

`tile_grants.json` not touched. No data step, no crontab change, `clinic-portal` restarted alone.

**Recorded, not changed:** the code's built-in tile lists (used only if `tile_grants.json` cannot be read) are the pre-S222 lists by design (S222: "behaves EXACTLY as it did before it existed"); they do not carry S586–S660. Display only — every page checks its own permission — and the grants file is in the nightly state bundle. Clinic Gist, Marg Purchases, Order Medicines and Daily Collection are defined but reach no named login (by the grants, his rulings); their pages stay live.

## Proven (S358, in manojz's VM, python3 + flask; on fe9cc368 rebuilt from the 26-Oct bundle)
`walk_s663.py` **11 of 11 green**: 96 homes (15 logins and a made-up one × 3 roles × on/off the clinic PC) draw the same tiles, folders, order, who-labels and doors as before; every home renders; Dr Bhawna's home carries the rule after `.chipbox`'s display; his two faces; the Gist card; the console template never reads `staff`, `_query_staff` gone, the Staff tab still builds its week. **Control** (`--old`): 7 S663 red · 0 older red · 4 green. **In a real browser** (Chromium, every fetch refused as for her login): before — the box shown, the strip on 2 rows at 1366 px; after — the box gone, the strip on 1 row; no sideways scroll at 390 px either way.

## Install (on the server, after the publish; the window is 08:02–23:49 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s663kit && cp -rp /root/deploy/repo/deploy_kits/S663_PORTAL_CONSOLIDATE /tmp/s663kit && bash /tmp/s663kit/install_S663_PORTAL_CONSOLIDATE.sh
```
## Undo (the installer prints it)
```
\cp -p /root/portal/portal.py.bak_S663_fe9cc368 /root/portal/portal.py && systemctl restart clinic-portal
```
