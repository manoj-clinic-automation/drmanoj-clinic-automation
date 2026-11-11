# S789_LAB_TILE_COUNT — the lab tile counts only what needs an answer

**The owner, 11-Nov-2026 09:29 IST:** *"And for the lab reports, it is still showing the same number 42."* — after S788 those 42 reports
were off Shavez's work list but his own tile still counted them, so they read as pending.

`/root/finance/check_screens.py` e86f16e1 (S788) → TO: his X-ray page's lab tile is now **"Lab report — wrong ID?"** and its number is
only the reports that need an answer (the lab's name is another visitor's of that week; 1 on the 11-Nov copy); under it: *"41 more filed
with no blood slip, for information only"*. The list shows the asking one first, then the filed ones (report inline, no buttons). His
console's X-ray & lab line counts the same way. Nothing is filed or moved by this kit.

**Walk** 3/3 (+ S788's 9/9 and S787's 22/22 on the new file); the CONTROL red on the live file; both pages' scripts pass `node --check`.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s789kit && cp -rp /root/deploy/repo/deploy_kits/S789_LAB_TILE_COUNT /tmp/s789kit && bash /tmp/s789kit/install_S789_LAB_TILE_COUNT.sh
```
Undo: `bash /tmp/s789kit/install_S789_LAB_TILE_COUNT.sh --undo`.
