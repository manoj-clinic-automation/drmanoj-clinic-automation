# S492_SETUP_NOTES — "Other set-ups" on the Clinic PCs & phones page (session 298, 07-Oct-2026)

**The owner, on his board, 06-Oct:** "is the pc and macrodroid setup section in my portal , add biometric machine details and its
setup , all hostinger , cyberpanel ,ssh login etc, websites setup and logins , links to open these from here , bitwarden setup for
storing logins in a phased easy and comprehensive way". **07-Oct:** "build biometric and also list all , the proposed ones in the
to be built section there".

| where | from → to | what |
|---|---|---|
| `/root/finance/setup_notes.py` | new | the notes as data and their HTML: the biometric machine's card (seven folded blocks — set-up, **the machine's menu and where each thing is**, what uses the punches, what to do when something goes wrong, adding or removing a person, **the eleven steps after a factory reset or with a replacement machine**, the codes to enrol with) and the five *To be built* lines. Two guarded live reads: the punch file's modification time, and the staff master's `user_id` and `name` (no other column). |
| `/root/finance/pc_kits.py` | 708fd203 → 9c2b3615 | three anchored edits by `apply_s492.py`: the module note, a guarded import, one guarded place on `/finance/pcs` after the phones. |

**The one rule:** never a password, PIN, key or token on the page or in this folder. A note says where a credential is kept.

**Every line on the card is a recorded fact** — the owner's photographs of 07-Oct-2026 06:58 IST (the label, Device Name, Serial
Number, Firmware and Software Version, the screens *Server Set* and *WIFI*, the home screen; kept on manojz in
`D:\Downloads\margsync\_config\biometric_machine_2026-10-07\`, never here) and his words of that hour ("At reception, connected to
clinic wifi. I hold the login, and it's a biometric lock. Vendor bl computers. What to do a factory reset / replacement - your job");
the listener's own header (port 8041, the punch file, the emergency address), the attendance doctor (the firewall ports), the
crontab (11:30, 21:00, 14:00), the freshness page's 74-hour window, the portal's own tiles (the links), the Attendance dossier and
the biometric SOP. A second set of photographs at 07:20 IST gave the menu itself (MENU's six items, *Register*, *Comm Set*, *U-down*,
*General Setting*, *Advance Setting*). **The reset steps** name each screen by the title the machine shows. Two routes are read
from the lists rather than from a photograph of the step (*WIFI* and *Server Set* inside *TCP/IP..*; *General Setting* and
*Advance Setting* inside *4 Advanced*), and what each of the three reset lines does is read from its name — nothing was pressed —
and the card says so. One thing is on the card as *Not written down yet*: what *All EnrollData* and *Upload Reg. Data* do. The label's network (MAC) address is deliberately in neither file.

**Guards.** Without `setup_notes.py`, or if a note raises, the page is byte for byte the page of today (walked). No new door, no
form, nothing written, the same owner-only gate.

**Walk** (`walk_s492.py`, hermetic, 80 checks): the edits give the predicted bytes; the old page whole and in order; the section's
words; the punch file fresh / five days old / unreadable; the codes from a made-up staff list (code and name only, escaped, no other
column) and from an unreadable one; 403 and no notes for anyone but the owner; nothing secret-shaped; known
links only; the HTML closes; both guards.

**To add the next set-up** (Hostinger first): its facts go into `setup_notes.py` as a second card and its line leaves `TO_BUILD`.
`pc_kits.py` is not touched again.

One line on the server, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S492_SETUP_NOTES/install_S492_SETUP_NOTES.sh
```
