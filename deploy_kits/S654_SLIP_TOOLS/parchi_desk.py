#!/usr/bin/python3
# -*- coding: utf-8 -*-
# S654_SLIP_TOOLS (session 354, 25-Oct-2026; D789): No. / Hatao on the day's rows -- api_renumber / api_void below.
"""parchi_desk.py -- kit S637_PARCHI_DESK (session S347, 24-Oct-2026; D775). PARENT.
Mounted by slip_log.init() and lives beside it. Flask and the standard library only.

THE OWNER, 23/24-Oct-2026 (D775): "all the entries need to be on one page only" · "Parchi - a warning helps in duplicate
entries cases, remaining ones go to shavez, and i also get have this desk available to me, if any need is there due to
staff absence" · "Flow should be quick and easy as much as possible, with minimum typing, by taps".

THE DESK. One laptop page for Shavez and the owner -- OPD, X-ray/Proc and Blood test side by side, the day's list below;
no page reload, no tabs (it stacks on a phone).
    OPD        the next parchi number filled, the clinic ID typed, the name shown, Enter saves.
    X-ray/Proc the patient tapped from the day's OPD chips (live: a chip appears the moment an OPD parchi saves, on any
               screen), items tapped from tiles (most-used first, a search box above them), side R/L tapped, the rate
               filled, Chhoot only on a tap. The same item twice on one parchi warns at once -- Keep / Remove.
    Blood test the patient tapped, Save.
    Undo       takes back your own last entry of the day.
No Paid / Done ticks: Paid comes from Docterz at night; billed is done (D774's rule, applied to X-rays too).

EVERY PARCHI RULE STAYS. Each save goes through slip_log.log_slip and slip_log.items_from_form exactly as the old pages
do: the book and its numbers, gaps (a big jump asks "yes, this number"), the late day (LATE_DAYS), a new or far-ahead
clinic ID, the chhoot / free with a reason going to slip_adjust for approval. The blood test keeps its one-per-day rule.
Only the screen is new; the phone menu and the old pages stay as the fallback.

It writes no table of its own. Undo voids the slip (a same-day correction, audited), the "missing" numbers that save
created, and any chhoot that save sent for approval; a blood test is voided as the old page does.
No patient name, no number, no secret in this file (F-185).
"""
import datetime as dt
import json

from flask import Blueprint, jsonify, request

bp = Blueprint("parchi_desk", __name__)
_db = _require = _audit = None
UNIT = "slips"
POLL_S = 8


def init(app, db_getter, require_fn, audit_fn=None, unit="slips"):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp)
    return bp


def _SL():
    import slip_log                                      # noqa: PLC0415 -- beside this file, mounted first
    return slip_log


def _gate():
    u, err = _require("maker", "checker", unit=UNIT)
    return u, err


def _eng(u):
    return "checker" in set((u or {}).get("roles") or []) and "maker" not in set((u or {}).get("roles") or [])


# ---------------------------------------------------------------- the day, as the desk shows it
def state(con, day, who):
    SL = _SL()
    SL.ensure(con)
    SL.blood_ensure(con)
    SL.fill_new_names(con)
    today = SL._today()
    rows = SL.day_slips(con, day)
    opd, xp, miss = [], [], []
    for s in rows:
        if s["state"] == "missing":
            miss.append(dict(series=s["series"], no=s["slip_no"]))
            continue
        if s["state"] != "ok":
            continue
        name = s.get("name_seen") or s.get("no_id_name") or ((SL.patient(con, s["clinic_id"]) or ("", ""))[0] if s["clinic_id"] else "")
        e = dict(id=s["id"], no=s["slip_no"], cid=s["clinic_id"], name=name, new=bool(s["is_new"]), noid=bool(s["no_id_name"]),
                 by=s["logged_by"], at=(s["logged_at"] or "")[11:16], ts=s["logged_at"] or "")
        if s["series"] == "opd":
            opd.append(e)
        else:
            e["items"] = [dict(n=it["name"], side=it.get("side") or "", p=int(it.get("price_p") or 0), d=int(it.get("discount_p") or 0))
                          for it in s.get("items", [])]
            e["total"] = sum(i["p"] - i["d"] for i in e["items"])
            xp.append(e)
    blood = []
    for r in con.execute("SELECT * FROM blood_order WHERE day=? AND state='ok' ORDER BY id", (day,)):
        blood.append(dict(id=r["id"], cid=r["clinic_id"], name=r["name_seen"] or "", by=r["logged_by"], at=(r["logged_at"] or "")[11:16],
                          ts=r["logged_at"] or ""))
    last = None
    if day == today:
        me = (who or "").lower()
        cands = [("slip", e["id"], e["ts"], "OPD %d" % e["no"]) for e in opd if (e["by"] or "").lower() == me]
        cands += [("slip", e["id"], e["ts"], "X-ray/Proc %d" % e["no"]) for e in xp if (e["by"] or "").lower() == me]
        cands += [("blood", b["id"], b["ts"], "Blood %s" % b["cid"]) for b in blood if (b["by"] or "").lower() == me]
        cands = [c for c in cands if (c[2] or "")[:10] == today]          # typed today, not merely belonging to today
        if cands:
            k = max(cands, key=lambda c: (c[2], c[0] == "blood", c[1]))
            last = dict(kind=k[0], id=k[1], label=k[3])
    return dict(day=day, today=today, day_word=SL._day_word(day), nx_opd=SL.next_no(con, "opd"), nx_xp=SL.next_no(con, "xp"),
                opd=opd, xp=xp, blood=blood, missing=miss, last=last)


def tiles(con):
    SL = _SL()
    xr, pr = SL.services(con)
    use = SL.usage_counts(con)
    out = []
    for kind, rows in (("xray", xr), ("proc", pr)):
        rows = sorted(rows, key=lambda r: (-int(use.get(r["id"], 0)), r["name"].lower()))
        for r in rows:
            out.append(dict(id=r["id"], k=kind, n=r["name"], p=int(r["price_p"] or 0), s=1 if r["side"] else 0,
                            a=SL._aliases(kind, r["name"]).lower(), u=int(use.get(r["id"], 0))))
    return out


def _j(**kw):
    return jsonify(**kw)


def _day_arg(v):
    SL = _SL()
    return SL._late_day(v or "")


# ---------------------------------------------------------------- the doors
@bp.route("/finance/slips/desk")
def page():
    u, err = _gate()
    SL = _SL()
    if err:
        return SL._shell("Parchi desk", SL._denied(), "en")
    con = _db()
    day = _day_arg(request.args.get("day")) or SL._today()
    st = state(con, day, SL._who(u))
    eng = _eng(u)
    days = []
    t = SL._now().date()
    for i in range(SL.LATE_DAYS + 1):
        d = (t - dt.timedelta(days=i)).isoformat()
        days.append((d, ("Today" if eng else "Aaj") if i == 0 else (("Yesterday" if eng else "Kal") if i == 1 else SL._dmy(d)[:6])))
    boot = json.dumps(dict(state=st, tiles=tiles(con), eng=eng, poll=POLL_S, days=days,
                           reasons=[dict(k=k, hi=h, en=e) for k, h, e in _reasons()]),
                      ensure_ascii=False).replace("</", "<\\/")
    return PAGE.replace("__BOOT__", boot).replace("__LANG__", "en" if eng else "hi").replace(
        "__TITLE__", "Parchi desk" if eng else "Parchi desk")


def _reasons():
    try:
        import slip_adjust                               # noqa: PLC0415
        return slip_adjust.REASONS
    except Exception:                                    # noqa: BLE001
        return (("staff", "Staff / ghar wale", "staff / family"), ("poor", "Garib mareez", "poor patient"),
                ("redo", "Dobara / redo", "repeat / redo"), ("doctor", "Doctor ke kehne par", "doctor's instruction"),
                ("other", "Kuch aur", "other"))


@bp.route("/finance/slips/desk/api/state")
def api_state():
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    day = _day_arg(request.args.get("day")) or SL._today()
    return _j(ok=True, state=state(_db(), day, SL._who(u)))


@bp.route("/finance/slips/desk/api/patient")
def api_patient():
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    cid = SL._clean_id(request.args.get("id"))
    if not cid:
        return _j(ok=False)
    day = _day_arg(request.args.get("day")) or SL._today()
    p = SL.patient(con, cid)
    new = SL.is_new_id(con, cid, day)
    if p:
        return _j(ok=True, known=True, name=p[0], new=new, far=False)
    hi = SL.highest_id(con)
    n = SL._int(cid)
    far = bool(hi and n is not None and n > hi + SL.ID_JUMP)
    return _j(ok=True, known=False, name="", new=new, far=far, highest=hi)


def _body():
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:                                    # noqa: BLE001
        return {}


@bp.route("/finance/slips/desk/api/save", methods=["POST"])
def api_save():
    """One parchi through log_slip, exactly the old pages' rules. JSON in, JSON out."""
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    f = _body()
    series = f.get("series") if f.get("series") in SL.SERIES_NAME else ""
    if not series:
        return _j(ok=False, err="Galat form.")
    eng = _eng(u)
    noid = bool(f.get("noid"))
    cid = "" if noid else SL._clean_id(f.get("clinic_id"))
    nm = (str(f.get("no_id_name") or "")).strip()[:60] if noid else ""
    if not noid and str(f.get("clinic_id") or "").strip() and not cid:
        return _j(ok=False, err="Clinic ID mein sirf number likhein.")
    if cid and not SL.patient(con, cid) and not f.get("id_ok"):
        hi, n = SL.highest_id(con), SL._int(cid)
        if hi and n is not None and n > hi + SL.ID_JUMP:
            return _j(ok=False, ask="id_ok", err="ID %s sabse bade ID %d se bahut aage hai — dobara dekhein; sahi ho to "
                                                  "'ID sahi hai' dabayein." % (cid, hi))
    day = _day_arg(f.get("day"))
    if day is None:
        return _j(ok=False, err="Din sahi chunein — aaj se %d din pehle tak." % SL.LATE_DAYS)
    form = {}
    if series == "xp":
        nx = np_ = 0
        for it in (f.get("items") or [])[: SL.MAX_XRAY + SL.MAX_PROC]:
            kind = "xray" if it.get("k") == "xray" else "proc"
            if kind == "xray":
                i, nx = nx, nx + 1
                if i >= SL.MAX_XRAY:
                    return _j(ok=False, err="Ek parchi par %d se zyada X-ray nahi." % SL.MAX_XRAY)
            else:
                i, np_ = np_, np_ + 1
                if i >= SL.MAX_PROC:
                    return _j(ok=False, err="Ek parchi par %d se zyada procedure nahi." % SL.MAX_PROC)
            key = "%s%d" % (kind, i)
            form[key] = str(it.get("id") or "")
            form[key + "_side"] = str(it.get("side") or "")
            if it.get("free"):
                form[key + "_free"] = "1"
            if it.get("disc"):
                form[key + "_disc"] = str(it.get("disc"))
            form[key + "_why"] = str(it.get("why") or "")
    try:
        items = SL.items_from_form(con, form) if series == "xp" else []
        sid, note = SL.log_slip(con, SL._who(u), series, SL._int(f.get("slip_no")), cid, nm, items,
                                confirm_gap=bool(f.get("gap_ok")), day=day)
    except SL.SlipError as ex:
        msg = str(ex)
        return _j(ok=False, err=msg, ask="gap_ok" if "Haan, yahi number" in msg else "")
    r = con.execute("SELECT slip_no FROM slip WHERE id=?", (sid,)).fetchone()
    who_ = cid or nm
    p = SL.patient(con, cid) if cid else None
    msg = ("Parchi %d saved — %s%s." if eng else "Parchi %d save — %s%s.") % (r["slip_no"], who_, (" · " + p[0]) if p else "")
    return _j(ok=True, msg=msg + ((" " + note) if note else ""), id=sid, state=state(con, day, SL._who(u)))


@bp.route("/finance/slips/desk/api/blood", methods=["POST"])
def api_blood():
    """The blood test, with the old page's rule: one per patient per day."""
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    SL.blood_ensure(con)
    f = _body()
    cid = SL._clean_id(f.get("clinic_id"))
    if not cid:
        return _j(ok=False, err="Mareez chunein ya clinic ID likhein.")
    day = SL._today()
    if con.execute("SELECT 1 FROM blood_order WHERE day=? AND clinic_id=? AND state='ok'", (day, cid)).fetchone():
        return _j(ok=False, err="ID %s ka blood test aaj pehle se likha hai." % cid)
    p = SL.patient(con, cid)
    c = con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
                    (day, cid, p[0] if p else "", SL._who(u), SL._stamp()))
    SL._audit_safe(con, c.lastrowid, "blood_order", None, json.dumps({"cid": cid, "via": "desk"}), SL._who(u))
    con.commit()
    return _j(ok=True, msg="Blood test: %s%s" % (cid, (" · " + p[0]) if p else ""), state=state(con, day, SL._who(u)))


@bp.route("/finance/slips/desk/api/undo", methods=["POST"])
def api_undo():
    """Your own last entry of today, only. A parchi: voided as a same-day correction, with the 'missing' numbers its save
    created and any chhoot it sent for approval. A blood test: voided as the old page does."""
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    SL.blood_ensure(con)
    who = SL._who(u)
    today = SL._today()
    st = state(con, today, who)
    f = _body()
    last = st.get("last")
    if not last or last["kind"] != f.get("kind") or int(last["id"]) != int(f.get("id") or 0):
        return _j(ok=False, err="Sirf aapki aaj ki aakhri entry wapas ho sakti hai.", state=st)
    now = SL._stamp()
    if last["kind"] == "blood":
        con.execute("UPDATE blood_order SET state='void' WHERE id=? AND state='ok'", (last["id"],))
        SL._audit_safe(con, last["id"], "blood_void", None, json.dumps({"via": "desk undo"}), who)
    else:
        s = con.execute("SELECT * FROM slip WHERE id=? AND state='ok'", (last["id"],)).fetchone()
        if s is None:
            return _j(ok=False, err="Parchi pehle hi badal chuki.", state=st)
        con.execute("UPDATE slip SET state='void', note=?, updated_by=?, updated_at=? WHERE id=?",
                    ("same-day correction (desk undo)", who, now, s["id"]))
        gaps = con.execute("SELECT id FROM slip WHERE series=? AND state='missing' AND logged_by=? AND logged_at=? AND day=?",
                           (s["series"], s["logged_by"], s["logged_at"], s["day"])).fetchall()
        for g in gaps:
            con.execute("UPDATE slip SET state='void', note='desk undo', updated_by=?, updated_at=? WHERE id=?", (who, now, g["id"]))
        try:
            con.execute("UPDATE slip_adjust SET state='replaced' WHERE slip_id=? AND state='pending'", (s["id"],))
        except Exception:                                # noqa: BLE001 -- no slip_adjust table: nothing to take back
            pass
        SL._audit_safe(con, s["id"], "slip_void", json.dumps({"state": "ok"}),
                       json.dumps({"state": "void", "why": "desk undo", "gaps": len(gaps)}), who)
    con.commit()
    return _j(ok=True, msg="Wapas le liya: %s." % last["label"], state=state(con, today, who))


@bp.route("/finance/slips/desk/api/renumber", methods=["POST"])
def api_renumber():
    """S654 (D789): a saved parchi of the day shown gets a new number. JSON {id, no, why} in; the day's state out."""
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    f = _body()
    who = SL._who(u)
    day = _day_arg(f.get("day"))
    if day is None:
        return _j(ok=False, err="Din sahi chunein.")
    try:
        old, new = SL.renumber_slip(con, who, int(f.get("id") or 0), f.get("no"), f.get("why"))
    except SL.SlipError as ex:
        return _j(ok=False, err=str(ex), state=state(con, day, who))
    except (TypeError, ValueError):
        return _j(ok=False, err="Galat form.")
    return _j(ok=True, msg="Parchi %d ab %d hai." % (old, new), state=state(con, day, who))


@bp.route("/finance/slips/desk/api/void", methods=["POST"])
def api_void():
    """S654 (D789): a saved parchi of the day shown is taken off, with a reason. JSON {id, why} in; the day's state out."""
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    f = _body()
    who = SL._who(u)
    day = _day_arg(f.get("day"))
    if day is None:
        return _j(ok=False, err="Din sahi chunein.")
    try:
        no = SL.void_past_slip(con, who, int(f.get("id") or 0), f.get("why"))
    except SL.SlipError as ex:
        return _j(ok=False, err=str(ex), state=state(con, day, who))
    except (TypeError, ValueError):
        return _j(ok=False, err="Galat form.")
    return _j(ok=True, msg="Parchi %d hata di." % no, state=state(con, day, who))


# ---------------------------------------------------------------- the page
PAGE = r"""<!doctype html><html lang="__LANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>__TITLE__</title><style>
:root{--ink:#14181c;--mut:#46525b;--line:#9fb0bb;--accent:#14456e;--paper:#fff;--bg:#e4eaee;--entry:#fffbe6;
 --ok:#2c6e2f;--okbg:#dff0d8;--bad:#9c2a20;--badbg:#fadbd8;--warn:#8a5a00;--warnbg:#fdf0d5}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.45 "Segoe UI",system-ui,-apple-system,sans-serif}
.top{position:static;display:flex;flex-wrap:wrap;align-items:center;gap:10px;background:var(--accent);color:#fff;padding:8px 12px}
.top a{color:#fff;text-decoration:none;font-weight:600;border:2px solid #fff;border-radius:8px;padding:8px 12px;min-height:44px;display:inline-flex;align-items:center}
.top h1{font-size:19px;margin:0;flex:1;min-width:140px}
.top select{font-size:16px;min-height:44px;border-radius:8px;border:2px solid #fff;padding:4px 8px}
.top button.undo{background:#fff;color:var(--accent);border:0;border-radius:8px;min-height:44px;padding:6px 14px;font-weight:700;font-size:16px}
main{padding:10px;max-width:1400px;margin:0 auto}
#msg{position:sticky;top:0;z-index:4}
.ok,.bad{padding:10px 14px;margin:0 0 10px;border-radius:8px;font-size:17px}
.ok{background:var(--okbg);border-left:6px solid var(--ok)}.bad{background:var(--badbg);border-left:6px solid var(--bad)}
.cols{display:grid;grid-template-columns:1fr 1.6fr 1fr;gap:10px;align-items:start}
@media(max-width:980px){.cols{grid-template-columns:1fr}}
.box{background:var(--paper);border:2px solid var(--line);border-radius:12px;padding:12px}
.box h2{margin:0 0 8px;font-size:19px;color:var(--accent);display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.box h2 small{font-size:15px;color:#3c464e;font-weight:700}
label.f{display:block;font-size:16px;color:#3c464e;margin:0 0 8px;font-weight:600}
input,select{font:inherit;font-size:19px;min-height:48px;padding:6px 10px;border:2px solid #6b7b86;border-radius:8px;background:var(--entry);width:100%}
input:focus{outline:3px solid #9dc0e0;border-color:var(--accent);background:#fff}
input.no{font-weight:700;color:var(--accent)}
.name{min-height:26px;font-weight:600;font-size:16px;margin:-2px 0 8px}.name.known{color:var(--ok)}.name.new{color:var(--warn)}.name.far{color:var(--bad)}
button{font:inherit;cursor:pointer}
button.go{background:var(--accent);color:#fff;border:0;border-radius:10px;padding:12px;font-size:19px;font-weight:700;width:100%;min-height:52px}
button.go:disabled{opacity:.5}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px;max-height:156px;overflow:auto}
.chip{border:2px solid var(--line);background:#fff;border-radius:20px;padding:6px 12px;font-size:15px;min-height:42px;color:var(--ink)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:700;animation:none}
.chip.fresh{animation:fl 1.6s ease-out}@keyframes fl{0%{background:#ffe9a8}100%{background:#fff}}
.chips:empty::after{content:attr(data-empty);font-size:15px;color:#3c464e}
.who{font-size:16px;color:#3c464e;margin:0 0 8px;font-weight:600}.who b{color:var(--ink)}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px;max-height:300px;overflow:auto;margin:0 0 8px}
.tile{display:flex;flex-direction:column;align-items:flex-start;gap:2px;text-align:left;border:2px solid var(--line);border-radius:10px;background:#fff;
 padding:7px 9px;min-height:56px;font-size:14px;color:var(--ink)}
.tile em{font-style:normal;font-weight:700;color:var(--accent);font-size:15px}.tile.proc{border-color:#b9a36a}
.tile:active{background:var(--entry)}
.kinds{display:flex;gap:6px;margin:0 0 6px}.kinds button{flex:1;min-height:42px;border:2px solid var(--accent);background:#fff;color:var(--accent);border-radius:8px;font-weight:600}
.kinds button.on{background:var(--accent);color:#fff}
.sel .it{background:var(--okbg);border:2px solid var(--ok);border-radius:10px;padding:8px;margin:0 0 6px}
.sel .it.dup{background:var(--warnbg);border-color:var(--warn)}
.sel .row1{display:flex;align-items:center;gap:8px}.sel .nm{flex:1;font-weight:600;min-width:0}.sel .pr{font-weight:700;white-space:nowrap}
.sel .x{min-width:44px;min-height:44px;border:2px solid var(--bad);color:var(--bad);background:#fff;border-radius:8px;font-size:18px;font-weight:700}
.sel .sd{display:flex;gap:6px;margin-top:6px}.sel .sd button,.sel .cb{min-height:46px;min-width:60px;font-size:17px;border:2px solid var(--accent);background:#fff;color:var(--accent);border-radius:8px;font-weight:700}
.sel .sd button.on{background:var(--accent);color:#fff}
.sel .ch{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;align-items:center}.sel .ch input{width:120px;min-height:42px;font-size:17px}
.sel .ch button{min-height:46px;border:2px solid #6b7b86;background:#fff;border-radius:10px;padding:6px 12px;font-size:16px;font-weight:600}.sel .ch button.on{background:var(--warn);border-color:var(--warn);color:#fff}
.dupw{background:var(--warnbg);border-left:6px solid var(--warn);padding:8px 10px;margin:6px 0 0;border-radius:6px;font-weight:600}
.dupw button{margin:6px 8px 0 0;min-height:42px;border-radius:8px;border:2px solid var(--warn);background:#fff;padding:4px 14px;font-weight:700}
.tot{font-size:19px;font-weight:700;color:#fff;background:var(--accent);border-radius:8px;text-align:right;padding:6px 10px;margin:4px 0 8px}
.sel:empty::after{content:attr(data-empty);font-size:15px;color:#3c464e}
.chk{display:flex;align-items:center;gap:8px;font-size:16px;margin:0 0 8px}.chk input{width:24px;height:24px;min-height:0}
.ask{background:var(--warnbg);border-radius:8px;padding:8px;margin:0 0 8px}.ask button{min-height:44px;border-radius:8px;border:2px solid var(--warn);background:#fff;padding:4px 14px;font-weight:700}
.list{margin-top:12px;display:grid;grid-template-columns:1fr 1.6fr 1fr;gap:10px}@media(max-width:980px){.list{grid-template-columns:1fr}}
.list .box h2{font-size:17px}
.lr{display:flex;gap:8px;padding:6px 0;border-bottom:1px solid #e1e7eb;font-size:15px}.lr:last-child{border-bottom:0}
.lr .n{font-family:ui-monospace,Consolas,monospace;font-weight:700;color:var(--accent);min-width:52px}.lr .t{flex:1;min-width:0}.lr .m{color:#3c464e;font-size:14px;white-space:nowrap}
.miss{background:var(--warnbg);border-radius:8px;padding:6px 10px;margin:0 0 8px;font-size:15px}
.sm{font-size:15px;color:#3c464e}
.fx{display:block;margin-top:3px}.fxb{min-height:30px;border-radius:7px;border:1px solid var(--line);background:#fff;padding:2px 8px;font-size:13px;margin-left:4px;cursor:pointer}
.fxf{flex-basis:100%;background:var(--warnbg);border-radius:8px;padding:6px 8px;margin-top:6px;font-size:14px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.fxf input{min-height:36px;font-size:15px;padding:2px 6px;border:1px solid var(--line);border-radius:6px}.fxf button{min-height:36px;border-radius:7px;border:2px solid var(--warn);background:#fff;padding:2px 12px;font-weight:700}.lr{flex-wrap:wrap}
</style></head><body>
<header class="top"><a href="/finance/slips" id="back">&larr; Menu</a><h1 id="ttl">Parchi desk</h1>
<select id="day" aria-label="day"></select><button class="undo" id="undo" hidden></button></header>
<main><div id="msg" aria-live="polite"></div><div id="missing"></div>
<div class="cols">
 <section class="box" id="b-opd"><h2><span data-t="opd">OPD parchi</span><small id="opdn"></small></h2>
  <label class="f"><span data-t="no">Parchi no.</span><input id="opd_no" class="no" inputmode="numeric" autocomplete="off"></label>
  <label class="f"><span data-t="cid">Clinic ID</span><input id="opd_id" inputmode="numeric" autocomplete="off"></label>
  <div class="name" id="opd_name"></div>
  <label class="chk"><input type="checkbox" id="opd_noid"> <span data-t="noid">ID nahi hai — naam likhein</span></label>
  <label class="f" id="opd_nmw" hidden><span data-t="nm">Naam</span><input id="opd_nm" autocomplete="off" maxlength="60"></label>
  <div id="opd_ask"></div>
  <button class="go" id="opd_go" data-t="save_opd">Save (Enter)</button>
 </section>
 <section class="box" id="b-xp"><h2><span data-t="xp">X-ray / Proc parchi</span><small id="xpn"></small></h2>
  <label class="f"><span data-t="no">Parchi no.</span><input id="xp_no" class="no" inputmode="numeric" autocomplete="off"></label>
  <div class="who" data-t="pick_pat">Mareez chunein (aaj ke OPD):</div>
  <div class="chips" id="xp_chips" data-empty=""></div>
  <label class="f"><span data-t="or_id">ya clinic ID</span><input id="xp_id" inputmode="numeric" autocomplete="off"></label>
  <div class="name" id="xp_name"></div>
  <div class="kinds"><button data-k="all" class="on" data-t="all">Sab</button><button data-k="xray">X-ray</button><button data-k="proc" data-t="proc">Procedure</button></div>
  <input id="q" autocomplete="off" placeholder="khojein: knee, slab, ILI…">
  <div class="tiles" id="tiles"></div>
  <div class="sel" id="sel" data-empty=""></div>
  <div class="tot" id="tot" hidden></div>
  <div id="xp_ask"></div>
  <button class="go" id="xp_go" data-t="save_xp">Save X-ray / Proc</button>
 </section>
 <section class="box" id="b-bl"><h2><span data-t="blood">Blood test</span><small id="bln"></small></h2>
  <div class="who" data-t="pick_pat">Mareez chunein (aaj ke OPD):</div>
  <div class="chips" id="bl_chips" data-empty=""></div>
  <label class="f"><span data-t="or_id">ya clinic ID</span><input id="bl_id" inputmode="numeric" autocomplete="off"></label>
  <div class="name" id="bl_name"></div>
  <button class="go" id="bl_go" data-t="save_bl">Save blood test</button>
 </section>
</div>
<div class="list">
 <section class="box"><h2><span data-t="l_opd">OPD</span><small id="lo_n"></small></h2><div id="lo"></div></section>
 <section class="box"><h2><span data-t="l_xp">X-ray / Proc</span><small id="lx_n"></small></h2><div id="lx"></div></section>
 <section class="box"><h2><span data-t="l_bl">Blood test</span><small id="lb_n"></small></h2><div id="lb"></div></section>
</div>
<p class="sm" id="foot"></p>
</main>
<script>
(function(){
var B=__BOOT__;var S=B.state,EN=B.eng;
var T={opd:["OPD parchi","OPD parchi"],no:["Parchi no.","Parchi no."],cid:["Clinic ID","Clinic ID"],noid:["ID nahi hai — naam likhein","No clinic ID — write the name"],
nm:["Naam","Name"],save_opd:["Save (Enter)","Save (Enter)"],xp:["X-ray / Proc parchi","X-ray / Proc parchi"],pick_pat:["Mareez chunein (aaj ke OPD):","Tap the patient (today's OPD):"],
or_id:["ya clinic ID","or the clinic ID"],all:["Sab","All"],proc:["Procedure","Procedure"],save_xp:["Save X-ray / Proc","Save X-ray / Proc"],blood:["Blood test","Blood test"],
save_bl:["Save blood test","Save blood test"],l_opd:["OPD","OPD"],l_xp:["X-ray / Proc","X-ray / Proc"],l_bl:["Blood test","Blood test"]};
function t(k){return (T[k]||[k,k])[EN?1:0];}
var W={known:["purana mareez","known patient"],newp:["naya mareez — naam raat ko Docterz se","new patient — the name comes from Docterz tonight"],
far:["ID bahut aage hai — dobara dekhein","this ID is far ahead — check it"],unknown:["yeh ID master mein nahi","this ID is not in the master"],
none:["abhi koi nahi","none yet"],nochips:["aaj abhi koi OPD parchi nahi","no OPD parchi yet today"],nosel:["tile dabakar X-ray / procedure chunein","tap a tile to add an X-ray or procedure"],
dup:["is parchi par do baar hai.","is on this parchi twice."],keep:["Dono rakhein","Keep both"],rem:["Yeh wali hatao","Remove this one"],tot:["Kul ","Total "],
chhoot:["Chhoot","Discount"],free:["Free","Free"],why:["wajah:","reason:"],undo:["Wapas: ","Undo: "],idok:["ID sahi hai","The ID is right"],
gapok:["Haan, yahi number","Yes, this number"],renum:["No.","No."],hatao:["Hatao","Remove"],newno:["Naya number","New number"],fixwhy:["wajah (zaroori)","reason (required)"],theek:["Theek","OK"],rehne:["Rehne do","Cancel"],miss:["Chhoote number (Aaj ki list mein batayein): ","Skipped numbers (answer them in today's list): "],
saving:["Save ho raha hai…","Saving…"],side:["side:","side:"],foot:["Paid / Done ki tick ab nahi: paise raat ko Docterz se aate hain, bill hua to kaam hua. Purane page menu mein hain.","No Paid / Done ticks: payment comes from Docterz at night, and billed means done. The old pages stay in the menu."]};
function w(k){return (W[k]||[k,k])[EN?1:0];}
document.querySelectorAll('[data-t]').forEach(function(e){e.textContent=t(e.getAttribute('data-t'));});
document.getElementById('xp_chips').setAttribute('data-empty',w('nochips'));document.getElementById('bl_chips').setAttribute('data-empty',w('nochips'));
document.getElementById('sel').setAttribute('data-empty',w('nosel'));document.getElementById('foot').textContent=w('foot');
if(EN){document.getElementById('q').placeholder='search: knee, slab, ILI…';}
function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function rs(p){return '₹'+Math.round((p||0)/100).toLocaleString('en-IN');}
var day=S.day;
var ds=$('day');B.days.forEach(function(d){var o=document.createElement('option');o.value=d[0];o.textContent=d[1];if(d[0]===day)o.selected=true;ds.appendChild(o);});
ds.addEventListener('change',function(){day=ds.value;refresh(true);});
function msg(ok,text){var m=$('msg');m.innerHTML='<div class="'+(ok?'ok':'bad')+'">'+esc(text)+'</div>';clearTimeout(msg._t);msg._t=setTimeout(function(){m.innerHTML='';},ok?6000:15000);}
function api(path,body){var o=body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'same-origin'}:{credentials:'same-origin'};
 return fetch(path,o).then(function(r){return r.json().catch(function(){return {ok:false,err:'HTTP '+r.status};});}).catch(function(e){return {ok:false,err:String(e)};});}
// ---------------- the day's state
var seenOpd={};var first=true;
function draw(st){S=st;var opdTouched=document.activeElement===$('opd_no');
 if(!$('opd_no')._typed)$('opd_no').value=st.nx_opd||'';if(!$('xp_no')._typed)$('xp_no').value=st.nx_xp||'';
 $('opdn').textContent=(EN?'next ':'agla ')+(st.nx_opd||'—');$('xpn').textContent=(EN?'next ':'agla ')+(st.nx_xp||'—');
 var got={};st.blood.forEach(function(b){got[b.cid]=1;});
 var ids=[],seen={};st.opd.slice().reverse().forEach(function(o){if(o.cid&&!seen[o.cid]){seen[o.cid]=1;ids.push(o);}});
 function chips(el,which){el.innerHTML='';ids.forEach(function(o){if(which==='bl'&&got[o.cid])return;var b=document.createElement('button');b.type='button';b.className='chip'+(!first&&!seenOpd[o.cid]?' fresh':'')+(pick[which]===o.cid?' on':'');
  b.textContent=(pick[which]===o.cid?'\u2713 ':'')+o.cid+(o.name?' · '+o.name:(o.new?(EN?' · new':' · naya'):''));b.addEventListener('click',function(){setPick(which,o.cid,o.name);});el.appendChild(b);});}
 chips($('xp_chips'),'xp');chips($('bl_chips'),'bl');
 ids.forEach(function(o){seenOpd[o.cid]=1;});first=false;
 function rows(el,arr,fn,n){el.innerHTML=arr.length?arr.slice().reverse().map(fn).join(''):'<p class="sm">'+w('none')+'</p>';$(n).textContent=arr.length;}
 function fx(o){return '<span class="fx"><button type="button" class="fxb" data-fx="renum" data-id="'+o.id+'" data-no="'+o.no+'">'+w('renum')+'</button><button type="button" class="fxb" data-fx="hatao" data-id="'+o.id+'" data-no="'+o.no+'">'+w('hatao')+'</button></span>';}
 rows($('lo'),st.opd,function(o){return '<div class="lr" data-sid="'+o.id+'"><span class="n">'+o.no+'</span><span class="t">'+esc(o.cid||'')+' '+esc(o.name||'')+(o.new?' <b>'+(EN?'new':'naya')+'</b>':'')+'</span><span class="m">'+esc(o.by)+' '+esc(o.at)+fx(o)+'</span></div>';},'lo_n');
 rows($('lx'),st.xp,function(o){return '<div class="lr" data-sid="'+o.id+'"><span class="n">'+o.no+'</span><span class="t">'+esc(o.cid||'')+' '+esc(o.name||'')+'<br><span class="sm">'+o.items.map(function(i){return esc(i.n+(i.side?' '+i.side:''))+(i.d?' (chhoot '+rs(i.d)+')':'');}).join(' · ')+'</span></span><span class="m">'+rs(o.total)+'<br>'+esc(o.by)+' '+esc(o.at)+fx(o)+'</span></div>';},'lx_n');
 /* S654 (D789): No. / Hatao on a saved parchi of the day shown -- a small form in the row, Theek sends it */
 document.querySelectorAll('.fxb').forEach(function(b){b.addEventListener('click',function(){var row=b.closest('.lr');if(!row||row.querySelector('.fxf'))return;
  var kind=b.getAttribute('data-fx'),id=b.getAttribute('data-id'),no=b.getAttribute('data-no');var f=document.createElement('div');f.className='fxf';
  f.innerHTML=(kind==='renum'?'<label>'+w('newno')+' <input class="fxno" inputmode="numeric" value="'+esc(no)+'" style="width:6em"></label> ':'')+'<label>'+w('fixwhy')+' <input class="fxwhy" maxlength="120" style="width:12em"></label> <button type="button" class="fxok">'+w('theek')+'</button> <button type="button" class="fxno2">'+w('rehne')+'</button>';
  row.appendChild(f);(f.querySelector('.fxno')||f.querySelector('.fxwhy')).focus();
  f.querySelector('.fxno2').addEventListener('click',function(){f.remove();});
  f.querySelector('.fxok').addEventListener('click',function(){var body={id:Number(id),day:day,why:f.querySelector('.fxwhy').value.trim()};if(kind==='renum')body.no=f.querySelector('.fxno').value.trim();
   f.querySelector('.fxok').disabled=true;api(kind==='renum'?'/finance/slips/desk/api/renumber':'/finance/slips/desk/api/void',body).then(function(r){msg(!!r.ok,r.ok?r.msg:r.err);if(r.state)draw(r.state);else f.querySelector('.fxok').disabled=false;});});
 });});
 rows($('lb'),st.blood,function(o){return '<div class="lr"><span class="n">'+esc(o.cid)+'</span><span class="t">'+esc(o.name||'')+'</span><span class="m">'+esc(o.by)+' '+esc(o.at)+'</span></div>';},'lb_n');
 $('missing').innerHTML=st.missing.length?'<div class="miss">'+w('miss')+st.missing.slice(0,6).map(function(m){return (m.series==='opd'?'OPD ':'XP ')+m.no;}).join(', ')+(st.missing.length>6?' +'+(st.missing.length-6):'')+' — <a href="/finance/slips?s=list">'+(EN?"today's list":'Aaj ki list')+'</a></div>':'';
 var u=$('undo');if(st.last&&st.day===st.today){u.hidden=false;u.textContent=w('undo')+st.last.label;}else{u.hidden=true;}
 $('bl_go').disabled=(day!==st.today);
}
function refresh(force){return api('/finance/slips/desk/api/state?day='+encodeURIComponent(day)).then(function(r){if(r.ok)draw(r.state);});}
setInterval(function(){if(!document.hidden)refresh();},(B.poll||8)*1000);
document.addEventListener('visibilitychange',function(){if(!document.hidden)refresh();});
// ---------------- the patient lookups
var pick={xp:'',bl:''};
function look(inp,out,cb){var v=inp.value.trim();if(!v){out.textContent='';out.className='name';cb&&cb(null);return;}
 api('/finance/slips/desk/api/patient?id='+encodeURIComponent(v)+'&day='+encodeURIComponent(day)).then(function(r){if(inp.value.trim()!==v)return;
  if(!r.ok){out.textContent='';out.className='name';cb&&cb(null);return;}
  if(r.known){out.textContent=r.name+' — '+w('known')+(r.new?' ('+(EN?'new ID':'naya ID')+')':'');out.className='name known';}
  else if(r.far){out.textContent=w('far');out.className='name far';}
  else if(r.new){out.textContent=w('newp');out.className='name new';}else{out.textContent=w('unknown');out.className='name new';}
  cb&&cb(r);});}
function deb(fn){var h;return function(){clearTimeout(h);h=setTimeout(fn,250);};}
$('opd_id').addEventListener('input',deb(function(){look($('opd_id'),$('opd_name'));}));
['opd_id','opd_no','opd_nm'].forEach(function(i){$(i).addEventListener('input',function(){$('opd_ask').innerHTML='';});});
['xp_id','xp_no'].forEach(function(i){$(i).addEventListener('input',function(){$('xp_ask').innerHTML='';});});
$('xp_id').addEventListener('input',deb(function(){pick.xp=$('xp_id').value.trim();draw(S);look($('xp_id'),$('xp_name'));}));
$('bl_id').addEventListener('input',deb(function(){pick.bl=$('bl_id').value.trim();draw(S);look($('bl_id'),$('bl_name'));}));
function setPick(which,cid,name){pick[which]=cid;var inp=$(which+'_id');inp.value=cid;look(inp,$(which+'_name'));draw(S);}
['opd_no','xp_no'].forEach(function(i){$(i).addEventListener('input',function(){$(i)._typed=true;});});
$('opd_noid').addEventListener('change',function(){var on=$('opd_noid').checked;$('opd_nmw').hidden=!on;$('opd_id').disabled=on;if(on)$('opd_nm').focus();});
// ---------------- OPD: Enter saves
function saveOpd(extra){var b={series:'opd',slip_no:$('opd_no').value.trim(),clinic_id:$('opd_id').value.trim(),day:day,
  noid:$('opd_noid').checked,no_id_name:$('opd_nm').value.trim()};for(var k in (extra||{}))b[k]=extra[k];
 $('opd_go').disabled=true;api('/finance/slips/desk/api/save',b).then(function(r){$('opd_go').disabled=false;
  if(r.ok){msg(true,r.msg);$('opd_id').value='';$('opd_name').textContent='';$('opd_nm').value='';$('opd_noid').checked=false;$('opd_nmw').hidden=true;$('opd_id').disabled=false;
   $('opd_no')._typed=false;$('opd_ask').innerHTML='';draw(r.state);$('opd_id').focus();}
  else{msg(false,r.err);askFor('opd_ask',r.ask,function(f){var e={};e[f]=true;saveOpd(Object.assign({},extra||{},e));});}});}
function askFor(el,ask,go){var a=$(el);a.innerHTML='';if(!ask)return;var lbl=ask==='id_ok'?w('idok'):w('gapok');
 a.innerHTML='<div class="ask"><button type="button">'+esc(lbl)+'</button></div>';a.querySelector('button').addEventListener('click',function(){go(ask);});}
$('opd_go').addEventListener('click',function(){saveOpd();});
['opd_id','opd_nm','opd_no'].forEach(function(i){$(i).addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();if(i==='opd_no'){$('opd_id').focus();return;}saveOpd();}});});
// ---------------- X-ray / Proc: tiles, side, chhoot, the duplicate warning
var kind='all',sel=[];
document.querySelectorAll('.kinds button').forEach(function(b){b.addEventListener('click',function(){kind=b.getAttribute('data-k');
 document.querySelectorAll('.kinds button').forEach(function(x){x.classList.toggle('on',x===b);});drawTiles();});});
$('q').addEventListener('input',drawTiles);
function drawTiles(){var q=$('q').value.trim().toLowerCase();var el=$('tiles');el.innerHTML='';
 B.tiles.forEach(function(s){if(kind!=='all'&&s.k!==kind)return;if(q&&s.a.indexOf(q)<0&&s.n.toLowerCase().indexOf(q)<0)return;
  var b=document.createElement('button');b.type='button';b.className='tile'+(s.k==='proc'?' proc':'');
  b.innerHTML=esc(s.n)+'<em>'+(s.p?rs(s.p):(EN?'no rate':'rate nahi'))+'</em>';b.addEventListener('click',function(){add(s);});el.appendChild(b);});}
function add(s){var it={id:s.id,k:s.k,n:s.n,p:s.p,ask:!!s.s,side:'',disc:'',free:false,why:'',open:false,dup:false};
 var same=sel.some(function(x){return x.id===s.id;});if(same)it.dup=true;sel.push(it);drawSel();}
function sameKey(x){return x.id+'|'+x.side;}
function drawSel(){var el=$('sel');el.innerHTML='';var tot=0;
 var counts={};sel.forEach(function(x){counts[sameKey(x)]=(counts[sameKey(x)]||0)+1;});
 sel.forEach(function(x,ix){var net=Math.max(0,x.p-(x.free?x.p:(parseInt(x.disc,10)||0)*100));tot+=net;
  var d=document.createElement('div');d.className='it'+(x.dup?' dup':'');
  var h='<div class="row1"><span class="nm">'+esc(x.n)+(x.side?' <b>'+x.side+'</b>':'')+'</span><span class="pr">'+(x.p?rs(net):(EN?'no rate':'rate nahi'))+'</span><button type="button" class="x" data-a="rm">&times;</button></div>';
  if(x.ask)h+='<div class="sd">'+['R','L','B'].map(function(sd){return '<button type="button" data-a="side" data-v="'+sd+'" class="'+(x.side===sd?'on':'')+'">'+sd+'</button>';}).join('')+'</div>';
  if(x.p){if(!x.open&&!x.free&&!x.disc)h+='<div class="ch"><button type="button" class="cb" data-a="open">'+w('chhoot')+'</button></div>';
   else{h+='<div class="ch"><input inputmode="numeric" data-a="disc" placeholder="'+(EN?'Rs':'Rs')+'" value="'+esc(x.disc)+'"'+(x.free?' disabled':'')+'><button type="button" data-a="free" class="'+(x.free?'on':'')+'">'+w('free')+'</button></div>'+
    '<div class="ch"><span class="sm">'+w('why')+'</span>'+B.reasons.map(function(r){return '<button type="button" data-a="why" data-v="'+r.k+'" class="'+(x.why===r.k?'on':'')+'">'+esc(EN?r.en:r.hi)+'</button>';}).join('')+'</div>';}}
  if(x.dup)h+='<div class="dupw">'+esc(x.n+(x.side?' '+x.side:''))+' '+w('dup')+'<br><button type="button" data-a="keep">'+w('keep')+'</button><button type="button" data-a="rm">'+w('rem')+'</button></div>';
  d.innerHTML=h;
  d.addEventListener('click',function(e){var a=e.target.getAttribute('data-a');if(!a)return;
   if(a==='rm'){sel.splice(ix,1);}else if(a==='keep'){x.dup=false;}else if(a==='side'){x.side=e.target.getAttribute('data-v');
    x.dup=sel.some(function(y,iy){return iy!==ix&&sameKey(y)===sameKey(x);});}
   else if(a==='open'){x.open=true;}else if(a==='free'){x.free=!x.free;if(x.free)x.disc='';}else if(a==='why'){x.why=e.target.getAttribute('data-v');}else{return;}
   drawSel();});
  var di=d.querySelector('input[data-a="disc"]');if(di)di.addEventListener('input',function(){x.disc=di.value.replace(/[^0-9]/g,'');var tt=0;sel.forEach(function(y){tt+=Math.max(0,y.p-(y.free?y.p:(parseInt(y.disc,10)||0)*100));});$('tot').textContent=w('tot')+rs(tt);});
  el.appendChild(d);});
 $('tot').hidden=!sel.length;$('tot').textContent=w('tot')+rs(tot);}
function saveXp(extra){if(sel.some(function(x){return x.dup;})){msg(false,w('dup'));return;}
 var b={series:'xp',slip_no:$('xp_no').value.trim(),clinic_id:$('xp_id').value.trim(),day:day,
  items:sel.map(function(x){return {id:x.id,k:x.k,side:x.side,disc:x.free?'':x.disc,free:x.free,why:x.why};})};
 for(var k in (extra||{}))b[k]=extra[k];
 $('xp_go').disabled=true;api('/finance/slips/desk/api/save',b).then(function(r){$('xp_go').disabled=false;
  if(r.ok){msg(true,r.msg);sel=[];drawSel();$('xp_id').value='';$('xp_name').textContent='';pick.xp='';$('xp_no')._typed=false;$('xp_ask').innerHTML='';$('q').value='';drawTiles();draw(r.state);}
  else{msg(false,r.err);askFor('xp_ask',r.ask,function(f){var e={};e[f]=true;saveXp(Object.assign({},extra||{},e));});}});}
$('xp_go').addEventListener('click',function(){saveXp();});
// ---------------- Blood
$('bl_go').addEventListener('click',function(){var cid=$('bl_id').value.trim();$('bl_go').disabled=true;
 api('/finance/slips/desk/api/blood',{clinic_id:cid}).then(function(r){$('bl_go').disabled=false;if(r.ok){msg(true,r.msg);$('bl_id').value='';$('bl_name').textContent='';pick.bl='';draw(r.state);}else msg(false,r.err);});});
// ---------------- Undo
$('undo').addEventListener('click',function(){if(!S.last)return;api('/finance/slips/desk/api/undo',{kind:S.last.kind,id:S.last.id}).then(function(r){msg(!!r.ok,r.ok?r.msg:r.err);if(r.state)draw(r.state);});});
drawTiles();drawSel();draw(S);$('opd_id').focus();
})();
</script></body></html>"""
