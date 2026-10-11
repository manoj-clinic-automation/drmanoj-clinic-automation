# S534_OLD_CARD_TO_SAVE_PAGE — phones that remember the old link land on the new save page

Kit of session 305 (the parent), 12-Oct-2026. Number claimed on the System Board (`_numbers` v371).

The owner's Fold (04:53 IST 12-Oct) still downloaded `DrManojAgarwalClinic.vcf` — "File can't be downloaded securely".
Chrome had remembered the old **permanent** forward of save.dr-manoj.in to `http://drmanojagarwal.com/DrManojAgarwalClinic.vcf`
and does not ask GoDaddy again, though GoDaddy now forwards to the new page (S529). Every phone that opened the link before
is in the same place.

**The change:** one marked block at the top of the website's `.htaccess` sends that old card address (http or https) to
`https://drmanojagarwal.com/save/` with a **temporary** (302) redirect, so nothing is remembered again. WordPress's own
blocks are untouched; the old file stays on disk. The installer proves the rest of the file is the old file byte for byte,
reads the old address back (302 to the page), follows it over http to the page, and checks the home page, the save page
and its card still answer; a graceful web-server reload only if the rule is not read at once. Red → the old file back.

## Install
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S534_OLD_CARD_TO_SAVE_PAGE/install_S534_OLD_CARD_TO_SAVE_PAGE.sh
```
## Undo
The installer prints it: copy `.htaccess.bak_S534_<first 8 of the old md5>` back over `.htaccess`.
