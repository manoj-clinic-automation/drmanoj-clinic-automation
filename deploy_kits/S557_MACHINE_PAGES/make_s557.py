#!/usr/bin/env python3
"""make_s557.py -- S557_MACHINE_PAGES: the two edited files rebuilt from the pinned live bytes, and the new module copied.

    python3 make_s557.py <dir with the live asset_register.py and sorting_desk.py> <out dir>

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the
counted number of times. Every byte of the two edited files comes from the live file plus these edits; asset_machine.py
(NEW) is the kit's own file, copied beside them."""
import hashlib, os, shutil, sys

FROM = {"asset_register.py": "7ac386641095cacbac79594356e7ec6d",
        "sorting_desk.py": "7e16fd80d6bd2bfe0a6e5366848d8569"}

AR_EDITS = [
    # A1 (B1) -- one word per lane on the owner's and managers' pages: the bill page, the lanes page and the papers pages
    #            receive LANES; for an owner / manager on those pages they get the same tuples with S555's one word first.
    #            Reception's pages (the intake, the slip, its own list and bill view) never change.
    ('    flow = ctx.pop("flow", None)                               # S440: a page of the scan flow carries the BACK bar and the up-arrow\n',
     '    flow = ctx.pop("flow", None)                               # S440: a page of the scan flow carries the BACK bar and the up-arrow\n'
     '    if ctx.get("lanes") is LANES and _s557_short_lanes(u):     # S557 B1: one word per lane (owner / manager pages only)\n'
     '        ctx["lanes"] = LANES_SHORT_S557\n', 1),
    # A2 (B1) -- the flash after a lane move (it shows on the bill page)
    ('    flash("%s moved to %s." % (b["stamp_no"] or ("#%d" % bid), LANES[to][0]))\n',
     '    flash("%s moved to %s." % (b["stamp_no"] or ("#%d" % bid), LANE_WORD.get(to) or LANES[to][0]))      # S557 B1\n', 1),
    # A3 (B1) -- the flash on the lanes page
    ('            flash("%s opens on %s." % (u, LANES[lane][0]))\n',
     '            flash("%s opens on %s." % (u, LANE_WORD.get(lane) or LANES[lane][0]))      # S557 B1\n', 1),
    # A4 (A1) -- the machine page: the cover line and the totals at the top (nothing at all when the hook gives nothing)
    ("{% endif %}</p>\n<div class=grid>\n<div class=card>{% if ent_name %}",
     "{% endif %}</p>\n{{s557[0]}}<div class=grid>\n<div class=card>{% if ent_name %}", 1),
    # A5 (A2-A4) -- the machine page: Parts, Cover history, Spends below the existing details
    ("{% if a['notes'] %}<div class=card>{{a['notes']}}</div>{% endif %}",
     "{{s557[1]}}{% if a['notes'] %}<div class=card>{{a['notes']}}</div>{% endif %}", 1),
    # A6 -- the machine page's one hook
    ("        ent_name=ent_name, zone_name=zone_name, today=today().isoformat())\n",
     "        ent_name=ent_name, zone_name=zone_name, today=today().isoformat(), s557=_s557_machine(a))      # S557: the machine pages\n", 1),
    # A7 (A5) -- the renewals hook: every live cover's and part's one reminder is on the list before it is read
    ("def renewals():\n    db = get_db()\n",
     "def renewals():\n    db = get_db()\n    _s557_heal(db)                                               # S557 A5: the covers' and parts' reminders\n", 1),
    # A8 (A6) -- the paper's own page: "Linked to <machine> as purchase / part / cover / spend", or "+ asset record"
    ("{% if b['dup_of'] %}<span class=\"badge red\">duplicate of {{dupstamp",
     "{{s557_line}}{% if b['dup_of'] %}<span class=\"badge red\">duplicate of {{dupstamp", 1),
    ("        b=b, items=items, sarvam_on=_reader_on(), blank=blank, lanes=LANES, lane_order=LANE_ORDER,\n",
     "        b=b, items=items, sarvam_on=_reader_on(), blank=blank, lanes=LANES, lane_order=LANE_ORDER, s557_line=_s557_paper_line(b),\n", 1),
    # A9 -- the guarded mount, after the sorting desk's
    ("# --- S551_SORTING_DESK end ---\n",
     "# --- S551_SORTING_DESK end ---\n"
     "\n\n"
     "# --- S557_MACHINE_PAGES begin -- D719: the machine pages -- parts, cover history, spends, each with its paper (14-Oct-2026) ---\n"
     "# Guarded: if asset_machine.py is absent or cannot load, this app runs exactly as before -- the hooks below give nothing.\n"
     "LANES_SHORT_S557 = {_k: ((LANE_WORD.get(_k) or _v[0]),) + tuple(_v[1:]) for _k, _v in LANES.items()}      # S557 B1\n"
     "_S557_SHORT_EPS = frozenset((\"bill_view\", \"lanes_admin\", \"d664_papers\", \"d664_paper\", \"d664_challans\", \"d664_join\", \"d664_month\"))\n"
     "\n\n"
     "def _s557_short_lanes(u):\n"
     "    \"\"\"S557 B1: the owner's and managers' pages name a lane in one word (S555's LANE_WORD, the one helper); reception's\n"
     "    pages -- the intake, the slip, its own list and bill view -- never change.\"\"\"\n"
     "    try:\n"
     "        return bool(u) and u[\"role\"] in (\"owner\", \"manager\") and request.endpoint in _S557_SHORT_EPS\n"
     "    except Exception:                                            # noqa: BLE001\n"
     "        return False\n"
     "\n\n"
     "def _s557_mod():\n"
     "    _m = _sys.modules.get(\"asset_machine\")\n"
     "    return _m if (_m is not None and getattr(_m, \"MOUNTED\", False)) else None\n"
     "\n\n"
     "def _s557_machine(a):\n"
     "    \"\"\"The machine page's hook: (top, folds); nothing when the module is not mounted or the page is not for this person.\"\"\"\n"
     "    try:\n"
     "        _m = _s557_mod()\n"
     "        return _m.sections(a) if _m else (Markup(\"\"), Markup(\"\"))\n"
     "    except Exception as _ex:                                     # noqa: BLE001\n"
     "        print(\"asset_machine sections: %s\" % _ex, file=_sys.stderr)\n"
     "        return (Markup(\"\"), Markup(\"\"))\n"
     "\n\n"
     "def _s557_paper_line(b):\n"
     "    try:\n"
     "        _m = _s557_mod()\n"
     "        return _m.paper_line(b) if _m else Markup(\"\")\n"
     "    except Exception as _ex:                                     # noqa: BLE001\n"
     "        print(\"asset_machine paper line: %s\" % _ex, file=_sys.stderr)\n"
     "        return Markup(\"\")\n"
     "\n\n"
     "def _s557_heal(db):\n"
     "    try:\n"
     "        _m = _s557_mod()\n"
     "        if _m:\n"
     "            _m.heal(db)\n"
     "    except Exception as _ex:                                     # noqa: BLE001\n"
     "        try:\n"
     "            db.rollback()\n"
     "        except Exception:                                        # noqa: BLE001\n"
     "            pass\n"
     "        print(\"asset_machine heal: %s\" % _ex, file=_sys.stderr)\n"
     "\n\n"
     "try:\n"
     "    import asset_machine as _asset_machine\n"
     "    _asset_machine.init(_sys.modules[__name__])\n"
     "except Exception as _ex_s557:                                  # noqa: BLE001\n"
     "    print(\"asset_machine NOT mounted: %s\" % _ex_s557, file=_sys.stderr)\n"
     "# --- S557_MACHINE_PAGES end ---\n", 1),
]

SD_EDITS = [
    # S1 -- the marker (VERSION and CORRECTIONS stay: the S551 and S555 walks read them)
    ("#                               Claude's reading beside each box (VERSION is kept: S551's walk reads it)\n",
     "#                               Claude's reading beside each box (VERSION is kept: S551's walk reads it)\n"
     "MACHINE = \"S557\"              # S557_MACHINE_PAGES: the machine-pages switch, one word per lane, a non-number amount ignored\n", 1),
    ("import json\nimport re\n", "import json\nimport math\nimport re\n", 1),
    # S2 (A7) -- the Switches card's fourth line, through POST /desk/switch (the allowed keys are this tuple)
    ('SWITCHES = (("scan.cv", "Smart scanner"), ("scan.lanes5", "Reception buttons"), ("desk.on", "Sorting desk for Shavez"))\n',
     'SWITCHES = (("scan.cv", "Smart scanner"), ("scan.lanes5", "Reception buttons"), ("desk.on", "Sorting desk for Shavez"),\n'
     '            ("machine.on", "Machine pages for Shavez"))                                  # S557 A7\n', 1),
    ('    return {"scan.cv": bool(AR._scan_cv_on()), "scan.lanes5": bool(AR._lanes5_on()), "desk.on": desk_on(db)}\n',
     '    return {"scan.cv": bool(AR._scan_cv_on()), "scan.lanes5": bool(AR._lanes5_on()), "desk.on": desk_on(db),\n'
     '            "machine.on": (_setting(db, "machine.on", "off") or "").strip().lower() == "on"}      # S557 A7\n', 1),
    # S3 (B2) -- a Claude amount that is not a number (NaN, inf, text) is ignored: never shown, never in a paper's JSON
    ("        amt = None\n    dt = parse_date(data.get(\"bill_date\")) or parse_date(data.get(\"date_as_read\"))\n",
     "        amt = None\n"
     "    if amt is not None and not math.isfinite(amt):                  # S557 B2 (S555 review N1): NaN / inf -> ignored\n"
     "        amt = None\n"
     "    dt = parse_date(data.get(\"bill_date\")) or parse_date(data.get(\"date_as_read\"))\n", 1),
    ("def _qty(q):\n    try:\n        f = float(q)\n        return (\"%d\" % f) if f == int(f) else (\"%g\" % f)\n    except (TypeError, ValueError):\n",
     "def _qty(q):\n    try:\n        f = float(q)\n"
     "        if not math.isfinite(f):                                     # S557 B2: a quantity that is not a number shows nothing\n"
     "            return \"\"\n"
     "        return (\"%d\" % f) if f == int(f) else (\"%g\" % f)\n    except (TypeError, ValueError, OverflowError):\n", 1),
    ("    try:\n        f = float(x)\n    except (TypeError, ValueError):\n        return \"\"\n    return (\"%d\" % f) if f == int(f) else (\"%.2f\" % f)\n",
     "    try:\n        f = float(x)\n    except (TypeError, ValueError):\n        return \"\"\n"
     "    if not math.isfinite(f):                                         # S557 B2\n        return \"\"\n"
     "    return (\"%d\" % f) if f == int(f) else (\"%.2f\" % f)\n", 1),
    # S4 (B3, S555 review N2) -- a stored date with a time part is compared as its day (no spurious "Claude read" date line)
    ('        if cd and cd != parse_date(b["bill_date"]):\n',
     '        if cd and cd != (parse_date(b["bill_date"]) or _iso(b["bill_date"])):          # S557 B3 (review N2)\n', 1),
    # S5 (A6) -- the machine helpers the desk reads (both fall back to nothing / the old bridge)
    ("def paper_json(db, b, owner, today=None):\n",
     "def _s557_machine():\n"
     "    m = sys.modules.get(\"asset_machine\")\n"
     "    return m if (m is not None and getattr(m, \"MOUNTED\", False)) else None\n"
     "\n\n"
     "def _s557_linked(db, b, owner):\n"
     "    \"\"\"S557 A6: 'Linked to <machine> as ...' for the Clinic-equipment destination note ('' when not linked / not mounted).\"\"\"\n"
     "    try:\n"
     "        m = _s557_machine()\n"
     "        return m.linked_text(db, b[\"id\"], owner) if m else \"\"\n"
     "    except Exception:                                                # noqa: BLE001\n"
     "        return \"\"\n"
     "\n\n"
     "def _s557_add_to(db, b, owner, a, it1):\n"
     "    \"\"\"S557 A6: where '+ asset record' goes -- ('machine', bill id): a new machine pre-filled from the paper (asset_machine);\n"
     "    else ('item', bill item id): the old bill-item bridge; else None. No url_for here (month_data is also read outside a request).\"\"\"\n"
     "    if a or not owner or b[\"status\"] != \"approved\":\n"
     "        return None\n"
     "    try:\n"
     "        m = _s557_machine()\n"
     "        if m:\n"
     "            return (\"machine\", b[\"id\"]) if m.can_from_paper(db, b, owner) else None\n"
     "    except Exception:                                                # noqa: BLE001\n"
     "        pass\n"
     "    return (\"item\", it1[0]) if it1 else None\n"
     "\n\n"
     "def paper_json(db, b, owner, today=None):\n", 1),
    # S6 (B1, A6) -- the desk's paper: the lane in one word; the machine it is linked to
    ('            "status": status, "lane": AR.LANES.get(_lane(b), ("",))[0].split(" — ")[0],\n',
     '            "status": status, "lane": AR._lane_word_s555(b), "linked": _s557_linked(db, b, owner),      # S557 B1, A6\n', 1),
    # S7, S8 (B1) -- Bills awaited's "what" line in one word per lane
    ('        cd["what"].add(AR.LANES.get(_lane(c), ("",))[0].split(" — ")[0] + ((" · " + CP.SUB.get(c["subgroup"], "")) if c["subgroup"] else ""))\n',
     '        cd["what"].add(AR._lane_word_s555(c) + ((" · " + CP.SUB.get(c["subgroup"], "")) if c["subgroup"] else ""))      # S557 B1\n', 1),
    ('        cd["what"].add(AR.LANES.get(_lane(f), ("",))[0].split(" — ")[0] + ((" · " + CP.SUB.get(f["subgroup"], "")) if f["subgroup"] else ""))\n',
     '        cd["what"].add(AR._lane_word_s555(f) + ((" · " + CP.SUB.get(f["subgroup"], "")) if f["subgroup"] else ""))      # S557 B1\n', 1),
    # S9 (A6) -- the month page's Clinic-equipment row: "+ asset record" opens the machine pre-filled from the paper
    ('                           "add": (it1[0] if (it1 and owner and b["status"] == "approved" and not a) else None),\n',
     '                           "add": (it1[0] if (it1 and owner and b["status"] == "approved" and not a) else None),\n'
     '                           "add_to": _s557_add_to(db, b, owner, a, it1),                         # S557 A6\n', 1),
    ("{% elif e.add %} · <a href=\"{{url_for('asset_edit', bill_item=e.add)}}\">+ asset record</a>",
     "{% elif e.add_to %} · <a href=\"{{url_for('s557_from_paper', bid=e.add_to[1]) if e.add_to[0]=='machine' else url_for('asset_edit', bill_item=e.add_to[1])}}\">+ asset record</a>", 1),
    # S10 (A6) -- the desk's Clinic-equipment destination note carries the "Linked to" line
    ("var note=C.notes[S.dest]||'';if(S.dest=='clinic_equipment'&&!C.owner){note='Waiting for Dr Manoj’s Save after yours: it is filed, not accepted.';}\n",
     "var note=C.notes[S.dest]||'';if(S.dest=='clinic_equipment'&&!C.owner){note='Waiting for Dr Manoj’s Save after yours: it is filed, not accepted.';}\n"
     " if(S.dest=='clinic_equipment'&&j.linked){note=(note?note+' ':'')+j.linked;}\n", 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, raw, edits):
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not the pinned %s" % (name, md5(raw)[:8], FROM[name][:8]))
    s = raw.decode("utf-8")
    for i, (old, new, n) in enumerate(edits, 1):
        c = s.count(old)
        if c != n:
            sys.exit("REFUSED: %s edit %d anchor found %d times, expected %d" % (name, i, c, n))
        s = s.replace(old, new)
    return s.encode("utf-8")


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for name, edits in (("asset_register.py", AR_EDITS), ("sorting_desk.py", SD_EDITS)):
        raw = open(os.path.join(src, name), "rb").read()
        new = build(name, raw, edits)
        open(os.path.join(out, name), "wb").write(new)
        print("%s %s -> %s (%d counted edits)" % (name, FROM[name][:8], md5(new), len(edits)))
    here = os.path.dirname(os.path.abspath(__file__))
    shutil.copyfile(os.path.join(here, "asset_machine.py"), os.path.join(out, "asset_machine.py"))
    print("asset_machine.py NEW -> %s" % md5(open(os.path.join(out, "asset_machine.py"), "rb").read()))


if __name__ == "__main__":
    main()
