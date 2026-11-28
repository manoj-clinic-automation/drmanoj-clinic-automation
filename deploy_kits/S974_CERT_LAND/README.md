# S974_CERT_LAND — a renewed certificate lands where the site reads it (F-1731)

**Why.** 28-Nov-2026: followup.dr-manoj.in served the 08-Dec certificate while CyberPanel's nightly renewal logged success
every night from 23-Nov — the renewal sat in acme.sh's own folder and was never copied into the two files the site's vhost
names. Copied in by hand 07:58 28-Nov. S759 had mended the same for drmanojagarwal.com alone.

**What it places.** NEW `/root/wa/cert_land.py`, nightly 00:25 UTC = 05:55 IST (`# S974_CERT_LAND`): for every site
`cert_watch.py` watches, when acme.sh's pair is newer than what the site's files hold, has more than 30 days, its key and
certificate belong together, it names the site, it is not Let's Encrypt STAGING, and the site's own two files are a matching
pair (the fallback) — the two files are backed up beside (`.bak_S974_<date>`), the new pair written into them, the web server
restarted ONCE, and what each site SERVES read back; a site that does not serve its new certificate is put back. Silent
otherwise. One health leg, "certificate lands" (Watchdog), in `/root/finance/freshness_legs.json` (46 → 47).

**Install** (after the publish):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s974kit && \cp -rp /root/deploy/repo/deploy_kits/S974_CERT_LAND /tmp/s974kit && bash /tmp/s974kit/install_S974_CERT_LAND.sh
```
Undo: `bash /tmp/s974kit/install_S974_CERT_LAND.sh --undo`
