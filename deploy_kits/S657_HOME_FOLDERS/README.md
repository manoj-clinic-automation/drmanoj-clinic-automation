# S657_HOME_FOLDERS — the owner's home: folders open in place, the Expiry watch box, his Sanjeevni tiles regrouped · project Sanjeevni · session 353 · 26-Oct-2026

**For the owner, in three lines.** On your PWA home a folder now opens right below itself and shuts again from the same tile or its Close — no new page and no Back. A new box in the top row, **Expiry watch**, shows how many medicines need moving out now (expired, plus what Marg stops selling on the next 1st) and opens the expiry page in one tap; it turns amber when the number is above 0. Your Sanjeevni tiles are two folders — **Sanjeevni Medicos** (your work) and **Sanjeevni staff screens** (what each person sees, each tile naming whose screen it is) — and four old tiles leave your home only. Nobody else's home changes.

## Why
The owner, 26-Oct-2026: *"Only make it more accessible ... right now it is buried down at the bottom of a page"* (05:45); *"Yes"* to the Expiry watch box (05:47); the tile review (05:47) — *"purchase related I see multiple tiles"*; the flow he asked for (05:57) — *"each section on clicking opens a submenu list as a drop down ... the same page expands and back is not required. It expands and collapses"*; the mock-up https://claude.ai/artifact/7YXMpfkuiU4awTHHkNSNfu; *"build"* (06:04 IST). The expiry page itself is not changed (his word, 05:45).

## Files — FROM → TO (every edit anchored; `make_s657.py` rebuilds the TO bytes from the live FROM bytes and stops on any other md5)
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/portal/portal.py` | **the parent** | 844166b1 | 5f4f3738 | 9 counted edits: the strip takes a 4th box (3 again when it hides itself); `.chipbox.due` amber; the S586 sheet styles → the in-place panel (`.gpanel`, dense grid); the Expiry watch box after *Sanjeevni to approve*; a tile may carry `who`; `groups()` draws each folder as a `<button>` with its panel right after it (the sheets loop removed); the accordion script replaces the hash script (one open at a time, Close, Esc, remembered per tab, an old `#g-<group>` link still opens it); the box's number from the count door (a refusal hides the box); `_home_blocks` splits a FOLDED Sanjeevni group into *Sanjeevni Medicos* (approvals first) and *Sanjeevni staff screens*, and his folder's face reads *Approve · purchase orders · pay · stock* |
| `/root/portal/tile_grants.json` | **the parent** | 025f8ab9 | 171f94f8 | v39 → v40: manoj `mask` = Daily Sale, Order Medicines, Marg Purchases, Stock milaan (his home only); manoj `groups` = the mock-up's folder order. Every other login byte-for-byte as v39 |
| `/root/finance/sanjeevni_approvals.py` | Sanjeevni | bf86c8c8 | 26a8dbdb | NEW `GET /finance/sanjeevni/expiry/api/count` (checker only, read only, `no-store`): `{ok, n, expired, stops, stops_on, made, title}` — the same two counts as his Needs-you line (`expiry_watch.needs_you_lines`) |
| `/root/finance/finance_ui/finance_approvals.html` | **the parent's template** (`finance_app.py` not touched) | 885f6f31 | 037af626 | *Other pages*: Order medicines (the old page), the Marg purchases hub, Stock milaan — the pages whose tiles left his home. Daily Sale is not linked: it sends him to his review console, already linked |

Read, not edited: `expiry_watch.py` (`newest`, `now_view`, `ym_add`, `MON`, `needs_you_lines`). No data step. No crontab change. The medical PC and manojz: nothing.

**One change from the mock-up, decided in the build:** *Corrections* sits in his own Sanjeevni folder, not among the staff screens — its bottom half (the ledger check, the owner transfer) is his desk (S223). The staff screens folder holds five: Kal ka hisaab (Darpan), Medical sale check (Bhati), Amir ka kaam (Amir), Aaj ki reports (Shavez · Shivani), Vaapsi Desk (Counter).

## Proven (`walk_s657.py`, on the 26-Oct bundle and the 26-Oct database copy)
26 of 26 green — the owner's home (the four tiles gone, every other tile where it was, the mock-up's folder order, the two Sanjeevni folders); **every other login under every role draws the same folders and tiles in the same order** (15 logins × 3 roles) and the rendered homes of darpan, shavez, amir, bhati, reception and Dr Bhawna hold the same tiles and links; the page (the box beside *Sanjeevni to approve*, every folder a button with its own closed panel, no sheet and no Back, a Close in each panel, the *who* labels, the accordion script); the door (200 for the checker; its number = his Needs-you line's two counts, 5 = *2 expired batches · 3 stop selling on 1-Nov* on the 26-Oct copy; `no-store`; 403 for a refused login; the expiry page itself unchanged; nothing written); the approvals page (the three links and nothing else); v40 and its mask. **Control** (`--old`, the live files as under test): 19 S657 checks red · 0 older red · 7 green. One look at a phone-width render with the Sanjeevni folder open before placing.

## Install (on the server, after the publish; the install window is 08:02–23:49 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s657kit && cp -rp /root/deploy/repo/deploy_kits/S657_HOME_FOLDERS /tmp/s657kit && bash /tmp/s657kit/install_S657_HOME_FOLDERS.sh
```
## Undo (the installer prints it with the exact backup names)
```
for f in portal/portal.py portal/tile_grants.json finance/sanjeevni_approvals.py finance/finance_ui/finance_approvals.html; do b=$(ls /root/$f.bak_S657_* | head -1); \cp -p "$b" /root/$f; done; systemctl restart clinic-finance; systemctl restart clinic-portal
```
