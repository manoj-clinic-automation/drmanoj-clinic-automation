#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clinic_papers.py -- S464_CLINIC_PAPERS (D664, the owner 03-Oct-2026), slice 1 of 3.

THE OWNER'S RULING
    Papers scanned at reception that are not pharmacy purchases need their own home. CLINIC CONSUMABLES is the main
    group, with three sub-groups: Procedure room, X-ray films (two sizes) and Others (stationery and the rest). The
    sub-group is OPTIONAL at scanning; Shavez or he sets it later, and it must be easy: the system suggests it from
    the supplier AND the items, one tap to confirm or skip. The supplier alone never decides -- Yuvika sells orthotics
    to the pharmacy on printed bills and procedure-room goods on handwritten slips. Goods like the inverter battery
    belong to the "Dr MK expense" lane.

WHAT THIS FILE IS
    A part of the asset app (asset_register.py), mounted by one guarded import at its foot: if this file cannot load,
    the asset app runs exactly as before. It adds ONE column, bills.subgroup, and four addresses:
        GET  /papers               the papers to sort, each with a suggestion: Yes / Change / Skip
        GET  /papers/<id>          one paper and its group
        POST /bills/<id>/subgroup  set or clear the group (audited)
        GET  /papers/month         clinic consumables for a month, by group
    Owner and manager only (the asset app's own checker_required). Staff are asked nothing new and see nothing new.

WHAT IT DELIBERATELY DOES NOT DO
    It adds no lane, changes no lane's meaning and never touches a pharmacy scan: a move between lanes goes through
    the asset app's own /bills/<id>/lane, with its rules and its audit line. A suggestion is worked out when the page
    is shown and stored nowhere; nothing is sorted until a person taps. Standard library and Flask only.
"""
import datetime
import re
import sqlite3

from flask import abort, flash, redirect, request, url_for

VERSION = "S464.1"
AR = None                     # the asset app's module, handed in by init()

SUB = {                       # what bills.subgroup may hold, and its words on a page
    "procedure":  "Procedure room",
    "xray":       "X-ray films",
    "xray_small": "X-ray films · small film",
    "xray_11x14": "X-ray films · 11 x 14",
    "others":     "Others",
}
GROUP_OF = {"procedure": "procedure", "xray": "xray", "xray_small": "xray", "xray_11x14": "xray", "others": "others"}
GROUPS = (("procedure", "Procedure room", "fibre cast, roller bandage, cotton, tape, betadine"),
          ("xray", "X-ray films", "small film or 11 x 14"),
          ("others", "Others", "stationery and the rest"))

# The words a suggestion is made from. Each list can be lengthened from the app's settings table without a new kit:
# key d664.words.<name>, a comma-separated list (added to these, never replacing them).
WORDS = {
    "expense":   ["battery", "batteries", "inverter", "invertor", "ups", "exide", "luminous", "amaron", "okaya",
                  "microtek", "warranty card", "warranty"],
    "orthotic":  ["brace", "belt", "knee cap", "kneecap", "cervical collar", "collar", "splint", "support", "sling",
                  "walker", "crutch", "crutches", "heel cup", "insole", "corset", "immobilizer", "immobiliser",
                  "wrist binder", "ankle binder", "abdominal binder"],
    "xray":      ["x-ray", "x ray", "xray", "film", "films", "fuji", "konica", "agfa", "carestream", "developer",
                  "fixer"],
    "xray_11x14": ["11x14", "11 x 14", "11*14", "11 by 14", "14x11", "14 x 11"],
    "xray_small": ["8x10", "8 x 10", "8*10", "10x12", "10 x 12", "10*12", "small film"],
    "procedure": ["fibre cast", "fiber cast", "fibrecast", "fibercast", "cast", "plaster of paris", "plaster", "pop",
                  "roller bandage", "bandage", "bandages", "cotton", "zigzag", "zig zag", "gauze", "gamjee",
                  "tape", "micropore", "leukoplast", "betadine", "povidone", "scrub", "lignocaine", "xylocaine",
                  "lox", "syringe", "syringes", "needle", "needles", "gloves", "glove", "spirit", "savlon",
                  "dressing", "crepe", "soft roll", "softroll", "stockinette", "stockinet"],
    "stationery": ["stationery", "stationary", "a4", "paper", "pen", "pens", "register", "file", "files", "folder",
                   "stapler", "staples", "toner", "cartridge", "ink", "envelope", "envelopes", "stamp pad",
                   "letterhead", "letter head", "prescription pad", "visiting card", "printing"],
    "procedure_supplier": ["agarwal surg", "agrawal surg", "aggarwal surg", "yuvika"],
}
PAGE_N = 30


# ---------------------------------------------------------------------------------------------- the database's part
def ensure(db):
    """ONE additive column, idempotent. Two workers start at once, so 'duplicate column' from the second is normal."""
    cols = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
    if "subgroup" not in cols:
        try:
            db.execute("ALTER TABLE bills ADD COLUMN subgroup TEXT")
        except sqlite3.OperationalError as ex:
            if "duplicate column" not in str(ex).lower():
                raise
        db.commit()


def _cols(db):
    return {r[1] for r in db.execute("PRAGMA table_info(bills)")}


def _live(db, alias="b"):
    """The papers that count: on the clinic lane, not rejected, not a duplicate, not a page joined into another."""
    w = ("COALESCE(%s.lane,'clinic')='clinic' AND %s.status IN ('draft','approved') AND %s.dup_of IS NULL"
         % (alias, alias, alias))
    if "page_of" in _cols(db):
        w += " AND %s.page_of IS NULL" % alias
    return w


def _words(db, name):
    out = list(WORDS[name])
    try:
        r = db.execute("SELECT value FROM settings WHERE key=?", ("d664.words." + name,)).fetchone()
        if r and r[0]:
            out += [w.strip().lower() for w in str(r[0]).split(",") if w.strip()]
    except sqlite3.Error:
        pass
    return out


def _hits(text, words):
    """The words of the list that stand in the text as whole words (so 'cast' never matches 'broadcast')."""
    got = []
    for w in words:
        if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", text) and w not in got:
            got.append(w)
    return [w for w in got if not any(w != x and w in x for x in got)]      # 'cast' is not said beside 'fibre cast'


# ---------------------------------------------------------------------------------------------- the suggestion
def suggest(db, vendor, items, has_bill_no, has_total):
    """What this paper looks like, from the supplier AND the words read on it.
    -> dict(kind='sub', value=<subgroup>, label, why)   a clinic sub-group, one tap to confirm
       dict(kind='lane', value='owner_expense', label, why)   not a clinic consumable at all
       dict(kind='note', why)                           something worth saying, nothing to tap
       None                                             nothing to suggest -- the person chooses"""
    v = re.sub(r"\s+", " ", (vendor or "").lower()).strip()
    t = re.sub(r"\s+", " ", (items or "").lower()).strip()
    both = (v + " " + t).strip()
    ex = _hits(both, _words(db, "expense"))
    if ex:
        return dict(kind="lane", value="owner_expense", label="Dr MK expense",
                    why="the words read on it: " + ", ".join(ex[:3]))
    orth = _hits(t, _words(db, "orthotic"))
    xr = _hits(t, _words(db, "xray"))
    pr = _hits(t, _words(db, "procedure"))
    st = _hits(t, _words(db, "stationery"))
    if xr and len(xr) >= len(pr):
        size = ("xray_11x14" if _hits(t, _words(db, "xray_11x14")) else
                "xray_small" if _hits(t, _words(db, "xray_small")) else "xray")
        return dict(kind="sub", value=size, label=SUB[size], why="the words read on it: " + ", ".join(xr[:3]))
    if pr and len(pr) >= len(orth):
        return dict(kind="sub", value="procedure", label=SUB["procedure"],
                    why="the words read on it: " + ", ".join(pr[:3]))
    if orth:
        return dict(kind="note", why="the words read on it (%s) look like orthotics — a pharmacy purchase; "
                                     "open it to move it, if so" % ", ".join(orth[:3]))
    if st:
        return dict(kind="sub", value="others", label=SUB["others"], why="the words read on it: " + ", ".join(st[:3]))
    sup = _hits(v, _words(db, "procedure_supplier"))
    if sup and not t:
        if not has_bill_no and not has_total:
            return dict(kind="sub", value="procedure", label=SUB["procedure"],
                        why="the supplier, and nothing else could be read — this supplier's handwritten slips "
                            "are procedure-room goods")
        return dict(kind="sub", value="procedure", label=SUB["procedure"],
                    why="the supplier (no item could be read — look at the paper before saying yes)")
    return None


def _items_text(db, bid):
    return " ; ".join(r[0] for r in db.execute(
        "SELECT item_name FROM bill_items WHERE bill_id=? ORDER BY id", (bid,)) if r[0])


def _paper(db, b):
    """One row for a page: the bill, what was read, and the suggestion."""
    items = _items_text(db, b["id"])
    read_nothing = not (b["bill_no"] or b["total_amount"] is not None or items)
    reading = (b["ocr_status"] or "") == "reading"
    s = None if reading else suggest(db, b["vendor"], items, bool(b["bill_no"]), b["total_amount"] is not None)
    if s and s["kind"] == "lane" and b["status"] == "approved":
        s = dict(kind="note", why="it looks like Dr MK expense (%s), but it is already approved on the clinic lane, "
                                  "so it stays there — give it a group" % s["why"])
    return dict(b=b, words=items, read_nothing=read_nothing, reading=reading, s=s,      # never a key named "items": a page would get the dict's own method
                stamp=b["stamp_no"] or ("#%d" % b["id"]), group=(b["subgroup"] or ""))


def _inr(x):
    """12,34,567.00 -- the Indian grouping, as the owner reads money."""
    if x is None:
        return "—"
    neg = x < 0
    whole, frac = ("%.2f" % abs(x)).split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return ("-" if neg else "") + "₹" + whole + "." + frac


# ---------------------------------------------------------------------------------------------- for the app's own pages
def group_label(b):
    """For the bill page: the group's words, or '' when none is set. Never raises."""
    try:
        return SUB.get((b["subgroup"] or "") if "subgroup" in b.keys() else "", "")
    except Exception:                                                # noqa: BLE001
        return ""


def to_sort_count():
    """For the Purchases page: how many clinic papers have no group yet. Never raises."""
    try:
        db = AR.get_db()
        return db.execute("SELECT COUNT(*) FROM bills b WHERE " + _live(db) + " AND COALESCE(b.subgroup,'')=''"
                          ).fetchone()[0]
    except Exception:                                                # noqa: BLE001
        return 0


# ---------------------------------------------------------------------------------------------- the pages
CSS = """<style>
.d6{max-width:640px;margin:0 auto}
.d6 .lead{color:#5a6b7b;font-size:14px;margin:0 0 12px}
.d6 .muted{color:#5a6b7b}
.d6card{background:#fff;border:1px solid #d5dce8;border-radius:12px;padding:14px;margin:0 0 14px;box-shadow:0 1px 3px rgba(20,40,70,.06)}
.d6top{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.d6top b{font-size:16px}
.d6row{display:flex;gap:12px;align-items:flex-start}
.d6row img{width:64px;height:84px;object-fit:cover;border-radius:6px;background:#dfe6f1;flex:none}
.d6say{background:#eef4ff;border-radius:8px;padding:10px;font-size:14px;margin:10px 0}
.d6say.other{background:#fff4e0;color:#5b3a06}
.d6say.none{background:#f2f5f9;color:#5a6b7b}
.d6btns{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.d6btns form{display:inline;margin:0}
.d6b{min-height:44px;padding:0 14px;border-radius:8px;font-size:15px;font-weight:600;font-family:inherit;display:inline-flex;align-items:center;text-decoration:none;cursor:pointer;box-sizing:border-box}
.d6b.yes{background:#3a5a78;color:#fff;border:0}
.d6b.alt{background:#fff;color:#1f3864;border:1px solid #1f3864}
.d6b.skip{background:#fff;color:#5a6b7b;border:1px solid #b7c2d4}
.d6opt{display:block;width:100%;max-width:none;text-align:left;min-height:52px;padding:8px 14px;margin:0 0 8px;border:1px solid #b7c2d4;border-radius:10px;background:#fff;color:#2d3742;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;box-sizing:border-box}
.d6opt.on{border:2px solid #3a5a78;background:#eef4ff}
.d6opt small{display:block;font-weight:400;color:#5a6b7b;font-size:13px}
.d6x summary{list-style:none}.d6x summary::-webkit-details-marker{display:none}
.d6x[open] summary{margin-bottom:6px}
.d6x .in{padding:0 0 4px 16px;display:flex;gap:8px;flex-wrap:wrap}
.d6t{border-radius:0}.d6t td,.d6t th{font-size:14px;border-left:0;border-right:0}.d6t tr:first-child td{border-top:0}.d6t tr:last-child td{border-bottom:0}
.d6line{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-top:1px solid #eef1f5}
.d6mini{display:inline-flex;align-items:center;min-height:36px;padding:0 10px;margin-top:4px;border:1px solid #b7c2d4;border-radius:8px;font-size:14px;text-decoration:none}
.nw{white-space:nowrap}
.d6t td.r,.d6t th.r{text-align:right;white-space:nowrap}
.d6t tr.sub td{color:#5a6b7b;padding-left:26px}
.d6nav{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:0 0 10px}
</style>"""

PAPERS_TPL = CSS + """<div class=d6><h2>Clinic papers to sort{% if total %} <span class="badge amber">{{total}} paper{{'' if total==1 else 's'}}</span>{% endif %}</h2>
<p class=lead>For you or Shavez. Staff are asked nothing new when they scan.
 &nbsp;<a href="{{url_for('d664_month')}}">This month by group →</a></p>
{% for p in papers %}<div class=d6card>
<div class=d6row><a href="{{url_for('bill_view',bid=p.b['id'])}}">{% if p.b['source_stored'] %}<img loading=lazy alt="the scanned paper" src="{{url_for('bill_thumb',bid=p.b['id'])}}">{% endif %}</a>
<div style="flex:1;min-width:0"><div class=d6top><b><a href="{{url_for('bill_view',bid=p.b['id'])}}" style="text-decoration:none">{{p.stamp}}</a> · {{p.b['vendor'] or 'supplier not read'}}</b>
<span>{% if p.b['total_amount'] is not none %}<b>{{inr(p.b['total_amount'])}}</b>{% else %}<span class=muted>amount not read</span>{% endif %}</span></div>
<div class=muted style="font-size:13px">{% if p.reading %}still being read — a suggestion follows in a minute{% elif p.read_nothing %}No bill number, amount or item could be read.{% else %}{% if p.b['bill_date'] %}Bill dated {{p.b['bill_date']}}{% else %}no date read{% endif %}{% if p.b['bill_no'] %} · no. {{p.b['bill_no']}}{% endif %}{% if p.words %} · {{p.words[:90]}}{% endif %}{% endif %}</div></div></div>
{% if p.s and p.s.kind=='sub' %}<div class=d6say>Looks like <b>Clinic consumables · {{p.s.label}}</b> — from {{p.s.why}}.{% if p.s.value=='xray' %} Which film?{% endif %}</div>
{% elif p.s and p.s.kind=='lane' %}<div class="d6say other">Looks like <b>{{p.s.label}}</b>, not a clinic consumable — from {{p.s.why}}.</div>
{% elif p.s %}<div class="d6say other">{{p.s.why[0]|upper}}{{p.s.why[1:]}}.</div>
{% elif not p.reading %}<div class="d6say none">No suggestion — nothing on it names a group.</div>{% endif %}
<div class=d6btns>
{% if p.s and p.s.kind=='sub' and p.s.value!='xray' %}<form method=post action="{{url_for('d664_set',bid=p.b['id'])}}"><input type=hidden name=back value="{{url_for('d664_papers')}}"><button class="d6b yes" name=subgroup value="{{p.s.value}}">Yes, {{p.s.label}}</button></form>
{% elif p.s and p.s.kind=='sub' %}<form method=post action="{{url_for('d664_set',bid=p.b['id'])}}"><input type=hidden name=back value="{{url_for('d664_papers')}}"><button class="d6b yes" name=subgroup value="xray_small">X-ray · small film</button> <button class="d6b yes" name=subgroup value="xray_11x14">X-ray · 11 x 14</button></form>
{% elif p.s and p.s.kind=='lane' %}<form method=post action="{{url_for('bill_lane',bid=p.b['id'])}}"><input type=hidden name=back value="{{url_for('d664_papers')}}"><button class="d6b yes" name=lane value="{{p.s.value}}">Move to {{p.s.label}}</button></form>{% endif %}
<a class="d6b alt" href="{{url_for('d664_paper',bid=p.b['id'])}}">{{'Change' if (p.s and p.s.kind!='note') else 'Open it'}}</a>
<button type=button class="d6b skip" onclick="this.closest('.d6card').style.display='none'">Skip</button></div></div>
{% endfor %}
{% if not papers %}<div class=d6card><b>Nothing to sort.</b><br><span class=muted>Every clinic paper has its group.</span></div>{% endif %}
{% if more %}<p class=muted>Showing the newest {{papers|length}} of {{total}}. Sort these and the older ones follow.</p>{% endif %}
<p class=muted>Skip leaves the paper here for later. Nothing is lost by not sorting: an unsorted paper still counts under Clinic consumables.</p></div>"""

PAPER_TPL = CSS + """<div class=d6><h2>{{p.stamp}} <span class=muted>{{p.b['vendor'] or 'supplier not read'}}</span></h2>
<p class=lead>Lane: {{lanes[p.b['lane'] or 'clinic'][0]}}{% if p.b['total_amount'] is not none %} · {{inr(p.b['total_amount'])}}{% endif %}{% if p.b['bill_date'] %} · {{p.b['bill_date']}}{% endif %}
 · <a href="{{url_for('bill_view',bid=p.b['id'])}}">open the bill</a></p>
{% if p.b['source_stored'] %}<a href="{{url_for('bill_file',bid=p.b['id'])}}"><img alt="the scanned paper" src="{{url_for('bill_thumb',bid=p.b['id'])}}" style="display:block;max-width:100%;max-height:260px;margin:0 auto 14px;border-radius:10px;background:#dfe6f1"></a>{% endif %}
{% if on_clinic %}<div class=d6card><b style="font-size:16px">Which clinic consumable?</b>
<p class=muted style="font-size:13px;margin:4px 0 10px">One tap saves it. Optional — leave it and the paper stays under Clinic consumables, not sorted.</p>
{% if p.s and p.s.kind!='sub' %}<div class="d6say other">{% if p.s.kind=='lane' %}Looks like <b>{{p.s.label}}</b>, not a clinic consumable — from {{p.s.why}}.{% else %}{{p.s.why[0]|upper}}{{p.s.why[1:]}}.{% endif %}</div>{% endif %}
<form method=post action="{{url_for('d664_set',bid=p.b['id'])}}"><input type=hidden name=back value="{{back}}">
<button class="d6opt {{'on' if cur=='procedure'}}" name=subgroup value=procedure>Procedure room{% if sug=='procedure' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>fibre cast, roller bandage, cotton, tape, betadine</small></button>
<details class=d6x {{'open' if (cur.startswith('xray') or sug.startswith('xray'))}}><summary class="d6opt {{'on' if cur.startswith('xray')}}">X-ray films{% if sug.startswith('xray') %} <span style="font-weight:400">— suggested</span>{% endif %}<small>then one more tap: small film or 11 x 14</small></summary>
<div class=in><button class="d6b {{'yes' if cur=='xray_small' else 'alt'}}" name=subgroup value=xray_small>Small film</button>
<button class="d6b {{'yes' if cur=='xray_11x14' else 'alt'}}" name=subgroup value=xray_11x14>11 x 14</button>
<button class="d6b {{'yes' if cur=='xray' else 'skip'}}" name=subgroup value=xray>size not known</button></div></details>
<button class="d6opt {{'on' if cur=='others'}}" name=subgroup value=others>Others{% if sug=='others' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>stationery and the rest</small></button>
{% if cur %}<button class="d6b skip" name=subgroup value="">Clear the group</button>{% endif %}
<a class="d6b skip" href="{{back}}">{{'Done' if cur else 'Skip for now'}}</a></form></div>
{% else %}<div class=d6card><b>This paper is not on the clinic lane.</b><br><span class=muted>Groups belong to clinic consumables only.</span></div>{% endif %}
{% if p.b['status']!='rejected' %}<div class=d6card><b>Not a clinic consumable?</b>
<p class=muted style="font-size:13px;margin:4px 0 10px">Move it to its own lane{% if p.b['status']=='approved' %} — but this bill is approved, and an approved bill stays on the clinic lane{% endif %}.</p>
<form method=post action="{{url_for('bill_lane',bid=p.b['id'])}}" class=d6btns style="display:flex"><input type=hidden name=back value="{{back}}">
{% for k in lane_order %}{% if k!=(p.b['lane'] or 'clinic') %}<button class="d6b alt" name=lane value="{{k}}">{{lanes[k][0].split(' — ')[0]}}</button>{% endif %}{% endfor %}</form></div>{% endif %}
<p class=muted>The suggestion comes from the supplier and the words read on the paper. The supplier alone never decides: Yuvika sells orthotics to the pharmacy too.</p></div>"""

MONTH_TPL = CSS + """<div class=d6><div class=d6nav><a class="d6b alt" href="{{url_for('d664_month',ym=prev)}}">← {{label(prev)}}</a>
{% if nxt %}<a class="d6b alt" href="{{url_for('d664_month',ym=nxt)}}">{{label(nxt)}} →</a>{% else %}<span></span>{% endif %}</div>
<h2>Clinic consumables</h2>
<p class=lead>What the clinic bought in <b>{{label(ym)}}</b>, by group.</p>
{% if g %}<p><a class="d6b alt" href="{{url_for('d664_month',ym=ym)}}">← All groups</a></p>
<div class=d6card><b style="font-size:16px">{{gname}}</b>
{% for b in rows %}<div class=d6line><div style="flex:1;min-width:0"><a href="{{url_for('bill_view',bid=b['id'])}}"><b>{{b['stamp_no'] or ('#'~b['id'])}}</b></a> · {{b['vendor'] or 'supplier not read'}}
<br><span class=muted style="font-size:13px"><span class=nw>{{b['bill_date'] or 'no date read'}}</span>{% if b['subgroup'] in ('xray_small','xray_11x14') %} · <span class=nw>{{sub[b['subgroup']].split(' · ')[1]}}</span>{% endif %}{% if b['status']=='draft' %} · <span class=nw>pending approval</span>{% endif %}</span></div>
<div style="text-align:right;flex:none"><b class=nw>{{inr(b['total_amount']) if b['total_amount'] is not none else 'amount not read'}}</b><br>
<a href="{{url_for('d664_paper',bid=b['id'],back=here)}}" class=d6mini>{{'sort it' if not b['subgroup'] else 'change group'}}</a></div></div>{% endfor %}
{% if not rows %}<p class=muted>No paper in this group this month.</p>{% endif %}</div>
{% else %}<div class=d6card style="padding:2px 14px"><table class=d6t>
{% for r in table %}<tr class="{{'sub' if r.sub else ''}}"><td>{% if r.key %}<a href="{{url_for('d664_month',ym=ym,g=r.key)}}" style="text-decoration:none">{% endif %}{% if not r.sub %}<b>{{r.name}}</b>{% else %}{{r.name}}{% endif %}{% if r.key %}</a>{% endif %}
{% if not r.sub %}<br><span class=muted style="font-size:13px">{{r.n}} paper{{'' if r.n==1 else 's'}}{% if r.vendors %} · {{r.vendors}}{% endif %}{% if r.noamt %} · {{r.noamt}} with no amount read{% endif %}</span>{% endif %}</td>
<td class=r>{% if not r.sub %}<b>{{inr(r.total)}}</b>{% else %}{{inr(r.total)}}{% endif %}</td></tr>{% endfor %}
<tr><td><b>All clinic consumables</b><br><span class=muted>{{alln}} paper{{'' if alln==1 else 's'}}{% if pending %} · {{pending}} still pending approval{% endif %}</span></td><td class=r><b>{{inr(alltotal)}}</b></td></tr></table></div>
{% if unsorted %}<p><a class=btn href="{{url_for('d664_papers')}}">Sort the {{unsorted}} unsorted paper{{'' if unsorted==1 else 's'}}</a></p>{% endif %}
<div class=d6card style="font-size:14px"><b style="font-size:15px">Kept apart, each in its own lane</b>
{% for k, nm, n in apart %}<div class=d6line style="padding:6px 0"><div style="flex:1">{{nm}}</div><div class=nw>{{n}} paper{{'' if n==1 else 's'}}</div></div>{% endfor %}</div>
<p class=muted>Tap a group to see its papers. A paper with no amount read counts as a paper and adds nothing to the total until its amount is typed on the bill.
 A paper counts in the month set on its bill; if none was set, the month of its bill date; if no date was read, the month it was scanned.</p>{% endif %}</div>"""


def _back(default_endpoint="d664_papers"):
    return AR._safe_from(request.values.get("back")) or url_for(default_endpoint)


def papers():
    db = AR.get_db()
    where = _live(db) + " AND COALESCE(b.subgroup,'')=''"
    total = db.execute("SELECT COUNT(*) FROM bills b WHERE " + where).fetchone()[0]
    rows = db.execute("SELECT b.* FROM bills b WHERE " + where + " ORDER BY b.id DESC LIMIT ?", (PAGE_N,)).fetchall()
    return AR.page(PAPERS_TPL, papers=[_paper(db, b) for b in rows], total=total, more=(total > len(rows)),
                   inr=_inr, flow=AR._flow("Clinic papers to sort", url_for("bills_list")))


def paper(bid):
    db = AR.get_db()
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    p = _paper(db, b)
    return AR.page(PAPER_TPL, p=p, cur=p["group"], sug=(p["s"]["value"] if (p["s"] and p["s"]["kind"] == "sub") else ""),
                   on_clinic=((b["lane"] or "clinic") == "clinic" and b["status"] != "rejected"),
                   lanes=AR.LANES, lane_order=AR.LANE_ORDER, inr=_inr, back=_back(),
                   flow=AR._flow("Clinic paper " + p["stamp"], _back()))


def set_group(bid):
    db = AR.get_db()
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    to = (request.form.get("subgroup") or "").strip().lower()
    back = _back()
    stamp = b["stamp_no"] or ("#%d" % bid)
    if to and to not in SUB:
        abort(400)
    if (b["lane"] or "clinic") != "clinic" or b["status"] == "rejected":
        flash("%s is not a live paper on the clinic lane — groups belong to clinic consumables only." % stamp)
        return redirect(back)
    frm = b["subgroup"] or ""
    if to != frm:
        db.execute("UPDATE bills SET subgroup=? WHERE id=?", (to or None, bid))
        AR._audit_bill(db, bid, "subgroup", {"from": frm, "to": to})
        db.commit()
    flash(("%s is under %s." % (stamp, SUB[to])) if to else ("%s has no group now." % stamp))
    return redirect(back)


def _ym_ok(ym):
    return bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", ym or ""))


def _ym_shift(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) + k
    while m < 1:
        y, m = y - 1, m + 12
    while m > 12:
        y, m = y + 1, m - 12
    return "%04d-%02d" % (y, m)


MONTH_OF = ("COALESCE(NULLIF(b.bill_month,''), substr(NULLIF(b.bill_date,''),1,7), "
            "substr(datetime(b.created_at,'+330 minutes'),1,7), substr(b.created_at,1,7))")


def month():
    db = AR.get_db()
    today = datetime.date.today().strftime("%Y-%m")
    ym = request.args.get("ym", "")
    if not _ym_ok(ym):
        ym = today
    g_ = request.args.get("g", "")
    live = _live(db)
    rows = db.execute("SELECT b.* FROM bills b WHERE " + live + " AND " + MONTH_OF + "=? ORDER BY b.bill_date, b.id",
                      (ym,)).fetchall()

    def agg(pred):
        sel = [b for b in rows if pred(b["subgroup"] or "")]
        ven = []
        for b in sel:
            v = (b["vendor"] or "").strip()
            if v and v not in ven:
                ven.append(v)
        return dict(n=len(sel), total=sum(b["total_amount"] or 0 for b in sel),
                    noamt=sum(1 for b in sel if b["total_amount"] is None),
                    vendors=", ".join(ven[:3]) + (" and %d more" % (len(ven) - 3) if len(ven) > 3 else ""), rows=sel)

    if g_ in ("procedure", "xray", "others", "unsorted"):
        a = agg((lambda s: s == "") if g_ == "unsorted" else (lambda s: GROUP_OF.get(s) == g_))
        return AR.page(MONTH_TPL, ym=ym, prev=_ym_shift(ym, -1), nxt=(_ym_shift(ym, 1) if ym < today else None),
                       label=AR._month_label, inr=_inr, g=g_, rows=a["rows"], sub=SUB,
                       gname=("Not sorted yet" if g_ == "unsorted" else dict((k, n) for k, n, _h in GROUPS)[g_]),
                       here=AR._here(full=True), flow=AR._flow("Clinic consumables", url_for("bills_list")))
    table = []
    for key, name, _hint in GROUPS:
        a = agg(lambda s, key=key: GROUP_OF.get(s) == key)
        table.append(dict(key=key, name=name, sub=False, **{k: a[k] for k in ("n", "total", "noamt", "vendors")}))
        if key == "xray":
            for sk, sn in (("xray_small", "Small film"), ("xray_11x14", "11 x 14 film"), ("xray", "size not known")):
                s2 = agg(lambda s, sk=sk: s == sk)
                if s2["n"]:
                    table.append(dict(key=None, name=sn, sub=True, n=s2["n"], total=s2["total"], noamt=0, vendors=""))
    u = agg(lambda s: s == "")
    table.append(dict(key="unsorted", name="Not sorted yet", sub=False, n=u["n"], total=u["total"], noamt=u["noamt"],
                      vendors=u["vendors"]))
    apart = []
    names = {"pharmacy": "Pharmacy purchases — Sanjeevni", "lab_purchase": "Lab purchases — NK Pathology",
             "owner_expense": "Dr MK expense", "other_doc": "Other documents — not bills"}
    extra = " AND b.page_of IS NULL" if "page_of" in _cols(db) else ""
    for k in ("pharmacy", "lab_purchase", "owner_expense", "other_doc"):
        n = db.execute("SELECT COUNT(*) FROM bills b WHERE b.lane=? AND b.status<>'rejected' AND b.dup_of IS NULL"
                       + extra + " AND " + MONTH_OF + "=?", (k, ym)).fetchone()[0]
        apart.append((k, names[k], n))
    return AR.page(MONTH_TPL, ym=ym, prev=_ym_shift(ym, -1), nxt=(_ym_shift(ym, 1) if ym < today else None),
                   label=AR._month_label, inr=_inr, g="", table=table, alln=len(rows),
                   alltotal=sum(b["total_amount"] or 0 for b in rows),
                   pending=sum(1 for b in rows if b["status"] == "draft"), unsorted=u["n"], apart=apart,
                   flow=AR._flow("Clinic consumables", url_for("bills_list")))


# ---------------------------------------------------------------------------------------------- the mount
def init(ar):
    """Called once, at the foot of asset_register.py. Adds the column, the four addresses and two helpers the asset
    app's own pages may call (each guarded there by 'is defined', so the pages do not need this file)."""
    global AR
    AR = ar
    db = sqlite3.connect(ar.DB_PATH, timeout=20)
    try:
        ensure(db)
    finally:
        db.close()
    app = ar.app
    app.add_url_rule("/papers", "d664_papers", ar.checker_required(papers))
    app.add_url_rule("/papers/month", "d664_month", ar.checker_required(month))
    app.add_url_rule("/papers/<int:bid>", "d664_paper", ar.checker_required(paper))
    app.add_url_rule("/bills/<int:bid>/subgroup", "d664_set", ar.checker_required(set_group), methods=["POST"])
    app.jinja_env.globals.update(d664_group_label=group_label, d664_to_sort=to_sort_count)
    return VERSION
