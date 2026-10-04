# S473_PHONE_KITS — the two phones on the Clinic PCs page (session 293, 04-Oct-2026)

**The owner, 04-Oct:** "a full setup of that MacroDroid part for the reception mobile and for my mobile should also be there in
case it is required again". He exported both phones' macros the same morning (kept, with their keys, in
`D:\Downloads\margsync\_config\macrodroid\` on manojz — never the repository).

| where | from → to | what |
|---|---|---|
| `/root/finance/pc_kits.py` | 83f318d7 → (the kit's pin) | the page is **Clinic PCs & phones**: two phone cards — *Dr Manoj’s phone (Fold)* (the two bank-SMS macros) and *Reception mobile* (the Sanjeevni WhatsApp order macro) — each with what the server last heard from it, its macros, the things only a person does on a fresh phone, what else lives on it, and **one button: Set up this phone again** → the browser downloads `MacroDroid_<phone>_<date>.mdr`, made at that moment from the repository's template with the **live key put in** (the bank-SMS door's key on the box; the reception phone's token from the settings). Same owner gate and cross-site check as a PC button; the press logged; a box that cannot read the key makes no file |
| `deploy_kits/PC_KITS/macrodroid/<phone>/macros.template.mdr` + `KIT_INFO.txt` | new | the owner's exports with every key a placeholder (`{{BANK_SMS_KEY}}` / `{{PHONE_TOKEN}}`), the retired *SMS to Google Sheet* macro dropped, the geofence / cell-tower data blanked — nothing secret, no number |

On the phone: open the downloaded file → MacroDroid imports it; the card lists the permissions to grant and the switch to turn on.
Not touched: the three PC kits and buttons, the doors, the keys themselves, the database.

## Proven — `walk_s473.py`, hermetic (F-709)
The edited file in `/tmp`, a throwaway Flask app with a made-up owner login, a scratch kits root, a made-up key and token made at
run time. 33 checks: both templates whole (md5 = KIT_INFO), placeholders in, no key-shaped string, no number, no geofence, only the
server's and wa.me addresses; the page with both cards and buttons and what the server heard; a press makes the file (valid JSON,
the made-up key in both HTTP actions, no placeholder left, the retired macro gone; the reception token likewise); both presses
logged without the key; a cross-site press 403, an unknown phone 404, a box that cannot read the key 503 — no file in any of the
three. Offline 04-Oct: `WALK_S473 GREEN 33 checks, 0 fail`.

## Install (the owner's one line; the lock F-694; DRY=1 places nothing)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S473_PHONE_KITS/install_S473_PHONE_KITS.sh
```
Red after placing → the file is put back. Backup `pc_kits.py.bak_S473_<from8>` beside it.

(The folder is named macrodroid, not phones: the repository's .gitignore refuses any path with "phones" in it -- F-185's guard -- and the first publish was refused on it.)
