# S759_SITE_CERT_INSTALL — the website serves the renewed certificate

**Why.** Kit S758 (09-Nov, 08:14 IST) found and mended the cause of the nightly failure — acme.sh wrote its check file into
`/home/drmanojagarwal.com/public_html`, while the website serves `/.well-known/acme-challenge` from `/usr/local/lsws/Example/html` —
and acme.sh then **renewed** drmanojagarwal.com. But the site kept serving the old certificate (ends 08-Dec): the new one sits in
acme.sh's own folder, and the website reads the two files its vhost names (`vhssl keyFile / certFile`).

**What it does.** LOOK: the renewed certificate (days left; it and its key belong together), the vhost's two files, what the site
serves. ACT only when all hold: the two files and acme.sh's conf backed up (`*.bak_S759`); `acme.sh --install-cert` into exactly those
two files with the web server's restart as its reload command — kept in acme.sh's conf, so **every later renewal lands there by
itself**; the certificate the site SERVES read back (> 60 days) and the site answering. Otherwise everything is put back and the web
server restarted once.

**Install** (after the publish):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s759kit && cp -rp /root/deploy/repo/deploy_kits/S759_SITE_CERT_INSTALL /tmp/s759kit && bash /tmp/s759kit/install_S759_SITE_CERT_INSTALL.sh
```
Undo: `bash /tmp/s759kit/install_S759_SITE_CERT_INSTALL.sh --undo`
