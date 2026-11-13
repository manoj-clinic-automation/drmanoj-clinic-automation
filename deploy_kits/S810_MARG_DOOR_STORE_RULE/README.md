# S810_MARG_DOOR_STORE_RULE — only a WHOLE STORES stock report is filed (13-Nov-2026, Sanjeevni session 441)

**The gap (plan v4 §4, D913).** Marg prints the store chosen at *Select Store* in the report's title. A closing stock, stock valuation or batch stock of MAIN STORE, DTH, SCRAP STORE — or of several stores without WHOLE — was filed at the door as good. Every reader already picks WHOLE STORES for itself, so nothing was miscounted; but the wrong file was filed and Shavez's tile could not say why in plain words.

**The kit.**
1. `/root/marg_ingest/marg_router.py` (318086e3 → TO): `verify()` refuses such a file with the store named — *"MAIN STORE only -- the WHOLE STORES report is needed"*. A choice that includes WHOLE passes; a title naming no store passes (never seen; never refused on a guess); the expiry report is never judged by store. The same file goes to manojz (`D:\Downloads\margsync\MargPull\marg_router.py`) — placed by Claude after the server install.
2. `/root/finance/reports_tile.py` (4eaeadbd → TO): the staff tile's Hindi line — *"Yeh sirf MAIN STORE ki report hai. Select Store mein WHOLE chuniye, phir dobara nikaaliye."* `clinic-finance` is restarted.
Both are rebuilt on the box from the live bytes by `make_s810.py` (exact anchors) and checked against `TO_PINS.md5`. No copy of a live file travels in the kit. The old single-store files already filed stay as history; nothing is re-filed.

**Proof before it left the bench.**
- *The bench, on the real files* (`03_WORKING_PAPERS\S441\kit810\bench_s810.py`, manojz's MargArchive, the live router against the built one): 121 stock files — 107 whole-shop files judged exactly as before (type, variant, verdict); 14 single-store files (MAIN STORE ×8, DTH, SCRAP STORE, DTH+MAIN ×4) VERIFIED by the live router, REFUSED by the built one with the store named. GREEN.
- `walk_s810.py` 14/14 GREEN on the built files; its control on the live files 8 red.
- The router's own selftest OK with 17 new S810 checks; the tile's selftest 55/55.
- `rehearse_s810.sh` 7/7 on a made-up root: dry · a changed live file stops · install · again · the undo line byte for byte · a red at [4/6] puts both back · another build's lock.

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s810kit && cp -rp /root/deploy/repo/deploy_kits/S810_MARG_DOOR_STORE_RULE /tmp/s810kit && bash /tmp/s810kit/install_S810_MARG_DOOR_STORE_RULE.sh

**Undo:** the installer prints the one line. Off: none needed — the rule only refuses a single store's stock file.
