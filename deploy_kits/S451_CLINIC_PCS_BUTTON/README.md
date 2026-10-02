# S451_CLINIC_PCS_BUTTON — session 290, 02-Oct-2026

The first live use of the Clinic PCs page (S450, D660) found two defects. This kit replaces one file,
`/root/finance/pc_kits.py` (104aca6d → the kit's), and touches nothing else.

## F-684 — the button refused its own owner

`POST /finance/pcs/setup/<pc>` answered **403 with the module's own "Not permitted" page** on the live box, from a
signed-in owner with the page itself open (`GET /finance/pcs` 200, `whoami` = the medical checker). Tried as a `fetch`,
an XHR and a real form submission, for a known and an unknown PC: 403 each time — so the refusal came before the PC was
even looked up. Reading the code, the gate, `require()` and the identity are the same for GET and POST; the one thing
left is S450's check `Origin == https://followup.dr-manoj.in`. The front server is OpenLiteSpeed, which F-68 already
recorded as not handing `Origin` through as the browser sent it. **The value the app received was never seen** — S450
gave no reason and logged nothing — which is itself the second half of the fault. The S450 walk tried "no Origin" and
"another site's Origin", never a real browser behind the real front server.

Now:

* the browser's own word decides — `Sec-Fetch-Site` of `same-origin`, `same-site` or `none` is taken whatever happened
  to `Origin` on the way; anything else is refused;
* a browser that does not send it: refused only when `Origin` names another HOST (not this server's name, not the name
  the request came to, not the loopback); `null` and a missing `Origin` are taken;
* every refusal says why on the page and writes a line to `pc_kit_log.txt` with the `Origin` and `Host` the app saw,
  so the card's own "Last:" line shows it;
* the owner-only rule is unchanged and still comes first.

What a forged press could gain: nothing. The answer is a file the forging page cannot read; the code inside it opens a
kit with no secret in it and can enrol one key, and only from a PC that holds the code.

## F-685 — the setup file did not ask which computer it was on

Run on the wrong PC, `ClinicSetup_Reception.cmd` would have installed the reception agent there and replaced the
reception PC's enrolled key. Now, before it makes a folder or fetches anything:

* it stops on the clinic's other PCs by name (`MEDICAL`, `MANOJZ`);
* it says `This computer is <name>.`; named `RECEPTIONPC` it goes on, any other name it asks Y/N (a reinstalled Windows
  has a new name) and N — or no answer — stops;
* the enrol door refuses a key whose computer names another clinic PC, whatever file sent it.

## Proof

`walk_s451.py` — the real `finance_app.py` over a scratch copy of `finance.db`: 64 checks on the new file, and the box
as it is (S450) reproducing the defect as the negative control. Everything S450 walked is walked again. The `.cmd`
itself is Windows: it is rehearsed on the reception PC after this install.

## Install

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S451_CLINIC_PCS_BUTTON/install_S451_CLINIC_PCS_BUTTON.sh

Seven steps; restarts `clinic-finance` only; red after placing → the S450 file is put back. `DRY=1` places nothing.
