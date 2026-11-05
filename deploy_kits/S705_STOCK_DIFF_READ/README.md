# S705_STOCK_DIFF_READ — READ-ONLY (S386, Sanjeevni, 05-Nov-2026)

The owner's ask (09:41 IST 05-Nov): the stock differences as a proper list — each with why, and the remedy.
The spine holds them in `/root/finance/spine/spine.db`, which is in no nightly bundle; this reader prints them.

- Opens spine.db with `mode=ro`. Writes nothing, restarts nothing, changes no file. Not an installer.
- Prints every OPEN finding at the latest checkable closing: the day it began, Marg and the spine on both sides,
  what moved in the spine in between, and the item at each pending (newer) closing with any later purchase.
- Walk: `python3 -B walk_s705.py <path to spine_build.py>` on a made-up spine — 8 ok, CONTROL red-capable.

The one server line (after the publish):

    cd /root/deploy/repo && git pull --ff-only && /usr/bin/python3 -B /root/deploy/repo/deploy_kits/S705_STOCK_DIFF_READ/s705_stock_diffs.py /root/finance/spine/spine.db
