#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""setup_notes.py -- kit S492_SETUP_NOTES (session 298, 07-Oct-2026). PARENT. S527 (session 305, 11-Oct-2026):
the five set-up cards that were "to be built" -- Hostinger, CyberPanel, the SSH login, the websites, Bitwarden --
are built (CARDS, below the biometric machine), from the server's own files and the records; see CARDS' note.

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
# S527 (the owner, 11-Oct-2026 08:10 IST: "DO NOW") -- the five set-up cards D688 listed as 'to be built'. Every line comes
# from the server's own files (cert_watch.py's site list, att_doctor.py's ports, the crontab, the unit list), the
# records (the Register, the renewals and vendor register of S230/S232, the estate inventory, the GoDaddy mails in the
# clinic account) or a read of the live site; where nothing records a fact, the card says so under 'Not written down
# yet'. NEVER a password, a key, a code -- nor WHERE one lies on a PC: that is a map to the vault (S232). Bitwarden is
# named as the one place logins go.
# Each card: label, chip, what (trusted HTML of this file), blocks [(title, [trusted HTML lines])], steps (numbered,
# optional, (title, [lines])), gaps [plain text].
# ---------------------------------------------------------------------------------------------------------------------
SERVER_IP = "93.127.195.49"
CARDS = [
    {
        "label": "Hostinger — the server",
        "chip": "Renews 10-Jun-2028",
        "what": "One rented server (Hostinger KVM 2) runs every clinic page, the website and every nightly job.",
        "blocks": [
            ("What it is", [
                "<b>Hostinger KVM 2 VPS</b>, rented for two years at a time; the next renewal is <b>10-Jun-2028</b>.",
                "Its name is <span class=nw>srv1746119.hstgr.cloud</span> and its address <span class=nw>" + SERVER_IP + "</span>. "
                "It runs AlmaLinux 9 on a 99 GB disk.",
                "<b>At the renewal:</b> Hostinger offers an add-on called Webuzo. It is not used and must stay switched "
                "off; a reminder for this is set for 10-May-2028.",
            ]),
            ("Where to sign in", [
                "<a href='https://hpanel.hostinger.com' target=_blank rel=noopener>hPanel</a> — Hostinger's own "
                "panel, with your Hostinger account. That login belongs in Bitwarden (the card below).",
                "From hPanel you can see whether the server is running, restart it, open its firewall and its weekly "
                "snapshot, and open a <b>browser terminal</b> that works without the SSH key.",
            ]),
            ("Who may reach it, and on which doors", [
                "Two firewalls stand in front of it: Hostinger's (in hPanel) and the server's own.",
                "The doors the clinic needs: <b>22</b> the SSH login · <b>80</b> and <b>443</b> every web page · "
                "<b>8090</b> CyberPanel · <b>8041</b> the biometric machine's punches (with <b>8042</b> beside it). "
                "Everything else is closed.",
                "The server checks its own firewall for the two attendance doors every day and puts them back if they "
                "have gone.",
            ]),
            ("Its backups", [
                "<b>Every night, to Google Drive:</b> the code (01:35), the finance database (01:40) and the clinic's "
                "encrypted state (01:50). Your PC copies them to the SSD at 03:10.",
                "<b>Every week, at Hostinger:</b> a snapshot of the whole machine. It brings back the whole server as it was "
                "that day — never one file — so it is the last resort, after the nightly copies.",
                "The website has its own weekly backup to Drive (on the Websites card).",
            ]),
            ("If the server is down", [
                "<b>One page not opening</b> is usually that page's program, not the server: the "
                "<a href='/finance/freshness'>freshness page</a> and the daily health mail say which.",
                "<b>Nothing opens at all</b> — not followup, not attendance, not the website: sign in to hPanel and look "
                "at the server's status. If it is stopped, start it; if it hangs, restart it from there. Every clinic "
                "program starts again by itself when the server starts.",
                "Until it is back the paper way stays the fallback: the counter sheet, the register, the slips.",
                "Then tell Claude, so that the cause is found and written down.",
            ]),
        ],
        "gaps": [
            "The exact list of Hostinger's firewall rules as they stand today, and which day of the week the snapshot "
            "runs and how many are kept, are not written down. One look in hPanel settles both.",
        ],
    },
    {
        "label": "CyberPanel",
        "chip": "Notes",
        "what": "The control panel of the web server on that machine (OpenLiteSpeed) — the door every page and the "
                "website pass through, and the place their certificates are renewed.",
        "blocks": [
            ("What it does", [
                "<b>OpenLiteSpeed</b>, managed by CyberPanel, receives every visit on 80 and 443. It serves the website "
                "<span class=nw>drmanojagarwal.com</span> (WordPress) itself, and hands each clinic address — followup, "
                "attendance, assets, fit, health, rx — to its own program on the server.",
                "<b>Certificates</b> (the padlock): free Let's Encrypt ones, renewed by CyberPanel when 15 days or fewer "
                "are left, checked daily.",
                "<b>A watch on what the world sees:</b> every morning at 06:40 the server opens each site as a "
                "patient's phone would and reads its certificate. If one is 10 days from expiry — meaning a renewal is "
                "late — it sends one alert and one mail; on 08-Sep the website served an expired certificate for a day "
                "and that is why this watch exists.",
            ]),
            ("Where to sign in", [
                "<a href='https://" + SERVER_IP + ":8090' target=_blank rel=noopener>CyberPanel</a> — door 8090 of the "
                "server. Its login belongs in Bitwarden.",
                "<b>On 11-Oct this address did not open from outside</b> (read from Claude's browser): the panel answers on "
                "the server itself, and its door may be closed to the open internet. If it does not open for you, "
                "hPanel's page for the server is the way in.",
            ]),
            ("Before changing anything there", [
                "<b>Tell Claude first.</b> A website's settings in CyberPanel are also the clinic pages' settings: "
                "a changed rule can close followup or attendance for everyone.",
                "<b>Never delete</b> anything about certificates, nor the server's certificate folder: renewals stop "
                "silently (D445).",
                "WordPress itself — the website's pages and posts — is changed inside WordPress, not in CyberPanel.",
            ]),
        ],
        "gaps": [
            "Whether door 8090 is meant to be open to the internet or only to you is not written down; one look at "
            "Hostinger's firewall settles it.",
            "CyberPanel's own backup jobs run but produce nothing (S230). They are not relied on: the website and the "
            "clinic data have their own backups.",
        ],
    },
    {
        "label": "SSH login",
        "chip": "Key only",
        "what": "How your PC reaches the server's command line — the window you paste the one-line installs into. "
                "It opens with a key, never with a password.",
        "blocks": [
            ("How it is set up", [
                "The server accepts <b>only a key</b> (type ed25519); logging in with a password is switched off.",
                "On your PC, one word opens it in a terminal:<pre class=cp>ssh vps</pre>",
                "<b>WinSCP</b> opens the server's folders with the same key (WinSCP keeps it in its own format), in "
                "Commander view. A <span class=nw>.py</span> or <span class=nw>.env</span> file is copied across in "
                "<b>Binary</b> mode, never Text (D164).",
                "Every install Claude prepares is one line pasted into this window; it fetches the kit itself.",
            ]),
            ("Where the key belongs", [
                "On your PC, in its own SSH folder, and one copy in <b>Bitwarden</b>. Nowhere else — not in a "
                "chat, a mail, a photo or a document.",
            ]),
        ],
        "steps": ("On a new PC, or if the key is lost", [
            "<b>A new PC:</b> take the key out of Bitwarden into the new PC's SSH folder; Claude writes the one-word "
            "<b>vps</b> shortcut and the WinSCP setting for it. Nothing changes on the server.",
            "<b>The key lost or exposed:</b> sign in to hPanel and open the server's <b>browser terminal</b> — it "
            "needs no key. Claude makes a new key with you and gives the lines that put it on the server and take the "
            "old one off.",
            "<b>Afterwards</b> the new key goes into Bitwarden and the old copy is deleted everywhere.",
        ]),
        "gaps": [
            "A copy of the key is still kept outside Bitwarden on your PC (flagged at S232): it is to go into Bitwarden "
            "and the key is then to be changed. Not recorded as done.",
        ],
    },
    {
        "label": "Websites",
        "chip": "4 names",
        "what": "The public website, the clinic's own pages, the retired name and the lab's site — where each is "
                "registered, where it runs, and when it renews.",
        "blocks": [
            ("drmanojagarwal.com — the public website", [
                "<a href='https://drmanojagarwal.com' target=_blank rel=noopener>drmanojagarwal.com</a> — "
                "<b>WordPress</b> (built with Elementor), on this server, through CyberPanel. The name renews on "
                "<b>10-Jun-2029</b>; its "
                "records point at Hostinger's name servers.",
                "Pages and posts are changed in WordPress itself (its admin page, with its own login — in "
                "Bitwarden).",
                "Backed up weekly to Google Drive by WordPress's own backup plug-in (UpdraftPlus).",
            ]),
            ("dr-manoj.in — the clinic's own pages", [
                "Registered at <b>GoDaddy</b> (with the clinic's Google account), renewed on 15-Aug-2026 for a year, "
                "<b>automatic renewal on</b> — next around Aug-2027.",
                "<b>On this server:</b> "
                "<a href='https://followup.dr-manoj.in/portal' target=_blank rel=noopener>followup</a> (the clinic hub) "
                "· <a href='https://attendance.dr-manoj.in' target=_blank rel=noopener>attendance</a> · "
                "<a href='https://assets.dr-manoj.in' target=_blank rel=noopener>assets</a> · fit · health "
                "· rx.",
                "<b>save</b> opens the clinic's <a href='https://drmanojagarwal.com/save/' target=_blank rel=noopener>save contact</a> "
                "page on this server (S529): one tap opens the phone's own new-contact form, filled in. Its card is "
                "<span class=nw>clinic.vcf</span> beside the page \u2014 change the card there, never the page.",
                "<b>At GoDaddy, as forwarding links</b> (they never touch this server): save (to that page), contact, map, web, ios, "
                "book, app, www.",
                "A new address under dr-manoj.in is a record added at GoDaddy and a site added in CyberPanel — "
                "Claude prepares both.",
            ]),
            ("drmanojagarwal.in — retired", [
                "Registered at Bigrock (bought through Justdial). <b>Retired by you and not renewed on purpose</b> "
                "(D422); until it lapses it forwards to the .com (it still did on 11-Oct).",
            ]),
            ("nkpathology.com — the lab", [
                "<a href='https://nkpathology.com' target=_blank rel=noopener>nkpathology.com</a> runs on <b>another "
                "host</b>, not this server — the only site of yours that does not. It is a hand-built site, not "
                "WordPress.",
            ]),
            ("Certificates and renewals", [
                "Every site on this server has a free certificate renewed by CyberPanel and checked every morning "
                "(the CyberPanel card).",
                "Domain renewals also come to you in the renewals list; dr-manoj.in renews by itself at GoDaddy.",
            ]),
        ],
        "gaps": [
            "Where nkpathology.com is registered and hosted, and when it renews, is not recorded anywhere.",
            "Which company drmanojagarwal.com is registered with is read only from its records (Hostinger's name "
            "servers); the bill would confirm it.",
        ],
    },
    {
        "label": "Bitwarden",
        "chip": "In use",
        "what": "One safe place for every login, so that none lives only in memory, on paper notes or in a photo. "
                "The free account has been in use since September (S230).",
        "blocks": [
            ("What is decided", [
                "Bitwarden replaces Apple Notes for logins (D421).",
                "Its <b>master password</b> and its <b>two-step recovery code</b> are kept on paper only — never "
                "inside Bitwarden, never in a chat.",
                "Claude never sees the vault and never types a password for you.",
            ]),
            ("Already in it", [
                "Folder <b>Clinic — VPS</b>: the key that unlocks the server's nightly encrypted backup.",
                "Folder <b>Clinic — Google</b>: the apps' Google sign-in secret and the MyOperator values.",
                "The personal apps' password.",
            ]),
            ("How to file one login", [
                "One entry per login: its name, the user name, the password, and <b>the website address</b> — so the "
                "browser fills it by itself next time.",
                "Then the old copy — a note, a photo, a file on the PC — is deleted.",
            ]),
        ],
        "steps": ("Bringing the rest in, a stage at a time", [
            "<b>The server:</b> the Hostinger account, CyberPanel, WordPress's admin, and the SSH key (after which a new "
            "key is made — the SSH card).",
            "<b>Names and code:</b> GoDaddy, Bigrock (until it lapses), the lab's website, GitHub and its recovery codes, "
            "the recovery codes of both Google accounts.",
            "<b>The clinic's services:</b> MyOperator's panel, Marg, Docterz, and the statement passwords typed on the "
            "packs page.",
            "<b>Last:</b> the older login files kept on your PC are deleted once each is in Bitwarden.",
        ]),
        "gaps": [
            "The move of the older login files on your PC into Bitwarden (the S232 list) is not recorded as done.",
        ],
    },
]

# the owner's ask of 06-Oct, all five built at S527: nothing is left 'to be built' (the section shows only when this has rows)
TO_BUILD = []

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


def card_html(c):
    """S527: one set-up card. Every string is this file's own trusted text; titles and gaps are escaped."""
    out = ["<div class=pc><div class=row><div class=pcn>%s</div><span class='st info'>%s</span></div><p class=what>%s</p>"
           % (html.escape(c["label"]), html.escape(c["chip"]), c["what"])]
    for title, items in c["blocks"]:
        out.append("<details class=sn><summary>%s</summary><ul>%s</ul></details>"
                   % (html.escape(title), "".join("<li>%s</li>" % i for i in items)))
    if c.get("steps"):
        title, items = c["steps"]
        out.append("<details class=sn><summary>%s</summary><ol>%s</ol></details>"
                   % (html.escape(title), "".join("<li>%s</li>" % i for i in items)))
    if c.get("gaps"):
        out.append("<div class=todo><b>Not written down yet:</b><ul>%s</ul></div>"
                   % "".join("<li>%s</li>" % html.escape(g) for g in c["gaps"]))
    out.append("</div>")
    return "".join(out)


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
    out.extend(card_html(c) for c in CARDS)                       # S527: the five set-up cards
    if TO_BUILD:
      out.append("<div class=pc><div class=pcn>To be built</div><p class=what>Asked for and on the list. Each gets a card "
               "like the one above: notes and links, never a password.</p>%s</div>" % "".join(
                   "<div class=tb><div class=row><div class=pcn>%s</div><span class='st info'>To be built</span></div>"
                   "<p class=what>%s</p></div>" % (html.escape(n), w) for n, w in TO_BUILD))
    return "".join(out)
