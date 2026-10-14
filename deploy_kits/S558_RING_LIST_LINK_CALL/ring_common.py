#!/usr/bin/env python3
# ring_common.py -- kit S366_RING_POPUP (session 279, 22-Sep-2026)
# What the ring-hook service and the portal share: the config files beside the portal, the push
# subscriptions, the agent-phone -> login map, the caller lookup in finance.db, and one webpush call.
#
# EVERY value with a number or a key in it lives in a 0600 file under /root/portal, never here (F-185):
#   ring_hook.env        RING_HOOK_SECRET · RING_INTERNAL_KEY · RING_HOOK_PORT · VAPID_PUBLIC · VAPID_SUBJECT
#   vapid_private.pem    the Web Push signing key (generated once by the installer)
#   push_subs.json       {"users": {"<login>": [ {endpoint, keys{p256dh,auth}, ua, added} ]}}
#   ring_agents.json     {"agents": {"<10 digits>": {"user": "<login>", "name": "<name>"}}}
# The caller is looked up in finance.db by the SAME salted fingerprint the clinic PC writes
# (finance_patient_match.fingerprint; salt at /root/finance/patient_fp.env) -- finance.db holds no
# raw mobile (S279 finding: patient_ref.mobile is empty on the VPS; mobile_fp is filled).
#
# S558_RING_LIST_LINK_CALL (14-Oct-2026, D726 (2) -- the owner: "the second number is remembered for future calls"):
# lookup_caller also reads the after-call list's links (ring_outcomes.db, table appt_link, READ-ONLY, its own path
# constant RING_STORE). A patient a person linked to this 10-digit number ('Haan, yahi hai') is added once, with
# "linked": True -- so the next call from that number shows the patient and offers the known list. Only while the
# owner's switch link_on is on; an undone link is not read; any error is ignored. Nothing else in this file changed.
import json
import os
import re
import sqlite3
import time

PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.environ.get("RING_HOOK_ENV", os.path.join(PORTAL_DIR, "ring_hook.env"))
SUBS_FILE = os.environ.get("PUSH_SUBS_FILE", os.path.join(PORTAL_DIR, "push_subs.json"))
AGENTS_FILE = os.environ.get("RING_AGENTS_FILE", os.path.join(PORTAL_DIR, "ring_agents.json"))
FINANCE_DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
FINANCE_DIR = os.environ.get("FINANCE_DIR", "/root/finance")
RING_STORE = os.environ.get("RING_OUTCOME_DB", os.path.join(PORTAL_DIR, "ring_outcomes.db"))   # S558: the links, read-only
MAX_SUBS_PER_USER = 6
_DIGITS = re.compile(r"\D+")


def load_env(path=None):
    """KEY=value lines -> dict. Never printed anywhere."""
    out = {}
    try:
        with open(path or ENV_FILE, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def _atomic_write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else default
    except Exception:
        return default


# ------------------------------------------------------------------ subscriptions
def load_subs(path=None):
    d = _read_json(path or SUBS_FILE, {"users": {}})
    if not isinstance(d.get("users"), dict):
        d["users"] = {}
    return d


def subs_for(user, path=None):
    return [s for s in load_subs(path)["users"].get(str(user), []) if isinstance(s, dict) and s.get("endpoint")]


def add_sub(user, sub, ua="", path=None):
    """Store one browser's subscription under a login. Same endpoint twice = refreshed, not doubled."""
    if not (isinstance(sub, dict) and sub.get("endpoint") and isinstance(sub.get("keys"), dict)
            and sub["keys"].get("p256dh") and sub["keys"].get("auth")):
        return False
    path = path or SUBS_FILE
    d = load_subs(path)
    lst = [s for s in d["users"].get(str(user), []) if s.get("endpoint") != sub["endpoint"]]
    lst.append({"endpoint": sub["endpoint"], "keys": {"p256dh": sub["keys"]["p256dh"], "auth": sub["keys"]["auth"]},
                "ua": str(ua or "")[:120], "added": int(time.time())})
    d["users"][str(user)] = lst[-MAX_SUBS_PER_USER:]
    _atomic_write_json(path, d)
    return True


def remove_sub(user, endpoint, path=None):
    path = path or SUBS_FILE
    d = load_subs(path)
    before = d["users"].get(str(user), [])
    after = [s for s in before if s.get("endpoint") != endpoint]
    if len(after) != len(before):
        d["users"][str(user)] = after
        _atomic_write_json(path, d)
        return True
    return False


# ------------------------------------------------------------------ agents
def mobile10(raw):
    d = _DIGITS.sub("", str(raw or ""))
    if len(d) > 10:
        d = d[2:] if (d.startswith("91") and len(d) == 12) else (d[1:] if (d.startswith("0") and len(d) == 11) else d[-10:])
    return d if len(d) == 10 else ""


def load_agents(path=None):
    d = _read_json(path or AGENTS_FILE, {"agents": {}})
    return d.get("agents") if isinstance(d.get("agents"), dict) else {}


def agent_for(phone, agents=None):
    """{'user','name'} for a ringing agent phone, or None."""
    a = load_agents() if agents is None else agents
    m = mobile10(phone)
    hit = a.get(m) if m else None
    return hit if (isinstance(hit, dict) and hit.get("user")) else None


# ------------------------------------------------------------------ caller lookup
def _fp(m10):
    try:
        import sys
        if FINANCE_DIR not in sys.path:
            sys.path.insert(0, FINANCE_DIR)
        import finance_patient_match as fpm          # the clinic's own salt + fingerprint (never re-implemented)
        return fpm.fingerprint(m10, fpm.salt())
    except Exception:
        return ""


def _dmy(iso):
    """2026-08-12 -> 12 Aug 2026 (the way the counter says it)."""
    try:
        y, mo, d = iso[:10].split("-")
        return "%d %s %s" % (int(d), ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(mo)], y)
    except Exception:
        return iso or ""


def _linked_ids(m10, store=None):
    """S558 (D726 (2)): the clinic IDs a person on the after-call list linked to this 10-digit number ('Haan, yahi hai'),
    newest first. ring_outcomes.db opened READ-ONLY; only while the owner's switch link_on is on; an undone link is
    not read; any error (no store, no table yet) -> none."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (store or RING_STORE), uri=True, timeout=3)
    except Exception:
        return []
    try:
        on = con.execute("SELECT v FROM kv WHERE k='link_on'").fetchone()
        if not on or str(on[0]) != "1":
            return []
        out = []
        for (cid,) in con.execute("SELECT clinic_id FROM appt_link WHERE mobile=? AND COALESCE(undone_at,'')='' "
                                  "ORDER BY linked_at DESC, id DESC", (m10,)):
            cid = str(cid or "").strip()
            if cid and cid not in out:
                out.append(cid)
        return out
    except Exception:
        return []
    finally:
        con.close()


def lookup_caller(phone, db_path=None, store=None):
    """Everything the pop-up says about a number: full number (owner ruling 21-Sep-2026), the patients on it
    (name, clinic id, last visit, visit count, whether a procedure), newest first. Read-only; never raises.
    S558: then each patient linked to this number on the after-call list, once, with "linked": True (by the 10 digits,
    so a number whose fingerprint cannot be made still reads its links)."""
    m10 = mobile10(phone)
    out = {"mobile": m10 or str(phone or ""), "patients": [], "fp_ok": False}
    if not m10:
        return out
    fp = _fp(m10)
    links = _linked_ids(m10, store)                              # S558
    if not fp and not links:
        return out
    out["fp_ok"] = bool(fp)
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (db_path or FINANCE_DB), uri=True, timeout=3)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT clinic_id, name, patient_uid, last_seen, first_seen FROM patient_ref "
            "WHERE mobile_fp=? AND (merged_into IS NULL OR merged_into='') "
            "ORDER BY COALESCE(last_seen,'') DESC, id DESC LIMIT 6", (fp,)).fetchall() if fp else []
        for r in rows:
            uid = r["patient_uid"] or ""
            v = con.execute(
                "SELECT visit_date, had_procedure, COUNT(*) OVER () n FROM patient_visit "
                "WHERE (patient_uid=? AND ?<>'') OR (clinic_id=? AND ?<>'') "
                "ORDER BY visit_date DESC LIMIT 1", (uid, uid, r["clinic_id"] or "", r["clinic_id"] or "")).fetchone()
            out["patients"].append({
                "name": (r["name"] or "").strip(), "clinic_id": str(r["clinic_id"] or ""),
                "last_visit": (v["visit_date"] if v else (r["last_seen"] or ""))[:10],
                "visits": int(v["n"]) if v else 0,
                "procedure": bool(v and str(v["had_procedure"] or "").strip().lower() in ("1", "y", "yes", "true", "p"))})
        for cid in links:                                        # S558: linked on the after-call list ('Haan, yahi hai')
            if any(p["clinic_id"] == cid for p in out["patients"]):
                continue
            r = con.execute(
                "SELECT clinic_id, name, patient_uid, last_seen FROM patient_ref WHERE clinic_id=? "
                "ORDER BY (merged_into IS NULL OR merged_into='') DESC, id DESC LIMIT 1", (cid,)).fetchone()
            uid = (r["patient_uid"] if r else "") or ""
            v = con.execute(
                "SELECT visit_date, had_procedure, COUNT(*) OVER () n FROM patient_visit "
                "WHERE (patient_uid=? AND ?<>'') OR (clinic_id=? AND ?<>'') "
                "ORDER BY visit_date DESC LIMIT 1", (uid, uid, cid, cid)).fetchone()
            out["patients"].append({
                "name": ((r["name"] if r else "") or "").strip(), "clinic_id": cid,
                "last_visit": (v["visit_date"] if v else ((r["last_seen"] if r else "") or ""))[:10],
                "visits": int(v["n"]) if v else 0,
                "procedure": bool(v and str(v["had_procedure"] or "").strip().lower() in ("1", "y", "yes", "true", "p")),
                "linked": True})
        con.close()
    except Exception:
        pass
    return out


def caller_card(info):
    """(title, body) for the notification. Hindi for the staff phone; names as the counter wrote them."""
    m = info.get("mobile") or ""
    ps = info.get("patients") or []
    if not ps:
        return ("\U0001F4DE नया नंबर · " + m,          # 📞 नया नंबर · <number>
                "कोई record नहीं")                           # कोई record नहीं
    if len(ps) == 1:
        p = ps[0]
        bits = []
        if p["clinic_id"]:
            bits.append("ID " + p["clinic_id"])
        if p["last_visit"]:
            bits.append("आखिरी visit " + _dmy(p["last_visit"]) + (" (procedure)" if p["procedure"] else ""))
        if p["visits"]:
            bits.append("कुल %d visit" % p["visits"])
        return ("\U0001F4DE " + (p["name"] or "?") + " · " + m, " · ".join(bits) or "पुराने मरीज़")
    head = "\U0001F4DE " + m + " · %d मरीज़" % len(ps)          # 📞 <number> · N मरीज़
    parts = []
    for p in ps[:3]:
        s = p["name"] or "?"
        extra = [x for x in (("ID " + p["clinic_id"]) if p["clinic_id"] else "", _dmy(p["last_visit"]) if p["last_visit"] else "") if x]
        if extra:
            s += " (" + ", ".join(extra) + ")"
        parts.append(s)
    if len(ps) > 3:
        parts.append("+%d" % (len(ps) - 3))
    return (head, " · ".join(parts))


# ------------------------------------------------------------------ the push itself
def send_push(sub, payload, env=None, timeout=6, pusher=None):
    """One notification to one browser. Returns (ok, http_status_or_reason, gone).
    gone=True means the subscription is dead (404/410) and the caller should drop it."""
    env = env or load_env()
    pem = env.get("VAPID_PRIVATE_PEM_FILE") or os.path.join(PORTAL_DIR, "vapid_private.pem")
    subj = env.get("VAPID_SUBJECT") or "mailto:clinic@dr-manoj.in"
    try:
        if pusher is None:
            from pywebpush import webpush, WebPushException
        else:
            webpush, WebPushException = pusher, Exception
        r = webpush(subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                    data=json.dumps(payload, ensure_ascii=False), vapid_private_key=pem,
                    vapid_claims={"sub": subj}, ttl=int(payload.get("ttl", 90)), timeout=timeout,
                    headers={"Urgency": "high"})
        code = getattr(r, "status_code", 201)
        return (200 <= int(code) < 300, code, int(code) in (404, 410))
    except Exception as e:  # noqa: BLE001
        resp = getattr(e, "response", None)
        code = getattr(resp, "status_code", None)
        return (False, code or type(e).__name__, code in (404, 410))


def push_user(user, payload, env=None, pusher=None, subs_path=None):
    """Every browser this login has allowed. Dead subscriptions are dropped. Returns (sent, failed)."""
    sent = failed = 0
    for s in subs_for(user, subs_path):
        ok, _code, gone = send_push(s, payload, env=env, pusher=pusher)
        if ok:
            sent += 1
        else:
            failed += 1
            if gone:
                remove_sub(user, s["endpoint"], subs_path)
    return sent, failed
