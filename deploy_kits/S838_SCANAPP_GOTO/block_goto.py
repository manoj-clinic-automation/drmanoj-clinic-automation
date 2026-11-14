

# ---------------------------------------------------------------------------------------------- S838_SCANAPP_GOTO
# The owner's FINAL mock-up ("FINAL", 20:32 IST 14-Nov-2026; https://claude.ai/artifact/JPVjEyijD9doKinJKgvDHY): the scan app's top bar
# keeps three everyday links -- Sorting desk, The month, Bills awaited -- and one button, Go to ▾, opening EVERY scan-app page grouped,
# as the Sanjeevni Hub's Go to does: 1 Papers coming in . 2 Clinic purchases & stock . 3 Dealers . 4 Machines & renewals . 5 Yours only.
# The panel is built from the bar's OWN list (asset_register._s559_items -- never a second list): a person sees only the pages he has.
# Shavez's bar changes only when the switch "Go to menu for Shavez" (bar.goto, absent = OFF) is on; the owner sees it at once.
# The bar's helper is defined in asset_register AFTER this desk mounts, so it is taken over once, at the first request a worker serves
# (asset_register whole by then): asset_register._s559_bar and the Jinja global s559_bar. Any error draws the old bar.
GOTO = "S838"
S838_PIN = ("s551_desk", "s551_month", "s551_awaited")
S838_BOLD = ("s551_desk", "s551_month")
S838_GROUPS = (("1 · Papers coming in", ("s551_desk", "s838_add", "s551_awaited", "bills_list")),
               ("2 · Clinic purchases & stock", ("s551_month", "s634_page", "s637_morning", "s568_stock", "s568_issue", "s674_sort", "s582_xray")),
               ("3 · Dealers", ("s551_implants", "vendors_list", "s838_hub")),
               ("4 · Machines & renewals", ("assets_list", "s571_page", "renewals")),
               ("5 · Yours only", ("admin", "s838_switches")))
S838_LABEL = {"s551_implants": "Implant stock ledger", "s582_xray": "X-ray films"}
S838_NOTE = {"s551_desk": "sort each scanned paper", "s551_awaited": "challans by supplier", "s551_month": "spend by group, credit notes taken off",
             "s838_hub": "pharmacy bills, Marg, dealer ledgers", "s838_switches": "on The month, at the top"}
S838_SUB = {"s551_desk": "bills, challans, receipts, statements, credit notes"}
S838_HUB = "/finance/approvals"
S838_OLD = []
S838_CSS = (".s838w{position:relative;flex:none}"
            ".s838go{font:inherit;font-size:14px;font-weight:700;color:#1f2a36;background:#fff;border:0;border-radius:8px;padding:6px 12px;min-height:36px;cursor:pointer}"
            ".s838go span{font-weight:400;color:#4a5866}"
            ".s838p{position:absolute;top:100%;left:18px;right:18px;z-index:1000;background:#fff;border:1px solid #c9d4df;border-top:0;border-radius:0 0 12px 12px;"
            "box-shadow:0 8px 22px rgba(20,40,70,.16);padding:16px 20px 20px;max-height:80vh;overflow:auto;color:#1f2a36;font-size:14.5px;line-height:1.45;"
            "font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,Helvetica,Arial,sans-serif;box-sizing:border-box}"
            ".s838p[hidden]{display:none}.s838top{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:12px}"
            ".s838top .m{font-size:13.5px;color:#4a5866}.s838x{font:inherit;font-size:13px;color:#1d4f80;background:none;border:1px solid #c9d4df;border-radius:6px;padding:4px 10px;min-height:32px;cursor:pointer}"
            ".s838g{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px 26px}.s838g>div{display:flex;flex-direction:column;gap:7px}"
            ".s838h{font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#3a5a78;border-bottom:1px solid #e3e8ee;padding-bottom:4px}"
            ".s838p a{color:#1d4f80;text-decoration:none}.s838p a:hover{text-decoration:underline}.s838p a.on{font-weight:700}"
            ".s838n{color:#4a5866}.s838s{font-size:12.5px;color:#4a5866;margin-top:-4px}")
S838_TPL = ("<style>{{css}}</style><div class=s838w><div class=s559h id=s559bar role=navigation>"
            "<a class=s559t href=\"{{url_for('dashboard')}}\"><b>\U0001F5C2 Scan app &amp; assets</b> <span class=s559v>v{{version}}</span></a>"
            "<nav>{% for ep_, label, href in pin %}<a href=\"{{href}}\" data-s559=\"{{ep_}}\"{% if ep_==ep %} class=on aria-current=page{% endif %}>{{label}}</a>{% endfor %}"
            "<button type=button id=s838go class=s838go aria-expanded=false aria-controls=s838panel>Go to ▾ <span>every scan-app page</span></button>"
            "{% for ep_, label, href in tail %}<a href=\"{{href}}\" data-s559=\"{{ep_}}\"{% if ep_==ep %} class=on aria-current=page{% endif %}>{{label}}</a>{% endfor %}</nav></div>"
            "<div id=s838panel class=s838p hidden><div class=s838top><div><b style=\"font-size:17px\">Go to</b> <span class=m>· every scan-app page, one tap · "
            "a number means something is waiting</span></div><button type=button id=s838close class=s838x>close ✕</button></div><div class=s838g>"
            "{% for title, rows in groups %}<div><div class=s838h>{{title}}</div>{% for ep_, label, href, note, sub in rows %}"
            "<a href=\"{{href}}\" data-s838=\"{{ep_}}\"{% if ep_==ep %} class=on{% endif %}>{% if ep_ in bold %}<b>{{label}}</b>{% else %}{{label}}{% endif %}"
            "{% if note %} <span class=s838n>— {{note}}</span>{% endif %}</a>{% if sub %}<span class=s838s>{{sub}}</span>{% endif %}{% endfor %}</div>{% endfor %}"
            "</div></div></div><script>(function(){var b=document.getElementById('s838go'),p=document.getElementById('s838panel');if(!b||!p){return;}"
            "function set(o){p.hidden=!o;b.setAttribute('aria-expanded',o?'true':'false');}"
            "b.addEventListener('click',function(e){e.stopPropagation();set(p.hidden);});"
            "var c=document.getElementById('s838close');if(c){c.addEventListener('click',function(){set(false);});}"
            "document.addEventListener('click',function(e){if(!p.hidden&&!p.contains(e.target)&&e.target!==b){set(false);}});"
            "document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!p.hidden){set(false);}});})();</script>")


def _s838_on(role):
    """Go to for this person: the owner always; a manager while bar.goto is on (absent = off); nobody else (no bar at all)."""
    if role == "owner":
        return True
    if role != "manager":
        return False
    try:
        return (_setting(AR.get_db(), "bar.goto", "off") or "").strip().lower() == "on"
    except Exception:                                                # noqa: BLE001
        return False


def _s838_parts(u):
    """(pin, tail, groups) from the bar's own items. pin: the three everyday links; tail: the account and Logout; groups: the
    panel's five groups (a group with nothing for this person is left out) and 'Other pages' for any page not placed."""
    role = AR._s559_role(u)
    items = list(AR._s559_items(u))
    by = {ep: (ep, label, href) for ep, label, href in items}
    if "s551_desk" in by and "s568_add" in AR.app.view_functions:
        by["s838_add"] = ("s838_add", "Add a paper from a file", url_for("s568_add"))
    if role == "owner":
        by["s838_hub"] = ("s838_hub", "Sanjeevni Hub ↗", S838_HUB)
        by["s838_switches"] = ("s838_switches", "The switches", url_for("s551_month") + "#s551switches")
    pin = [by[e] for e in S838_PIN if e in by]
    tail = [by[e] for e in ("account", "logout") if e in by]
    groups, placed = [], {"account", "logout"}
    for title, eps in S838_GROUPS:
        rows = [(e, S838_LABEL.get(e, by[e][1]), by[e][2], S838_NOTE.get(e, ""), S838_SUB.get(e, "")) for e in eps if e in by]
        placed.update(eps)
        if rows:
            groups.append((title, rows))
    rest = [(e, l, h, "", "") for e, l, h in items if e not in placed]
    if rest:
        groups.append(("Other pages", rest))
    return pin, tail, groups


def _s838_bar(u=None):
    """THE bar from now on: Go to for the owner (and Shavez with bar.goto on); the old bar for anyone else and on any error."""
    old = S838_OLD[0] if S838_OLD else None
    try:
        u = AR.current_user() if u is None else u
        if not _s838_on(AR._s559_role(u)):
            return old(u) if old else Markup("")
        pin, tail, groups = _s838_parts(u)
        if not (pin or groups):
            return old(u) if old else Markup("")
        here = request.endpoint
        if here == "dashboard":
            here = ""
        return Markup(render_template_string(S838_TPL, pin=pin, tail=tail, groups=groups, ep=here, version=AR.APP_VERSION,
                                             css=Markup(AR._S559_BAR_CSS + S838_CSS), bold=S838_BOLD))
    except Exception as ex:                                          # noqa: BLE001
        print("S838 bar: %s" % ex, file=sys.stderr)
        try:
            return old(u) if old else Markup("")
        except Exception:                                            # noqa: BLE001
            return Markup("")


def _s838_take(ar):
    """Once per worker, at its first request: the bar's helper (asset_register._s559_bar) and the Jinja global become Go to's."""
    if S838_OLD or not callable(getattr(ar, "_s559_bar", None)) or not hasattr(ar, "_s559_items"):
        return
    S838_OLD.append(ar._s559_bar)
    ar._s559_bar = _s838_bar
    ar.app.jinja_env.globals["s559_bar"] = _s838_bar


def _s838_mount(ar):
    def first():
        if S838_OLD:
            return None
        try:
            _s838_take(ar)
        except Exception as ex:                                      # noqa: BLE001
            print("S838 Go to: NOT mounted (%s)" % ex, file=sys.stderr)
        return None
    ar.app.before_request(first)


# --- S838_SCANAPP_GOTO end ---
