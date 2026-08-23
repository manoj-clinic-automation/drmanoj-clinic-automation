# S196_HLT2 — the health headline reaches the portal tile

The last inch of the Sanjeevni-crisis lesson: S195 built the health page AND
`_health_headline()` "for the portal tile" — nothing consumed it. Now
`tile-summary` carries `health_line` (None when all is well) and the
Sanjeevni tile shows it FIRST, fail-soft as ever. All clear = tile unchanged.

Pins: finance_app.py `cfacce27…` → `6fc3becc92c2f28f9f5533611e5c1af7` (smoke 665 → 667) ·
portal.py `ff089807…` → `ee749cd9f3ac1294aab0d13ce069efc1` (live bytes recovered by hash from
S195_CLUB2.tar.gz; three JS lines added, nothing else touched).
Differential offline: 658 → 660, +2 exact, fail-set identical.

Install: publish, then
`cd /root/deploy/repo && git pull && bash deploy_kits/S196_HLT2/INSTALL_S196_HLT2.sh`
