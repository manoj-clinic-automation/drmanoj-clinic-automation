# S710_VIEWER_FIT — S387 (Sanjeevni), 05-Nov-2026 · D830

**Why:** S708 went live at 20:31 IST. Its live check (the owner's login, Chrome on manojz) found the PC scan viewer showing a PDF bill at
about 40 % with Chrome's thumbnail strip, in a frame 541 px tall: the owner's *"scans that open shd be big enough for proper viewing in pc
screen"* not met. A read-only test of the PDF viewer's address settings on the live origin: `#navpanes=0&view=FitH` shows the bill at the
frame's full width, legible at reading size (with `#view=FitH` alone: 62 %, beside the strip).

| file | from | to | what |
|---|---|---|---|
| `/root/finance/order_track_page.py` | eaa23b1f | TO_PINS | the PDF frame's address `#navpanes=0&view=FitH`; its height `100vh - 230px` — the bill as tall as the screen allows with its buttons still in view (was `- 260px`) |

Phones are unchanged (no PDF frame; the picture and *Open the full scan*).

**Proofs:** walk S710 2 ok (the change, and S708's walk 70 ok on the same code); control on S708's file 1 ok, 1 red. Installer rehearsed on a
made-up server tree (DRY, a forced red at [7/7], the install, ALREADY INSTALLED).

**Install (one server line, after the publish):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s710kit && cp -rp /root/deploy/repo/deploy_kits/S710_VIEWER_FIT /tmp/s710kit && bash /tmp/s710kit/install_S710_VIEWER_FIT.sh
