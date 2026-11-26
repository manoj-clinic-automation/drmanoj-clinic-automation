#!/usr/bin/env python3
"""make_s957.py -- kit S957_PUNCH_DOOR (the parent, S523, 26-Nov-2026). Remakes the four TO files from the FROM bytes, by exact
anchors each found exactly once (F-472: never an inferred anchor). The installer runs it on the box against the LIVE files and
installs only when every remade file equals the kit's TO.
    python3 make_s957.py <attlistener_v2.py> <att_source_summary.py> <callback_clock.py> <freshness_legs.json> <out dir>
"""
import hashlib
import os
import sys

FROM = {"attlistener_v2.py": "588ea08e744d11fc9fbbee7e41d7515c",
        "att_source_summary.py": "2aa34b8862c178c236bc38b3dba73847",
        "callback_clock.py": "5fbcd29cb50a97ce46854d97addba9cd",
        "freshness_legs.json": "f5c68b240f179a8aaee7d6e730dfcd07"}


def once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise SystemExit("REFUSED %s: anchor found %d times" % (what, n))
    return text.replace(old, new)


# ------------------------------------------------------------------------------------------------ attlistener_v2.py
L_DOC_OLD = '''The owner, 12:10 IST 11-Nov: "Ok and correct today's punches also" (his word waives the attendance freeze D247 for this).
'''
L_DOC_NEW = L_DOC_OLD + '''S957 (26-Nov-2026, session S523; F-773, roadmap E0): + THE DOOR -- step 2 of the S535 source watch. Every punch the machine has
sent since 12-Oct carried the machine's own mark in one header, one value throughout (686 punches over 45 days; its internet address
changed 13 times, so the address is NOT the lock). A punch is now admitted only when it carries that mark. The header's name and its
value are NOT in this file: they are read from DOOR_CONF (/root/punch_door.json, 0600, written by the S957 installer from the
watch's own evidence). A punch without the mark is KEPT ASIDE in REFUSED_CSV -- never in punches.csv, never lost -- acknowledged
'OK' as before, counted in DOOR_STATE, and the console's health leg "punch door" turns red for a day. DOOR_CONF missing or
incomplete = the door open (as before S957); mode "watch" = every punch stored and the ones without the mark only counted.
'''

L_HANDLER_OLD = '''class Handler(BaseHTTPRequestHandler):
'''
L_HANDLER_NEW = '''# --- S957 (session S523, 26-Nov-2026; F-773, roadmap E0): THE DOOR -- step 2 of the S535 source watch --------------------------
# The owner, 07-Oct (F-773): "the listener admits only the machine it knows, checked on every punch, and counts what it refuses
# where the health page can see it". The mark (a header name and its one value) is in DOOR_CONF, never in this file.
# Every failure here leaves the door as it was configured: a fault reading the state never stops a punch.
DOOR_CONF = os.environ.get("ATT_DOOR_CONF", "/root/punch_door.json")
DOOR_STATE = os.environ.get("ATT_DOOR_STATE", "/root/punch_door.state.json")
REFUSED_CSV = os.environ.get("ATT_REFUSED_CSV", "/root/punches_refused.csv")
DOOR_RED_H = float(os.environ.get("ATT_DOOR_RED_H", "24"))   # a refusal keeps the health leg red this long
REFUSED_HEADER = "user_id,datetime,io_mode,verify_mode,received_at,ip,reason\\n"
_door_lock = threading.Lock()
_door_cache = {"mtime": None, "conf": None}


def door_conf():
    """{'mode': 'enforce' | 'watch' | 'open', 'header': ..., 'value': ...}; re-read when the file changes."""
    try:
        mt = os.stat(DOOR_CONF).st_mtime
    except OSError:
        return {"mode": "open", "header": "", "value": ""}
    if _door_cache["mtime"] == mt and _door_cache["conf"] is not None:
        return _door_cache["conf"]
    c = {"mode": "open", "header": "", "value": ""}
    try:
        with open(DOOR_CONF, encoding="utf-8") as f:
            d = json.load(f)
        h, v, m = str(d.get("header") or "").strip(), str(d.get("value") or "").strip(), str(d.get("mode") or "").strip()
        if h and v and m in ("enforce", "watch"):
            c = {"mode": m, "header": h, "value": v}
    except Exception:
        pass
    _door_cache.update(mtime=mt, conf=c)
    return c


def door_judge(handler):
    """(admit, flagged, why) for one punch-shaped request."""
    c = door_conf()
    if c["mode"] == "open":
        return True, False, "open"
    got = handler.headers.get(c["header"])
    if got is not None and str(got).strip() == c["value"]:
        return True, False, "mark"
    why = "no mark" if got is None else "wrong mark"
    return (c["mode"] == "watch"), True, why


def door_note(admitted, flagged, refused=False):
    """Update DOOR_STATE (atomic): counts, the newest refusal (last_failure_iso) and the newest admitted punch; last_ok_iso
    moves only when no refusal is younger than DOOR_RED_H -- the health leg stays red that long. admitted None = start-up."""
    try:
        with _door_lock:
            try:
                with open(DOOR_STATE, encoding="utf-8") as f:
                    st = json.load(f)
            except Exception:
                st = {}
            t = datetime.now()
            iso = t.strftime("%Y-%m-%dT%H:%M:%S")
            day = iso[:10]
            st["kit"], st["mode"] = "S957", door_conf()["mode"]
            byday = st.get("by_day") or {}
            if flagged:
                k = "refused" if refused else "would_refuse"
                st[k + "_total"] = int(st.get(k + "_total") or 0) + 1
                ent = byday.setdefault(day, {})
                ent[k] = int(ent.get(k) or 0) + 1
                st["last_failure_iso"] = iso
            if admitted:
                st["last_admitted_iso"] = iso
            st["by_day"] = {d: byday[d] for d in sorted(byday)[-14:]}
            lf = st.get("last_failure_iso") or ""
            fresh = True
            if lf:
                try:
                    fresh = (t - datetime.strptime(lf, "%Y-%m-%dT%H:%M:%S")).total_seconds() > DOOR_RED_H * 3600
                except Exception:
                    fresh = False
            if (admitted or admitted is None) and fresh:
                st["last_ok_iso"] = iso
            tmp = DOOR_STATE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(st, f, indent=1, sort_keys=True)
            os.replace(tmp, DOOR_STATE)
    except Exception:
        pass


def keep_aside(handler, uid, when, iom, vm, why):
    """A refused punch: one row in REFUSED_CSV (0600), never in punches.csv. Never raises."""
    try:
        ip = handler.client_address[0] if handler.client_address else ""
        with _door_lock:
            fresh = not os.path.exists(REFUSED_CSV)
            fd = os.open(REFUSED_CSV, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as f:
                if fresh:
                    f.write(REFUSED_HEADER)
                f.write("%s,%s,%s,%s,%s,%s,%s\\n" % (str(uid).replace(",", " "), when, iom, vm, now_str(), ip, why))
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):
'''

L_CAP_OLD = '''                direction = {"0": "IN", "1": "OUT"}.get(iom, f"mode{iom}")
                wrote = save_punch(uid, when, iom, vm, live)
'''
L_CAP_NEW = '''                direction = {"0": "IN", "1": "OUT"}.get(iom, f"mode{iom}")
                admit, flagged, why = door_judge(self)              # S957: the door
                self._door = why
                if not admit:
                    self._door = "refused"
                    keep_aside(self, uid, when, iom, vm, why)
                    door_note(False, True, refused=True)
                    log(f"REFUSED user {uid}  {when}  {direction}  ({why}) -- kept aside in {REFUSED_CSV}, not stored -> response_code OK")
                    return "OK"
                wrote = save_punch(uid, when, iom, vm, live)
                door_note(True, flagged)
                if flagged:
                    log(f"DOOR   user {uid}  {when}  {direction}  ({why}) -- watch mode: stored, would be refused")
'''

L_SRC_OLD = '''                           "request_code": rc_hdr, "ack": ack, "punch": punch, "user_id": uid, "datetime": when,
                           "headers": hdrs}, ensure_ascii=True, sort_keys=True)
'''
L_SRC_NEW = '''                           "request_code": rc_hdr, "ack": ack, "punch": punch, "user_id": uid, "datetime": when,
                           "headers": hdrs, "door": getattr(handler, "_door", None)}, ensure_ascii=True, sort_keys=True)
'''

L_MAIN_OLD = '''    load_seen()
    log(f"attlistener v2 STANDALONE (capture + local ack) on :{PORT}  "
        f"loaded {len(_seen)} existing punch keys  DEBUG={DEBUG}  — NO upstream call  SOURCE_WATCH=S535")
'''
L_MAIN_NEW = '''    load_seen()
    door_note(None, False)                                   # S957: the door's state, at start-up
    log(f"attlistener v2 STANDALONE (capture + local ack) on :{PORT}  "
        f"loaded {len(_seen)} existing punch keys  DEBUG={DEBUG}  — NO upstream call  SOURCE_WATCH=S535  DOOR={door_conf()['mode']} (S957)")
'''


def make_listener(t):
    t = once(t, L_DOC_OLD, L_DOC_NEW, "listener doc")
    t = once(t, L_HANDLER_OLD, L_HANDLER_NEW, "listener door block")
    t = once(t, L_CAP_OLD, L_CAP_NEW, "listener capture")
    t = once(t, L_SRC_OLD, L_SRC_NEW, "listener source line")
    t = once(t, L_MAIN_OLD, L_MAIN_NEW, "listener start-up")
    return t


# ------------------------------------------------------------------------------------------------ att_source_summary.py
S_DOC_OLD = '''The listener's own test calls from this box (127.0.0.1 / ::1) are counted apart and never judged.
"""
'''
S_DOC_NEW = '''The listener's own test calls from this box (127.0.0.1 / ::1) are counted apart and never judged.
S957 (26-Nov-2026): a punches.csv row whose time the listener corrected (S792: the server's time stored, the machine's in the last
column) is matched on the machine's time too. A punch the door refused (S957, the line's "door" is "refused") is counted apart and
never judged as the machine's. Since S957 the door's mark is the key to the punch door, and this file travels with the nightly
bundle: a header's VALUE (outside the generic ones) is written only as its length, and every address only as its first two parts,
unless ATT_SUMMARY_KEEP=1 (the S957 installer, into its own 0700 scratch, never to OUT's default path).
"""
'''
S_READ_OLD = '''            if len(p) >= 5 and p[0] != "user_id" and p[4] >= since:
                out.append((p[0], p[1]))
'''
S_READ_NEW = '''            if len(p) >= 5 and p[0] != "user_id" and p[4] >= since:
                out.append((p[0], p[1], p[5] if len(p) >= 6 else ""))     # S957: + the machine's time (S792)
'''
S_PUN_OLD = '''    punches = [r for r in outside if r.get("punch")]
'''
S_PUN_NEW = '''    punches = [r for r in outside if r.get("punch") and r.get("door") != "refused"]          # S957
    refused = [r for r in outside if r.get("punch") and r.get("door") == "refused"]
'''
S_MISS_OLD = '''    missing = [x for x in punch_rows if x not in seen]
'''
S_MISS_NEW = '''    missing = [x[:2] for x in punch_rows if x[:2] not in seen and not (len(x) > 2 and x[2] and (x[0], x[2]) in seen)]   # S957
'''
S_MASK_OLD = '''    return {
        "kit": "S535_PUNCH_SOURCE_WATCH", "built": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
'''
S_MASK_NEW = '''    if os.environ.get("ATT_SUMMARY_KEEP") != "1":                       # S957: never the mark, never a full address
        def _mask_ip(a):
            a = str(a or "")
            return ".".join(a.split(".")[:2] + ["x", "x"]) if a.count(".") == 3 else (a.split(":")[0] + ":x" if ":" in a else a)
        for k, h in headers.items():
            if k not in GENERIC:
                h["commonest"] = [["<%d chars>" % len(str(v)), n] for v, n in h["commonest"]]
        merged = {}
        for a, d0 in by_ip.items():
            m_ = merged.setdefault(_mask_ip(a), {"punch": 0, "other": 0, "first": None, "last": None})
            m_["punch"] += d0["punch"]
            m_["other"] += d0["other"]
            m_["first"] = min(x for x in (m_["first"], d0["first"]) if x) if (m_["first"] or d0["first"]) else None
            m_["last"] = max(x for x in (m_["last"], d0["last"]) if x) if (m_["last"] or d0["last"]) else None
        by_ip = merged
        ips_shown = sorted({_mask_ip(a) for a in ips_on_punches})
    else:
        ips_shown = ips_on_punches
    return {
        "kit": "S535_PUNCH_SOURCE_WATCH", "built": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
'''
S_IPS_OLD = '''        "by_address": dict(by_ip), "addresses_on_punches": ips_on_punches,
'''
S_IPS_NEW = '''        "by_address": dict(by_ip), "addresses_on_punches": ips_shown, "addresses_on_punches_count": len(ips_on_punches),
'''
S_OUT_OLD = '''        "missing_examples": [list(x) for x in missing[:5]],
'''
S_OUT_NEW = '''        "missing_examples": [list(x) for x in missing[:5]],
        "refused_by_door": len(refused), "fixed_by": "S957",
'''


def make_summary(t):
    t = once(t, S_DOC_OLD, S_DOC_NEW, "summary doc")
    t = once(t, S_READ_OLD, S_READ_NEW, "summary read")
    t = once(t, S_PUN_OLD, S_PUN_NEW, "summary punches")
    t = once(t, S_MISS_OLD, S_MISS_NEW, "summary missing")
    t = once(t, S_OUT_OLD, S_OUT_NEW, "summary out")
    t = once(t, S_MASK_OLD, S_MASK_NEW, "summary mask")
    t = once(t, S_IPS_OLD, S_IPS_NEW, "summary addresses")
    return t


# ------------------------------------------------------------------------------------------------ callback_clock.py
C_DOC_OLD = '''CLI:  callback_clock.py          the run (what cron calls)
'''
C_DOC_NEW = '''S957_PUNCH_DOOR (session S523, 26-Nov-2026, roadmap E0): who is on duty is read through /root/portal/presence.py (on_duty moved
there): a punch-out ends a person's duty; when no punch at all has come by 09:30, or the machine is silent, the duty roster stands in
("on duty by roster"); presence.py missing -> every phone staff login, as for unreadable duty files. Nothing else changed.

CLI:  callback_clock.py          the run (what cron calls)
'''
C_FN_OLD = '''    rec = re.sub(r"[^a-z]", "", str(CC._cfg_path("PORTAL_RECEPTION_AGENT", RECEPTION) or RECEPTION).lower().split()[0]) or RECEPTION
    d = now.date().isoformat()
    try:
        staff, punches, ok = CC.load_duty(CC._cfg_path("SR_STAFF_MASTER", CC.STAFF_MASTER_DEFAULT),
                                          CC._cfg_path("SR_PUNCH_CSV", CC.PUNCH_CSV_DEFAULT), [d])
    except Exception:                                    # noqa: BLE001
        staff, punches, ok = {}, {}, False
    if not ok or not staff:
        return phone + [rec], "duty not known"
    on = []
    for k in phone:
        ent = staff.get(k)
        w = CC.duty_window(ent, d, punches.get(k, {}).get(d)) if ent else None
        if w and w[0] <= now <= w[1]:
            on.append(k)
    if on:
        return on + [rec], "on duty"
    return [rec] + [b for b in BACKUP if b not in phone], "no phone staff on duty"
'''
C_FN_NEW = '''    rec = re.sub(r"[^a-z]", "", str(CC._cfg_path("PORTAL_RECEPTION_AGENT", RECEPTION) or RECEPTION).lower().split()[0]) or RECEPTION
    try:                                                 # S957: the duty is read through presence.py (roadmap E0)
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import presence as PR                            # noqa: PLC0415
    except Exception:                                    # noqa: BLE001
        return phone + [rec], "duty not known (presence.py not loaded)"
    return PR.clock_on_duty(CC, now, phone, rec, BACKUP)
'''
C_FNDOC_OLD = '''    """(logins, why): the phone staff on duty now + the reception mobile; nobody on duty -> the reception mobile + the backup;
    the duty files unreadable -> every phone staff login + the reception mobile."""
'''
C_FNDOC_NEW = '''    """(logins, why): the phone staff on duty now + the reception mobile; nobody on duty -> the reception mobile + the backup;
    the duty files unreadable -> every phone staff login + the reception mobile. S957: read through presence.py (punch-out, the
    roster fallback)."""
'''


def make_clock(t):
    t = once(t, C_DOC_OLD, C_DOC_NEW, "clock doc")
    t = once(t, C_FNDOC_OLD, C_FNDOC_NEW, "clock on_duty doc")
    t = once(t, C_FN_OLD, C_FN_NEW, "clock on_duty body")
    return t


# ------------------------------------------------------------------------------------------------ freshness_legs.json
G_OLD = '''   "note": "S949 (roadmap F1a) · 23:40 nightly: the server's call log table compared with the Call_Durations Sheet, row by row; red at once when they differ or cannot be read; three equal nights with calls let the console read the table (F1b)"
  }
 ]
}'''
G_NEW = '''   "note": "S949 (roadmap F1a) · 23:40 nightly: the server's call log table compared with the Call_Durations Sheet, row by row; red at once when they differ or cannot be read; three equal nights with calls let the console read the table (F1b)"
  },
  {
   "name": "punch door",
   "group": "Attendance",
   "kind": "state_json",
   "target": "/root/punch_door.state.json",
   "field": "last_ok_iso",
   "fail_field": "last_failure_iso",
   "max_age_h": 74,
   "note": "S957 (F-773, roadmap E0) · the punch listener admits only the attendance machine's own mark; red for a day after a punch without it was refused (kept aside in /root/punches_refused.csv, never lost) · three days with no punch, as the punch file"
  }
 ]
}'''


def make_legs(t):
    return once(t, G_OLD, G_NEW, "legs")


def main(argv):
    if len(argv) != 6:
        raise SystemExit(__doc__)
    srcs = dict(zip(("attlistener_v2.py", "att_source_summary.py", "callback_clock.py", "freshness_legs.json"), argv[1:5]))
    out = argv[5]
    os.makedirs(out, exist_ok=True)
    fns = {"attlistener_v2.py": make_listener, "att_source_summary.py": make_summary, "callback_clock.py": make_clock,
           "freshness_legs.json": make_legs}
    for name, path in srcs.items():
        raw = open(path, "rb").read()
        h = hashlib.md5(raw).hexdigest()
        if h != FROM[name]:
            raise SystemExit("REFUSED %s: %s is %s, not the FROM %s" % (name, path, h[:8], FROM[name][:8]))
        new = fns[name](raw.decode("utf-8"))
        with open(os.path.join(out, name), "wb") as f:
            f.write(new.encode("utf-8"))
        print("MADE %s %s -> %s" % (name, h[:8], hashlib.md5(new.encode("utf-8")).hexdigest()[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
