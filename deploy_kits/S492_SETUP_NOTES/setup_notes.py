#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""setup_notes.py -- kit S492_SETUP_NOTES (session 298, 07-Oct-2026). PARENT.

THE OWNER, on his board, 06-Oct-2026: "is the pc and macrodroid setup section in my portal , add biometric machine details
and its setup , all hostinger , cyberpanel ,ssh login etc, websites setup and logins , links to open these from here ,
bitwarden setup for storing logins in a phased easy and comprehensive way". And on 07-Oct: "build biometric and also list
all , the proposed ones in the to be built section there". The same morning he photographed the machine's label and every
settings screen and said: "At reception, connected to clinic wifi. I hold the login, and it's a biometric lock. Vendor bl
computers. What to do a factory reset / replacement - your job." Asked which screens were still missing, he photographed
the menu itself twenty minutes later.

WHAT THIS IS. The notes for the things that are set up once and then forgotten, as DATA, and the HTML that shows them on
the page /finance/pcs (pc_kits.py imports this module under a guard: if it is missing or does not load, that page is
exactly what it was). The owner only, as that page already is. Read-only: no door, no form, no database, nothing written.

THE ONE RULE: NEVER A PASSWORD, PIN, KEY OR TOKEN HERE. This file is in a public repository and on a page. A note says
WHERE a credential is kept, never what it is. (The machine has no PIN: its menu opens with the owner's finger.)

WHERE EVERY LINE COMES FROM.
  * The owner's photographs of 07-Oct-2026, 06:58 IST (kept on manojz in D:\\Downloads\\margsync\\_config\\, never in the
    repository): the label (model, serial number), Device Name, Serial Number, Firmware Version, Software Version, the
    screen 'Server Set' (DNS No, Server IP 093.127.195.049, SerPortNo 8041), the screen 'WIFI' (Link Net WIFI, DHCP Yes,
    IP 192.168.001.005, mask 255.255.255.000, gateway 192.168.001.001, Port No 5005), and the home screen (the Wi-Fi's
    name; its clock right to the minute). The label's network (MAC) address is deliberately NOT here.
  * His second set, 07:20 IST: MENU (1 Register, 2 Set COMM, 3 Set time, 4 Advanced, 5 Set bell, 6 ViewInfo), 'Register'
    (New Reg., Delete, All EnrollData, Upload Reg. Data), 'Comm Set' (U-down, TCP/IP..), 'U-down' (four downloads),
    'General Setting' (its nine lines and values) and 'Advance Setting' (Delete All Rec, All Delete Data, Default Setting,
    Update Firmware) -- photographed only, nothing pressed.
  * His words of the same hour: where it stands, who holds the login, the vendor.
  * This box: /root/attlistener_v2.py (the port, the file, the emergency address), /root/att_doctor.py (the firewall
    ports), the crontab (11:30, 21:00, 14:00), /root/finance/freshness_legs.json (the 74-hour window), portal.py's own
    tiles (the links), the Attendance dossier and the biometric SOP.
  * THE STEPS AFTER A RESET OR A REPLACEMENT are written from those facts and name each screen by the title the machine
    itself shows. TWO ROUTES ARE READ FROM THE LISTS, NOT FROM A PHOTOGRAPH OF THE STEP ITSELF, and the card words them so:
    'WIFI' and 'Server Set' are inside 'TCP/IP..' (Comm Set has only that and U-down), and 'General Setting' and
    'Advance Setting' are inside '4 Advanced' (MENU has no other settings item). WHAT EACH RESET LINE DOES is read from
    its name only -- nothing was pressed -- and the card says 'by its name'. What 'All EnrollData' and 'Upload Reg. Data'
    do is not known and is the one line left under 'Not written down yet'.

TWO LIVE READS, both guarded, both read-only: the modification time of the punch file (when the last punch reached this
box), and the staff master's two columns user_id and name (the codes to enrol with). Nothing else is opened; a file that
cannot be read says so in words. No other column of the staff master is touched.

Stdlib only.
"""
import csv
import datetime as dt
import html
import os
import time

PUNCH_CSV = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
STAFF_MASTER = os.environ.get("ATT_STAFF_MASTER", "/root/staff_master.csv")
PUNCH_STALE_HOURS = 74          # the same window the freshness page gives the punch file (a Sunday plus a holiday)
WIFI = "Airtel_Airtrl_mano_8080"

# ---------------------------------------------------------------------------------------------------------------------
# the biometric attendance machine
# ---------------------------------------------------------------------------------------------------------------------
BIOMETRIC = {
    "label": "Biometric attendance machine",
    "what": "Secureye S-B251CB/WiFi · at reception · on the clinic Wi-Fi · sends each punch to the clinic server by itself",
    "blocks": [
        ("How it is set up", [
            "<b>The machine:</b> Secureye S-B251CB/WiFi, serial number <b>2209031616</b>. It stands at reception. "
            "Software <span class=nw>WS535BW3_BSST_v1.5.43</span>, firmware EASY_A1.",
            "<b>Its menu opens with your finger.</b> You are its administrator; there is no PIN to remember.",
            "<b>Wi-Fi:</b> it is on the clinic Wi-Fi, <span class=nw>" + WIFI + "</span>. On its screen <b>WIFI</b>: Link Net "
            "<b>WIFI</b>, DHCP <b>Yes</b> \u2014 the router gives it its address, so nothing else is typed there. "
            "On 07-Oct-2026 that address was 192.168.1.5. Port No <b>5005</b>.",
            "<b>Where it sends the punches:</b> on its screen <b>Server Set</b>: DNS <b>No</b>, Server IP "
            "<b>093.127.195.049</b>, SerPortNo <b>8041</b>. That is the clinic server and the door it listens on, "
            "instead of the maker's cloud.",
            "On the server a small program (the service <b>attlistener</b>) receives every punch and adds it to one file. "
            "A punch is never changed or deleted, and a punch sent twice is kept once.",
            "Each punch carries the machine's own clock. The server also notes when it received the punch, "
            "so a wrong clock on the machine can be seen. On 07-Oct-2026 the machine's clock was right to the minute.",
            "Running this way, without the maker's cloud, since 28-Jun-2026.",
            "<b>Vendor:</b> BL Computers.",
            "Your photographs of the label and of every settings screen (07-Oct-2026) are on your PC, in "
            "<span class=pth>D:\\Downloads\\margsync\\_config\\biometric_machine_2026-10-07\\</span>",
        ]),
        ("The machine's menu, and where each thing is", [
            "<b>MENU</b> opens with your finger and shows six items: 1 Register \u00b7 2 Set COMM \u00b7 3 Set time \u00b7 "
            "4 Advanced \u00b7 5 Set bell \u00b7 6 ViewInfo.",
            "<b>Wi-Fi and the server:</b> MENU \u2192 2 Set COMM \u2192 2 TCP/IP.. \u2014 the screens <b>WIFI</b> and "
            "<b>Server Set</b> are in there.",
            "<b>The clock:</b> MENU \u2192 3 Set time.",
            "<b>Enrolling or removing a finger:</b> MENU \u2192 1 Register \u2192 1 New Reg., or 2 Delete.",
            "<b>Model, serial number and versions:</b> MENU \u2192 6 ViewInfo.",
            "<b>General Setting</b> (inside 4 Advanced), as it stands: Machine ID 1 \u00b7 Language English \u00b7 DateFormat YMD "
            "\u00b7 VoiceOut Yes \u00b7 Volume 8 \u00b7 Auto Off No \u00b7 Screen Saver 10 \u00b7 Verify F/P/C \u00b7 Card Format 8D N.",
            "<b>Advance Setting</b> (inside 4 Advanced) has four lines: 1 Delete All Rec \u00b7 2 All Delete Data \u00b7 "
            "3 Default Setting \u00b7 4 Update Firmware. <b>The first two delete, and nothing in daily running needs any of "
            "the four.</b> What each does is under the reset steps below.",
            "<b>Punches onto a USB stick:</b> MENU \u2192 2 Set COMM \u2192 1 U-down (Download GLog and three more). "
            "Not needed while the Wi-Fi works.",
        ]),
        ("What uses the punches", [
            "<a href='https://attendance.dr-manoj.in'>Attendance</a> \u2014 the day's board.",
            "<a href='/register/review'>Staff Register</a> \u2014 the daily register, read from the punches.",
            "<a href='/register/salary'>Salary</a> \u2014 the month's sheets.",
            "<i>Meri attendance</i> \u2014 each staff member's own page in the Clinic app.",
            "Two mails a day from the server, at 11:30 and at 21:00 (the day summary), and a self-check at 14:00.",
        ]),
        ("If something goes wrong", [
            "<b>No punches are showing.</b> Look at the Attendance group on the "
            "<a href='/finance/freshness'>freshness page</a>: it says when the last punch came in.",
            "<b>The machine has lost its network.</b> It keeps the punches inside itself and sends them when the network is "
            "back. Until then the paper register is the fallback. The Wi-Fi's name shows at the top of its home screen "
            "when it is connected.",
            "<b>The machine is on the network and still nothing arrives.</b> First read its screen <b>Server Set</b> "
            "against the three values above. If they are right, one line on the server restarts the program "
            "that receives the punches:<pre class=cp>systemctl restart attlistener</pre>",
            "<b>A finger is not reading.</b> Clean the sensor; if it still fails, enrol that finger again "
            "(MENU \u2192 1 Register).",
            "<b>Your own finger is not read at the menu.</b> Nobody else can open the menu. If only one of your fingers is "
            "enrolled as administrator, enrol a second one, so that a cut or a bandage does not lock it.",
            "<b>Last resort.</b> On the screen Server Set (MENU \u2192 2 Set COMM \u2192 2 TCP/IP..), put Server IP back to <b>054.186.015.016</b> (typed with its zeros, "
            "as the machine shows it). The machine then talks to the maker's cloud as it did before June, and the clinic's "
            "pages stop receiving punches until it is set back.",
        ]),
        ("Adding or removing a person", [
            "<b>A new person:</b> their row on the staff roster comes first. Then the finger is enrolled on the machine, and "
            "their code on the machine (the Emp Code) is entered in that same row \u2014 never a second row.",
            "<b>A person who leaves:</b> their code is retired. A code is never given to a second person.",
        ]),
    ],
    # after a factory reset, or with a replacement machine -- numbered, in this order
    "reset": [
        "<b>What a reset is on this machine.</b> Advance Setting has three different lines, and by their names: "
        "<b>3 Default Setting</b> puts the settings back to the factory's and leaves the fingers \u00b7 "
        "<b>1 Delete All Rec</b> removes the punches still inside the machine \u00b7 "
        "<b>2 All Delete Data</b> removes the fingers and the punches. Nothing was pressed to test this.",
        "<b>Before any of them, if the machine still works:</b> look at the top of this card. Punches that have not reached "
        "the server yet are still inside the machine.",
        "<b>Wi-Fi.</b> MENU \u2192 2 Set COMM \u2192 2 TCP/IP.. \u2192 <b>WIFI</b>: Link Net <b>WIFI</b> \u00b7 Search Ap, choose "
        "<span class=nw>" + WIFI + "</span> and type the Wi-Fi password \u00b7 DHCP <b>Yes</b>. Nothing else on that screen is "
        "typed. The Wi-Fi's name then shows at the top of the home screen.",
        "<b>The server.</b> In the same place, <b>Server Set</b>: DNS <b>No</b> \u00b7 Server IP <b>093.127.195.049</b> \u00b7 "
        "SerPortNo <b>8041</b>.",
        "<b>The clock.</b> MENU \u2192 3 Set time: the date and the time, to the minute. Every punch carries that clock.",
        "<b>General Setting.</b> Put back what is listed in the menu block above; Machine ID <b>1</b> and DateFormat "
        "<b>YMD</b> first.",
        "<b>Your finger first.</b> MENU \u2192 1 Register \u2192 1 New Reg.: enrol your own finger as the administrator before "
        "anyone else's, so that the menu is locked to you again. Enrol a second finger of yours as well.",
        "<b>The staff, with the same codes.</b> If the fingers are gone \u2014 on a replacement machine, or after All Delete "
        "Data \u2014 enrol each person again <b>with the code they had</b>. The server knows a person only by that code; with a "
        "new code their punches belong to nobody. The codes are in the next block.",
        "<b>One test punch.</b> Within a minute the top of this card should say that the last punch reached the server at "
        "that time. If it does not, go to \u201cIf something goes wrong\u201d.",
        "<b>A replacement machine</b> must be this model, Secureye S-B251CB/WiFi, or one that BL Computers confirms sends its "
        "punches to a Server IP in the same way. The server understands this machine's language only \u2014 tell Claude before "
        "buying anything else.",
        "<b>Tell Claude</b> afterwards, so that this card carries the new serial number.",
    ],
    "gaps": [
        "The Register screen has two more lines, All EnrollData and Upload Reg. Data. By their names they may copy the "
        "enrolled fingers to a USB stick and back, which would spare everyone a second enrolment on a replacement "
        "machine. Not tried; BL Computers can say.",
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
# asked for by the owner, not built yet -- one line each on what the card will hold (each line is trusted HTML of this file)
# ---------------------------------------------------------------------------------------------------------------------
TO_BUILD = [
    ("Hostinger \u2014 the server", "The plan and its renewal date, where to sign in, and what to do if the server is down."),
    ("CyberPanel", "The websites' control panel on the server: its link and what it is used for."),
    ("SSH login", "How your PC reaches the server, where its key is kept, and what to do on a new PC."),
    ("Websites", "<span class=nw>drmanojagarwal.com</span>, the clinic's internal pages on <span class=nw>dr-manoj.in</span> and "
                 "<span class=nw>nkpathology.com</span>: where each is hosted, how each is changed, and the domain renewals."),
    ("Bitwarden", "Every login kept in one place, brought in by stages, so that nothing lives only in memory."),
]

CSS = (".sn{margin:10px 0 0;border-top:1px solid var(--line);padding-top:8px}"
       ".sn summary{cursor:pointer;font-size:14px;font-weight:650;color:#fff;padding:4px 0}"
       ".sn ul,.sn ol{margin:6px 0 4px;padding-left:20px;font-size:13px;color:#d5e2ee}.sn li{margin:7px 0}"
       ".sn b{color:#fff}"
       ".cp{margin:8px 0 2px;padding:9px 11px;border-radius:8px;background:#0b1b29;border:1px solid var(--line);color:#eaf2fa;"
       "font:13px/1.4 ui-monospace,Consolas,monospace;white-space:pre-wrap;word-break:break-all;user-select:all;-webkit-user-select:all}"
       ".codes{margin:8px 0 2px;display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:4px 14px;font-size:13px;color:#d5e2ee}"
       ".codes b{display:inline-block;min-width:34px;color:#fff;font-variant-numeric:tabular-nums}"
       ".tb{margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}.tb .pcn{font-size:15px}.tb .what{margin:4px 0 0}"
       ".nw{white-space:nowrap}.pth{word-break:break-all}.sn li{overflow-wrap:anywhere}")


def _ist(ts):
    return dt.datetime.utcfromtimestamp(ts) + dt.timedelta(hours=5, minutes=30)


def last_punch(now_ts=None):
    """(state, chip, words) from the punch file's own modification time. Never raises."""
    try:
        ts = os.path.getmtime(PUNCH_CSV)
    except OSError:
        return "info", "No record", "This box could not read its punch file, so it cannot say when the last punch came."
    # time.time(), NOT datetime.utcnow().timestamp(): the second reads the naive UTC clock as LOCAL time, so on this box
    # (India time) it was five and a half hours short -- the kit's own walk caught it at the first install, 07-Oct-2026.
    now_ts = time.time() if now_ts is None else now_ts
    hours = max(0.0, (now_ts - ts) / 3600.0)
    when = _ist(ts).strftime("%d-%b %H:%M")
    if hours <= PUNCH_STALE_HOURS:
        return "ok", "Punches arriving", "The last punch reached the server on %s." % when
    return "warn", "Needs a look", ("No punch has reached the server since %s (%d days). "
                                    "See \u201cIf something goes wrong\u201d below." % (when, int(hours // 24)))


def staff_codes():
    """[(code, name)] from the staff master's two columns, in code order; None when the file cannot be read. Never raises.
    Only user_id and name are read -- the file's other columns are not touched."""
    try:
        out = []
        with open(STAFF_MASTER, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    code = int(str(row.get("user_id", "")).strip())
                except ValueError:
                    continue
                out.append((code, str(row.get("name") or "").strip()[:60] or "(no name)"))
        return sorted(out)
    except Exception:                                          # noqa: BLE001 -- a note never breaks the page
        return None


def _codes_html():
    rows = staff_codes()
    if rows is None:
        return ("<p class=what>This box could not read its staff list just now. The codes are also on the "
                "<a href='/register/review'>Staff Register</a>.</p>")
    if not rows:
        return "<p class=what>The server's staff list is empty.</p>"
    return ("<p class=what>These are the codes the server knows, read now from its staff list. Enrol each person with their "
            "own code. A code on this list is never given to a new person, even after its owner has left.</p>"
            "<div class=codes>%s</div>" % "".join("<div><b>%d</b> %s</div>" % (c, html.escape(n)) for c, n in rows))


def section(now_ts=None):
    """The HTML of the 'Other set-ups' part of the page /finance/pcs. Trusted text only: every string is this file's own,
    except the staff names, which are escaped."""
    state, chip, words = last_punch(now_ts)
    b = BIOMETRIC
    out = ["<style>%s</style>" % CSS,
           "<h1 style='margin-top:18px'>Other set-ups</h1><p class=sub>Notes and links for the things that are set up once and "
           "then forgotten. No password, PIN or key is ever written on this page.</p>",
           "<div class=pc><div class=row><div class=pcn>%s</div><span class='st %s'>%s</span></div>"
           "<p class=what>%s</p><p class=said>%s</p>"
           % (html.escape(b["label"]), state, html.escape(chip), html.escape(b["what"]), html.escape(words))]
    for title, items in b["blocks"]:
        out.append("<details class=sn><summary>%s</summary><ul>%s</ul></details>"
                   % (html.escape(title), "".join("<li>%s</li>" % i for i in items)))
    out.append("<details class=sn><summary>After a factory reset, or with a replacement machine</summary><ol>%s</ol></details>"
               % "".join("<li>%s</li>" % i for i in b["reset"]))
    out.append("<details class=sn><summary>The codes to enrol with</summary>%s</details>" % _codes_html())
    if b["gaps"]:
        out.append("<div class=todo><b>Not written down yet:</b><ul>%s</ul></div>"
                   % "".join("<li>%s</li>" % html.escape(g) for g in b["gaps"]))
    out.append("</div>")
    out.append("<div class=pc><div class=pcn>To be built</div><p class=what>Asked for and on the list. Each gets a card "
               "like the one above: notes and links, never a password.</p>%s</div>" % "".join(
                   "<div class=tb><div class=row><div class=pcn>%s</div><span class='st info'>To be built</span></div>"
                   "<p class=what>%s</p></div>" % (html.escape(n), w) for n, w in TO_BUILD))
    return "".join(out)
