#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s661.py -- kit S661_RESTORE_DRILLS (the parent, S357, 26-Oct-2026). The weekly audit's recovery-story asks (run 9, slice 4,
26-Oct: AF-15 the restore drills, AF-32 the two blind legs, AF-33 the petty leg, AF-34 five unbacked files, AF-30 clinic_doctor.py).
Rebuilds the TO bytes of three LIVE files from their live bytes (stops on any other md5); the two new drill scripts ship whole.
  /root/state_backup/code_bundle.py          37a5a132 -> TO   v1.9: four SOURCES entries (never an edit to an old one) -- usr/local/bin clinic-doctor,
                                                                   root/portal/static_inbox *.js, root/assetapp/static *.js; DEPLOY_ALLOW + clinic_doctor.py
  /root/state_backup/clinic_state_backup.py  f315bf43 -> TO   SRC_FILES + the three configs the code bundle's *.conf wall keeps out: the website .htaccess,
                                                                   the followup vhost.conf, the watchdog drop-in (each pinned LIVE; each proven present before placing)
  /root/finance/freshness_legs.json          9df66934 -> TO   + 4 legs (code bundle off-box 26 h; Google Sheets pull 26 h; code bundle restore drill 200 h;
                                                                   state bundle restore drill 200 h); finance restore drill 4400 h -> 200 h (weekly by cron now);
                                                                   petty bill photos off-box: disabled (AF-33: no photo has ever existed; empty by design)
Usage: python make_s661.py <live root, e.g. /root's parent: /> <out dir>   (reads <root>/root/..., writes <out>/root/...)"""
import hashlib, json, os, sys

FROM = {"root/state_backup/code_bundle.py": "37a5a1326a8e90c364e3e50c6083f4f3",
        "root/state_backup/clinic_state_backup.py": "f315bf43b619f97b2537930d245b98a6",
        "root/finance/freshness_legs.json": "9df66934e0df2bf3771ffeb517312674"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s" % (r, h[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:90])
    T[r] = T[r].replace(old, new, 1)


C = "root/state_backup/code_bundle.py"
rep(C, '''    ("root/wa",                      ("*.sh",),                                      False, ("users", "secret", "token")),
]
''', '''    ("root/wa",                      ("*.sh",),                                      False, ("users", "secret", "token")),
    # v1.9 (S661, 26-Oct-2026; the weekly audit's AF-34 and AF-30): files pinned LIVE in the Register that no nightly
    # store carried -- the portal's self-repair wrapper, two vendor JS libraries in sub-folders the non-recursive
    # entries above never reach, and (below, in DEPLOY_ALLOW) clinic_doctor.py itself. New entries, never an edit
    # to an old one (the S273 precedent). The two web-server configs and the watchdog drop-in go to the encrypted
    # state bundle instead: "*.conf" is this file's wall and stays so.
    ("usr/local/bin",                ("clinic-doctor",),                             False, ()),
    ("root/portal/static_inbox",     ("*.js",),                                      False, ("users", "secret")),
    ("root/assetapp/static",         ("*.js",),                                      False, ()),
]
''')
rep(C, '''    "root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine_schema.sql",
)
''', '''    "root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine_schema.sql",
    "root/deploy/clinic_doctor.py",                                    # v1.9 (S661, AF-30): the self-repair doctor itself
)
''')

S = "root/state_backup/clinic_state_backup.py"
rep(S, '''    "/root/att_config.py",
    "/root/wa/wa_inbox/send_log.jsonl",
]
''', '''    "/root/att_config.py",
    "/root/wa/wa_inbox/send_log.jsonl",
    # S661 (AF-34), 26-Oct-2026: three CONFIGS pinned LIVE that no nightly store carried -- the code bundle's "*.conf" wall
    # keeps them out of code_nightly by design, so they travel here, inside the encrypted bundle, as the shape of the machine:
    # the patient-facing website's access rules, the followup site's web-server vhost, the watchdog's doctor-first drop-in.
    # Each is a source like any other here: absent on the box = FATAL 41, so the installer proves all three present first.
    "/home/drmanojagarwal.com/public_html/.htaccess",
    "/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf",
    "/etc/systemd/system/clinic-watchdog.service.d/s578-doctor-first.conf",
]
''')

L = "root/finance/freshness_legs.json"
rep(L, '''   "name": "petty bill photos off-box",
   "group": "Backups",
   "kind": "log_mtime",
   "target": "/root/backups/petty_backup.log",
   "max_age_h": 26,
   "note": "nightly at 02:40 by petty_backup.py (S295)''', '''   "name": "petty bill photos off-box",
   "group": "Backups",
   "kind": "log_mtime",
   "target": "/root/backups/petty_backup.log",
   "max_age_h": 26,
   "disabled": true,
   "note": "RETIRED S661 (26-Oct-2026, the audit's AF-33): the petty book has never held a photo (0 of all entries) and the lane has shipped the empty set since 17-Sep -- empty by design, not dead; the row is parked, not deleted, and comes back the day a photo exists. Was: nightly at 02:40 by petty_backup.py (S295)''')
rep(L, '''   "name": "finance restore drill",
   "group": "Backups",
   "kind": "state_json",
   "target": "/root/finance/finance_restore_verify.state.json",
   "field": "last_verify_iso",
   "max_age_h": 4400,
   "note": "a TWICE-YEARLY drill, not a job — the window is six months on purpose, and this row going stale is a reminder to do the drill, not a fault"
  },
''', '''   "name": "finance restore drill",
   "group": "Backups",
   "kind": "state_json",
   "target": "/root/finance/finance_restore_verify.state.json",
   "field": "last_verify_iso",
   "max_age_h": 200,
   "note": "WEEKLY by cron since S661 (Sunday 02:10): the finance.db Drive copy pulled back, gunzipped, opened, integrity-checked. Was a twice-yearly drill nobody ran (last 07-Sep; the audit's AF-15)"
  },
  {
   "name": "code bundle restore drill",
   "group": "Backups",
   "kind": "state_json",
   "target": "/root/state_backup/verify_restore_code.state.json",
   "field": "last_verify_iso",
   "max_age_h": 200,
   "note": "S661, weekly (Sunday 02:20): the 01:35 code bundle pulled back from Drive, untarred, held to its own MANIFEST and to the live box -- the IN side of the code backup, never exercised before (AF-15)"
  },
  {
   "name": "state bundle restore drill",
   "group": "Backups",
   "kind": "state_json",
   "target": "/root/state_backup/verify_restore_state.state.json",
   "field": "last_verify_iso",
   "max_age_h": 200,
   "note": "S661, weekly (Sunday 02:35): the 01:50 encrypted bundle pulled back from Drive, decrypted with the box's key, untarred, every database integrity-checked, counted against its own inventory -- proves the key and the copy both work (AF-15)"
  },
  {
   "name": "code bundle (off-box)",
   "group": "Backups",
   "kind": "log_mtime",
   "target": "/root/state_backup/code_bundle.log",
   "max_age_h": 26,
   "note": "nightly 01:35 by code_bundle.py (S243): the whole live codebase to Drive. The log is written on every run, so its mtime is the heartbeat. No leg watched it before S661 (AF-18/AF-32)"
  },
  {
   "name": "Google Sheets pull",
   "group": "Backups",
   "kind": "log_mtime",
   "target": "/root/state_backup/sheets_pull.log",
   "max_age_h": 26,
   "note": "nightly 01:45 by sheets_pull.py (S233): the seven irreplaceable Sheets to /root/state_backup/sheets, five minutes before the state bundle takes them. A dead puller shipped stale copies inside a green bundle forever (AF-32)"
  },
''')
json.loads(T[L])
for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print(r, FROM[r][:8], "->", hashlib.md5(t.encode("utf-8")).hexdigest())
