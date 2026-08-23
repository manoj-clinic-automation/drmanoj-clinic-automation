# S198_P4 — the portal as a phone app (A4)

One file: portal.py 40b10a8b7993176cb0469537060e7a43 -> e2484429cfb0217cb6b8d6f3a44ce5c8.
The S196_ATT2 pattern on the portal: manifest (name, start /portal, scope /, standalone,
dark theme) + the two clinic-logo icons byte-identical to ATT2's; head links on every
portal page incl. login; NO service worker (ATT2 ruling); the three PWA routes public on
purpose (name + picture only). Gate 10/10: manifest fields, byte-exact icons, login/home
carry the links, auth unchanged, ZERO tile changes vs baseline.

Install:

    cd /root/deploy/repo && git pull
    bash deploy_kits/S198_P4/INSTALL_S198_P4.sh

Then the staff-phone installs (the standing ⭐0 item): open followup.dr-manoj.in/portal
in Chrome, sign in, menu -> Add to Home screen.
