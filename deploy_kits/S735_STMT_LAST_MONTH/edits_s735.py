# -*- coding: utf-8 -*-
"""edits_s735.py -- S735_STMT_LAST_MONTH: the counted edits on /root/assetapp/stationery.py (FROM 3a22c6bb, S674's file = live).

D845 item 1 (the owner's "eos, build in fresh session then", 17:58 IST 06-Nov-2026): the Variety flow's first month checked end to
end on the live page (read only, 19:1x IST 06-Nov). Found: no statement was ever made; the Stationery page offers ONLY the current
month's statement (its month is today's), so once November began, October's statement could no longer be made on its own -- the
November one would have swallowed every older line. The server's make door already takes any month (stmt_make_post reads ym from
the form); only the page lacked the button. The owner confirmed at 19:2x IST that Variety's six challans of 24-Aug .. 14-Oct are
all unpaid -- they go on October's statement (August's and September's named "earlier, not billed yet", as S674 already words it).

What changes, on the owner's Stationery page only (section 5, Monthly statement):
  * while NO statement stands for the month just ended, none for the current month either, and the month just ended has
    unbilled lines up to its end: the page offers "Make <last month>'s statement" (N lines on M papers) INSTEAD of the current
    month's button, with the words "<this month>'s comes after it." The header names that month.
  * once last month's stands (or it has nothing), the page is exactly as before.
Nothing else: no table, no column, no data step, no change to stmt_make / its door / the staff screen / the account.

Each edit is (name, (old, new)): `old` must occur EXACTLY ONCE in the FROM bytes, or make_s735.py refuses and writes nothing.
"""

KIT = "S735_STMT_LAST_MONTH"

E_MARK = ('FLOOR_KEY = "stationery.suppliers_from"',
          'STMT_LAST = "S735"                     # S735_STMT_LAST_MONTH: the page offers the month just ended first\n'
          'FLOOR_KEY = "stationery.suppliers_from"')

E_PREV = ('def _end_of(ym):\n',
          'def _prev_ym(ym):                                                    # S735: the month just ended\n'
          '    y, m = int(ym[:4]), int(ym[5:7])\n'
          '    return "%04d-%02d" % ((y, m - 1) if m > 1 else (y - 1, 12))\n'
          '\n'
          '\n'
          'def _end_of(ym):\n')

E_VIEW = ('    pending = stmt_lines_for(db, ym, keys[0]) if keys else []\n',
          '    pending = stmt_lines_for(db, ym, keys[0]) if keys else []\n'
          '    prev = _prev_ym(ym)                                              # S735: last month first, while none stands for it\n'
          '    prev_stands = any(s["ym"] == prev and s["supplier"] == (keys[0] if keys else "") for s in stmts)\n'
          '    prev_pending = stmt_lines_for(db, prev, keys[0]) if (keys and not cur_month and not prev_stands) else []\n')

E_RET = ('"cur": cur, "cur_month": cur_month, "pending": pending, ',
         '"cur": cur, "cur_month": cur_month, "pending": pending, "prev": prev, "prev_first": bool(prev_pending), "prev_pending": prev_pending, '
         '"prev_pending_papers": _group_by_paper(prev_pending), ')

E_HEAD = ('<b>5 · Monthly statement{% if f.cur %} — {{mlabel(f.cur.ym)}}{% else %} — {{label}}{% endif %}</b>',
          '<b>5 · Monthly statement{% if f.cur %} — {{mlabel(f.cur.ym)}}{% elif f.prev_first %} — {{mlabel(f.prev)}}{% else %} — {{label}}{% endif %}</b>')

E_BTN = ('{% if not f.cur_month %}<form method=post action="{{url_for(\'s674_stmt_make\')}}"',
         '{% if f.prev_first %}<form method=post action="{{url_for(\'s674_stmt_make\')}}" id=s735prev style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">'
         '<input type=hidden name=ym value="{{f.prev}}"><button class=btn>Make {{mlabel(f.prev)}}\'s statement</button>\n'
         '<span class=muted>{{f.prev_pending|length}} line{{\'\' if f.prev_pending|length == 1 else \'s\'}} on {{f.prev_pending_papers|length}} '
         'paper{{\'\' if f.prev_pending_papers|length == 1 else \'s\'}} up to its end ready · {{label}}\'s comes after it.</span></form>\n'
         '{% elif not f.cur_month %}<form method=post action="{{url_for(\'s674_stmt_make\')}}"')

EDITS = [("mark", E_MARK), ("prev_ym", E_PREV), ("flow_view", E_VIEW), ("flow_return", E_RET), ("header", E_HEAD), ("button", E_BTN)]
