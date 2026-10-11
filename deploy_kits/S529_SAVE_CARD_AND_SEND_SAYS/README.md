# S529_SAVE_CARD_AND_SEND_SAYS — the save-contact page, and the pack's Send that says "Sent" (F-855)

Kit of session 305 (the parent), 11-Oct-2026. Numbers claimed on the System Board (`_numbers` v358): kit S529, F-855.

**The owner, 11:23 IST:** the save link *"showing multiple prompts and not opening the contacts directly in my fold ... do
whatever is required"*; the accountant pack *"no confirmation message on that page ... check it"*.

**Measured first:** September's pack reached both accountants at **08:52 IST** and again at **11:22 IST** (subject
"- resend"); no bounce. F-855: the Send button answered only with a flash at the top of the page and the *Sent:* line —
out of sight — so it was pressed twice.

## What it does
1. **https://drmanojagarwal.com/save/** (new, on this server) — the clinic's *save contact* page. One tap on **Save to my
   contacts**: on Android the phone's own new-contact form opens, already filled in (name, both numbers); on iPhone the
   contact card itself opens (*Create New Contact*). Call buttons and the card download stay below. The card
   (`clinic.vcf`) is **fetched on the box at install** from the card the clinic's contact page already uses —
   **no number is in this kit or the repository**; the page reads the numbers from the card when it is opened.
   `save.dr-manoj.in` (GoDaddy) is then pointed at this page.
2. **packs.html** — the Send button says *Sending… (up to a minute)*, then **✓ Sent at HH:MM — N mail(s)** or **NOT sent —
   why** right under itself; it cannot be pressed twice while a send is on its way; once a month is sent it reads
   **Send again**, and asks *"This pack was already sent. Send it AGAIN…?"*.
3. **setup_notes.py** — the Websites card names the save page; the "did not open" note is gone.

| file | from | to |
|---|---|---|
| `/root/finance/packs.html` | `633ddba801a80e2aaaf1102d8ef7d1a2` | `d25452a51f2f5fdd5c1e2b39b54bd9ff` |
| `/root/finance/setup_notes.py` | `63477bc0781f6554b57a7868ea6161dc` | `d32423d1472081416b140fc5437523ab` |
| `/home/drmanojagarwal.com/public_html/save/index.php` | new | `f6496578168fc565cfd20e935d9f0510` |
| `/home/drmanojagarwal.com/public_html/save/clinic.vcf` | new | fetched on the box, checked as a vCard with a name and numbers |

Restarts `clinic-finance`. WordPress itself is not touched.

## Proven before the publish
- The save page under PHP with a made-up card: Android gets the new-contact form link (name, both numbers, work type,
  fallback to the card); iPhone gets the card; `?card=1` is `text/vcard`; no card → the contact page.
- The Send button's code run with stand-ins: Sending → Sent at …, NOT sent, and a lost answer — each shown under the
  button; the old page's code fails the same test.
- `walk_s529.py`: both pages render as templates; outside the button the two packs pages are identical; the notes differ
  only on the Websites card; the save page holds no number. Three negative controls red.
- The installer rehearsed on a made-up root with the page served by PHP.

## Install
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S529_SAVE_CARD_AND_SEND_SAYS/install_S529_SAVE_CARD_AND_SEND_SAYS.sh
```
## Undo
```
\cp -p /root/finance/packs.html.bak_S529_633ddba8 /root/finance/packs.html && \cp -p /root/finance/setup_notes.py.bak_S529_63477bc0 /root/finance/setup_notes.py && mv /home/drmanojagarwal.com/public_html/save /home/drmanojagarwal.com/public_html/save.removed_S529 && systemctl restart clinic-finance
```
