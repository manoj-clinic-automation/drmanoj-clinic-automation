# S210_SWEEP — the daily read-only sweep (S209 stocktake §4B, built)

> *"no point in hunting and chasing them as firefighting any more."* — the owner, 30-Aug.
> This is the standing detector that ruling asked for.

## The three questions it asks, automatically

1. **Does every page's JavaScript parse?** (`node --check` per script block — the F-241
   class: one apostrophe killed the whole console for a day behind four green gates.)
2. **Does every path a page `fetch()`es exist as a route?** (the "could not load" class;
   concatenated URLs like `fetch("/x/"+id)` are matched as prefixes.)
3. **Which API routes does NO page call?** (the F-161/F-245 class — engine wired to
   nothing, twice in one S209 day.)

## Wallpaper-proof by design (the S195 flags-as-info ruling)

Standing facts are not alarms. The first run writes a **baseline** of accepted findings;
every later run reports ONLY what is new. A new orphan route, a new unroutable fetch, a
new syntax error — those alert. The 60-odd legitimate POST tools and cross-box feeds do
not, ever again.

Selftest 6/6 (broken JS caught · missing route caught · orphan caught · used and
parameterised routes not flagged). Proven against the real S210 page+app corpus — where it
immediately caught a REAL fact: `S208_LEDGER3/darpan_app.py` and `S208_CONSOLE/darpan_app.py`
are DIVERGENT copies (CONSOLE is the superset with the cn-approve family). Recorded for the
close; the HANDOVER patch anchors on a block identical in both, so it is safe either way.

## Install — VPS (read-only; no restart; nothing changes on the box)

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_SWEEP/sweep_daily.py /root/finance --baseline /root/deploy/sweep_baseline.txt --write
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_SWEEP/sweep_daily.py /root/finance --baseline /root/deploy/sweep_baseline.txt
```

(line 2 records today's standing facts once; line 3 is the daily check — expect
"SWEEP CLEAN — nothing new since the baseline". Cron it daily whenever you rule; it is
read-only and safe at any hour.)

*S210 · 30-Aug-2026 · built unattended; read-only by construction.*
