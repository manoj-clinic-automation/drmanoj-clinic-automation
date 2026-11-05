"""order_track_page.py -- S708_TRACK_REDESIGN (S387, Sanjeevni, 05-Nov-2026; D830): the order list and reception's scan work, rebuilt.

  The owner (05-Nov 09:41 IST, D830): the tracking page "collapsible sections with clear headers, PC and mobile, far less scrolling; the
  incomplete flows finished; for a bill scanned twice a way to pick the good scan; after the blurry / cut scans are deleted by their buttons
  the good ones stay visible". On the mock (17:50 IST): "scroll up button, collapsed default, expand all, collapse all button at top, scans
  that open shd be big enough for proper viewing in pc screen ... also need reception flow for their work generated frm this page".

  GET  /finance/porders/s454/track     page()      -- the owner (English) and porders.rescan_askers (Roman Hindi); ?old=1 = the S619 page
  GET  /finance/porders/s454/rescan    reception() -- reception's scan work: the rescans asked + the papers never scanned; ?old=1 = S618's
  POST /finance/porders/api/s454/s708/pick            {keep, drop}   one bill scanned twice: this one is right, the other is the copy
  POST /finance/porders/api/s454/s708/pick/undo       {id}
  POST /finance/porders/api/s454/s708/dealer          {scan, dealer} a scan saved under another dealer whose paper is not read for sure
  POST /finance/porders/api/s454/s708/paper           {order}        an order whose bill paper was never scanned -> reception
  POST /finance/porders/api/s454/s708/paper/withdraw  {id}
  POST /finance/porders/api/s454/s708/paper/scanned   {id}          reception: "Scan ho gaya" (the ask leaves reception's list)
  POST /finance/porders/api/s454/s708/paper/tie       {id, scan}    the owner / Shavez: "This is its bill" (one of the server's candidates)
  POST /finance/porders/api/s454/s708/paper/reask     {id}          back to reception (the old ask withdrawn, a new one made)
  POST /finance/porders/api/s454/s708/lost            {kind, id}     reception: the paper is not found (kind rescan | paper)
  POST /finance/porders/api/s454/s708/lost/clear      {id}           found after all
  (the routes are declared in porders_s454.py, beside the others; the logic is here.)

  ONE FACT, ONE PLACE: every list is the S619 / S618 / S628 reader's (order_track.light_all / full_all / wrong_dealer / paper_dealer /
  same_paper, porders_s454.rescan_list); this module only draws them and holds three tables of people's entries:
    s708_scan_pick   keep_id, drop_id -- order_track.Ctx reads it: the dropped scan is never usable, its head is the kept one
    s708_paper_ask   order_id         -- open while not withdrawn AND the order still has no scan (worked out on every read)
    s708_lost        kind, ref_id     -- reception's "Kaagaz nahi mila"; open while not cleared
  A read writes nothing. Words: porders_s454.T (the one wordbook), Roman Hindi for the staff, English for the owner.
"""
import datetime as dt
import json
import sqlite3
from urllib.parse import urlencode

KIT = "S708"
P = "/finance/porders"
PICK_DAYS = 7                                                 # a pick stays on the page, with Undo, this long
DONE_MAX = 60                                                 # Complete shows the newest this many; the older are counted
NOSCAN_HOURS = 20                                             # an arrived order with no scan after this long (or in Marg) is "never scanned"

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS s708_scan_pick (id INTEGER PRIMARY KEY AUTOINCREMENT, keep_id INTEGER NOT NULL, drop_id INTEGER NOT NULL, "
    "picked_by TEXT, picked_at TEXT, undone_at TEXT, undone_by TEXT)",
    "CREATE TABLE IF NOT EXISTS s708_paper_ask (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL, asked_by TEXT, asked_at TEXT, "
    "withdrawn_at TEXT, withdrawn_by TEXT, scanned_at TEXT, scanned_by TEXT)",
    "CREATE TABLE IF NOT EXISTS s708_lost (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, ref_id INTEGER NOT NULL, lost_by TEXT, "
    "lost_at TEXT, cleared_at TEXT, cleared_by TEXT)",
)


def _p4():
    import porders_s454 as P4                                 # noqa: PLC0415
    return P4


def _ot():
    import order_track as OT                                  # noqa: PLC0415
    return OT


def _os():
    import order_sheet as OS                                  # noqa: PLC0415
    return OS


def ensure(con):
    for s in SCHEMA:
        con.execute(s)


# ------------------------------------------------------------------ the words (into porders_s454.T, once)
WORDS = {
    "s708_hint": ("Section par tap karke kholiye / band kijiye", "Tap a section to open or close it"),
    "s708_since": ("%s se %d order", "%d orders since %s"),
    "s708_exp": ("Sab kholiye ▾", "Expand all ▾"), "s708_col": ("Sab band kijiye ▸", "Collapse all ▸"),
    "s708_up": ("Upar", "Top"),
    "s708_now": ("Abhi kya karna hai", "To do now"),
    "s708_now_late": ("%d order der se hain — dealer ko call kijiye", "Late orders: %d — call the dealer"),
    "s708_now_pair": ("%d bill ke do scan — saaf wala chuniye", "Bills scanned twice: %d — pick the clear one"),
    "s708_now_redo": ("%d scan kharab — reception ko bhejiye", "Bad scans: %d — send them to reception"),
    "s708_now_nosc": ("%d bill ka kaagaz scan nahi hua — reception se karwaiye", "Bills never scanned: %d — ask reception"),
    "s708_now_wrong": ("%d scan galat dealer ke naam — dealer badliye", "Under the wrong dealer: %d — change the dealer"),
    "s708_now_lost": ("%d kaagaz reception ko nahi mile", "Papers reception could not find: %d"),
    "s708_now_none": ("Abhi kuch nahi karna ✓", "Nothing to do now ✓"),
    "s708_all": ("Saare scan ek-ek karke dekhiye (%d) ▸", "Check all scans one by one (%d) ▸"),
    "s708_more": ("Baaki %d dekhiye ▸", "Show the other %d ▸"),
    "s708_na_s": ("Der wale upar. Dealer ko call kijiye; maal aaye to “Maal aaya” dabaiye.",
                  "Late ones first. Call the dealer; when the goods come, tap “Goods arrived”."),
    "s708_sh_s": ("Jo dawa nahi aayi, woh agle order mein apne aap jaati hai. Aapko kuch nahi karna.",
                  "What did not come goes on the next order by itself. Nothing to do."),
    "s708_scan_h": ("Scan ki dikkat", "Scan problems"),
    "s708_scan_s": ("Har bill ka ek saaf scan chahiye. Har card par ek tap — kiya hua card par dikhta hai.",
                    "Every bill needs one clear scan. One tap per card — what you did shows on the card."),
    "s708_marg_s": ("Amir Marg mein entry karenge. Aapko kuch nahi karna.", "Amir enters these in Marg. Nothing to do."),
    "s708_done_s": ("Saari dawa aayi, bill scan hua, Marg mein hai.", "Every medicine came, the bill is scanned and in Marg."),
    "s708_lines": ("Dawa dekhiye", "Show medicines"),
    "s708_days": ("%d din se", "%d days"), "s708_today": ("aaj", "today"),
    "s708_big": ("Bada dekhiye ⤢", "View large ⤢"),
    "s708_g_pair": ("Ek bill, do scan", "One bill, two scans"),
    "s708_pair_q": ("Bill %s · kaunsa scan saaf hai? Usi par “Yeh sahi hai” dabaiye — dusra copy maana jayega.",
                    "Bill %s · which scan is clear? Tap “This one is right” on it — the other becomes the copy."),
    "s708_keep": ("Yeh sahi hai", "This one is right"),
    "s708_kept": ("Rakha gaya ✓ %s — %s copy maana gaya.", "Kept ✓ %s — %s is the copy."),
    "s708_kept_ask": (" Uska reception wala kaam bhi hata diya.", " Its rescan request to reception is withdrawn too."),
    "s708_undo": ("Galti hui? Wapas", "Mistake? Undo"),
    "s708_undone": ("Wapas kar diya — page dobara kholiye. Reception wala kaam wapas nahi aata.",
                    "Undone — reload the page to choose again. A rescan request it withdrew stays withdrawn."),
    "s708_both_bad": ("Dono kharab? Reception ko bhejiye:", "Both bad? Send to reception:"),
    "s708_g_redo": ("Dobara scan", "Rescan"),
    "s708_with_rec": ("Reception ke paas · %s", "With reception · %s"),
    "s708_g_nosc": ("Bill ka scan nahi hai", "Bill not scanned"),
    "s708_nosc_l": ("Maal aaya%s — par kaagaz ka scan nahi hua.", "The goods came%s — but the paper was never scanned."),
    "s708_nosc_marg": (", Marg mein hai", " and are in Marg"),
    "s708_ask_rec": ("Reception se scan karwaiye", "Ask reception to scan it"),
    "s708_asked": ("Reception ko bheja ✓ %s", "Sent to reception ✓ %s"),
    "s708_withdraw": ("Wapas lijiye", "Withdraw"),
    "s708_withdrawn": ("Wapas le liya ✓", "Withdrawn ✓"),
    "s708_lost_l": ("Reception: kaagaz nahi mila · %s", "Reception: paper not found · %s"),
    "s708_ask_again": ("Dobara dhoondhwaiye", "Ask again"),
    "s708_g_stale": ("Reception ke paas, par scan aa gaya", "With reception, but the scan has come"),
    "s708_stale_l": ("Is order ka scan dusre raaste se aa gaya — reception wala kaam wapas lijiye.", "This order's scan came another way — withdraw reception's work."),
    "s708_now_stale": ("%d order ka scan aa gaya — reception wala kaam wapas lijiye", "Scan came another way: %d — withdraw reception's work"),
    "s708_now_tie": ("Reception ne %d scan kiye — unka bill chuniye", "Reception scanned %d — pick their bill"),
    "s708_dealer_to": ("%s ✓ — %s ke order se jud gaya.", "%s ✓ — tied to the order of %s."),
    "s708_g_kept": ("Saaf scan chuna gaya (7 din)", "Clear scan picked (7 days)"),
    "s708_older": ("+ %d purane", "+ %d older"),
    "s708_g_wrong": ("Galat dealer ke naam se save", "Saved under the wrong dealer"),
    "s708_pick_d": ("Kaagaz ka dealer pakka nahi padha gaya. Scan dekhkar sahi dealer chuniye:",
                    "The paper's dealer is not read for sure. Open the scan and pick the dealer:"),
    "s708_no_choice": ("Is samay ka koi order nahi mila — Doctor sahab ko bataiye.", "No order of that time to choose from — tell Dr Manoj."),
    "s708_dealer_ok": ("%s ✓ — order se jud gaya.", "%s ✓ — tied to its order."),
    "s708_dealer_ok2": ("%s ✓ — dealer badal diya.", "%s ✓ — the dealer is changed."),
    "s708_conflict": ("Is order ka scan %s kisi aur dealer ka kaagaz hai.", "This order's scan %s is another dealer's paper."),
    "s708_v_close": ("Band kijiye", "Close"), "s708_v_prev": ("◂ Pichhla", "◂ Previous"), "s708_v_next": ("Agla scan ▸", "Next scan ▸"),
    "s708_v_zoom": ("Bada ⊕", "Zoom ⊕"), "s708_v_fit": ("Poora ⊖", "Fit ⊖"), "s708_v_full": ("Poora scan alag kholiye ↗", "Open the full scan ↗"),
    # reception
    "s708_r_title": ("Scan ka kaam", "Scan work"),
    "s708_r_top": ("In bills ka kaagaz dhoondhiye aur scan kijiye. “Scan karo” dabaiye — camera khulega.",
                   "Find these bills' papers and scan them. Tap “Scan” — the camera opens."),
    "s708_r_tag_redo": ("dobara scan", "rescan"), "s708_r_tag_new": ("scan nahi hua", "never scanned"),
    "s708_r_old": ("Pichhla scan:", "Last scan:"), "s708_r_how": ("Kaise karein:", "How:"),
    "s708_r_how_cut": ("Poora bill table par seedha rakhiye. Chaaron kone aur neeche ka total frame mein hon.",
                       "Lay the whole bill flat. All four corners and the total at the bottom inside the frame."),
    "s708_r_how_blur": ("Roshni mein rakhiye, phone hilaiye mat. Scan ke baad akshar saaf dikhne chahiye.",
                        "In good light, hold the phone still. The letters must be sharp after the scan."),
    "s708_r_how_not": ("Sahi kaagaz dhoondhiye — dealer ka bill (challan ya bill), koi aur kaagaz nahi.",
                       "Find the right paper — the dealer's bill (challan or bill), nothing else."),
    "s708_r_how_new": ("%s ki %s ki file mein bill dhoondhiye; poora scan kijiye.", "Find the bill in %s's file of %s; scan the whole paper."),
    "s708_r_new_what": ("Is bill ka kaagaz kabhi scan nahi hua", "This bill's paper was never scanned"),
    "s708_r_bills": ("Bill: %s", "Bill: %s"),
    "s708_r_from": ("Order tracker se · %s · %s", "From the order tracker · %s · %s"),
    "s708_r_lost": ("Kaagaz nahi mila", "Paper not found"),
    "s708_r_lost_ok": ("Shavez aur Doctor sahab ke page par dikh gaya ✓ — kaagaz mile to “Mil gaya” dabaiye.",
                       "It shows on Shavez's and Dr Manoj's page ✓ — when the paper turns up, tap “Found it”."),
    "s708_r_found": ("Mil gaya — scan karna hai", "Found it — scan it"),
    "s708_r_found_ok": ("Theek hai — ab “Scan karo” dabaiye.", "Fine — now tap “Scan”."),
    "s708_r_none": ("Aaj ka scan kaam poora ✓", "No scan work today ✓"),
    "s708_r_done": ("Scan ho gaya ✓", "Scanned ✓"),
    "s708_r_done_ok": ("Shavez ke page par dikh gaya ✓ — woh scan ko order se mila dengi.", "It shows on Shavez's page ✓ — she matches the scan to the order."),
    "s708_scanned_l": ("Reception ne scan kar diya (%s) — kaunsa scan is order ka bill hai?", "Reception scanned it (%s) — which scan is this order's bill?"),
    "s708_this_bill": ("Yeh iska bill hai", "This is its bill"),
    "s708_no_cand": ("Is dealer ka koi naya scan nahi mila.", "No new scan of this dealer was found."),
    "s708_tied_ok": ("%s ✓ — order se jud gaya.", "%s ✓ — tied to the order."),
    "s708_reask": ("Reception ko dobara bhejiye", "Send to reception again"),
    "s708_r_view": ("Pichhla scan dekhiye ↗", "See the last scan ↗"),
}


def _w():
    P4 = _p4()
    if "s708_hint" not in P4.T:
        P4.T.update(WORDS)
    return P4


# ------------------------------------------------------------------ the people's entries (reads fail-soft: a missing table = none)
def picks(con):
    try:
        return [dict(r) for r in con.execute("SELECT id, keep_id, drop_id, picked_by, picked_at FROM s708_scan_pick WHERE undone_at IS NULL ORDER BY id")]
    except sqlite3.Error:
        return []


OPEN_PAPER = ("FROM s708_paper_ask WHERE withdrawn_at IS NULL AND order_id NOT IN (SELECT order_id FROM order_scan_tie) "
              "AND order_id IN (SELECT id FROM purchase_order WHERE status IN ('sent','received'))")
RECEPTION_PAPER = OPEN_PAPER + " AND scanned_at IS NULL"     # reception's list and its home row: the same set, by one rule


def paper_asks(con, reception_only=False):
    """{order_id: the newest open ask} -- open = not withdrawn AND the order has no bill scan tied (the ask closes the moment a scan is
    tied -- by Shavez's or the owner's "This is its bill", or by the S454 tie; nothing is written for that). reception_only: and not yet
    marked "Scan ho gaya" by reception. No scan is ever tied here by itself (S708 R2)."""
    out = {}
    try:
        for r in con.execute("SELECT id, order_id, asked_by, asked_at, scanned_at, scanned_by " + (RECEPTION_PAPER if reception_only else OPEN_PAPER)
                             + " ORDER BY id"):
            out[int(r["order_id"])] = dict(r)
    except sqlite3.Error:
        pass
    return out


def lost_marks(con):
    """{(kind, ref_id): the newest uncleared mark}."""
    out = {}
    try:
        for r in con.execute("SELECT id, kind, ref_id, lost_by, lost_at FROM s708_lost WHERE cleared_at IS NULL ORDER BY id"):
            out[(str(r["kind"]), int(r["ref_id"]))] = dict(r)
    except sqlite3.Error:
        pass
    return out


def _dtm(s):
    try:
        return dt.datetime.fromisoformat(str(s)[:19]) if s else None
    except ValueError:
        return None


def never_scanned(rows, now):
    """The arrived orders with no bill scan at all: in Marg already, or arrived NOSCAN_HOURS ago (S619's rows; nothing stored)."""
    out = []
    for s in rows:
        if not s.get("arrived") or s.get("scans"):
            continue
        at = s.get("arrived_at")
        old = False
        try:
            old = bool(at) and (now.replace(tzinfo=None) - at.replace(tzinfo=None)) >= dt.timedelta(hours=NOSCAN_HOURS)
        except (AttributeError, TypeError):
            old = False
        if s.get("in_marg") or old:
            out.append(s)
    return out


def dealer_choices(con, ctx, sid):
    """[(supplier key, the name as ordered)] -- the dealers of the orders made in the 7 days before the scan, newest first, and the dealer it
    was saved under: the server's own list for the 'pick the dealer' door (never the browser's). At most 6."""
    OT = _ot()
    pa = OT._pa()
    s = ctx.scans.get(int(sid)) or {}
    at = s.get("at")
    out, seen = [], set()
    if at is not None:
        lo = (at - dt.timedelta(days=7)).replace(microsecond=0).isoformat()
        try:
            for r in con.execute("SELECT vendor FROM purchase_order WHERE status IN ('sent','received') AND created_at<=? AND created_at>=? "
                                 "ORDER BY created_at DESC, id DESC", (at.replace(microsecond=0).isoformat(), lo)):
                k = pa.supplier_key(r[0] or "")
                if k and k not in seen:
                    seen.add(k)
                    out.append((k, str(r[0])))
        except sqlite3.Error:
            pass
    k = pa.supplier_key(s.get("vendor") or "")
    if k and k not in seen:
        out.append((k, str(s.get("vendor"))))
    return out[:6]


# ------------------------------------------------------------------ the model: every list from its one reader
def model(con, en, now=None):
    OT, OS, P4 = _ot(), _os(), _w()
    now = now or OS.now()
    rows = OT.light_all(con, now)
    ctx = OT.Ctx(con)
    OT.full_all(con, now, en=en, ctx=ctx, rows=rows)
    redo = getattr(ctx, "redo", None) or dict(asks=[], redo=[])
    redo = dict(redo, redo=[r for r in redo.get("redo") or [] if ctx.head(r["scan"]) == int(r["scan"])])     # as S628 (F-992)
    wd = [w for w in OT.wrong_dealer(con, ctx) if int(w["scan"]) not in getattr(ctx, "dropped", ())]
    wd_ids = {int(w["scan"]) for w in wd}
    pairs = OT.same_paper(con, ctx, asked_too=True)
    nosc = never_scanned(rows, now)
    nosc_ids = {s["id"] for s in nosc}
    conflict = [s for s in rows if s.get("scan_conflict") and not any(int(x.get("head") or x["scan"]) in wd_ids for x in s.get("scans") or [])]
    conf_ids = {s["id"] for s in rows if s.get("scan_conflict")}
    na = sorted([s for s in rows if s["key"] in ("not_arrived", "part")], key=lambda s: (0 if s["late"] else 1, s["created_at"]))
    nm = [s for s in rows if s["key"] == "awaiting"]
    sh = [s for s in rows if s["short"]]
    done = [s for s in rows if s["complete"] and s["id"] not in nosc_ids and s["id"] not in conf_ids]
    done.sort(key=lambda s: s["created_at"], reverse=True)
    asked = {int(a["scan"]): int(a["id"]) for a in redo.get("asks") or []}
    pask = paper_asks(con)
    lost = lost_marks(con)
    stale = [dict(ask, order_id=oid) for oid, ask in pask.items() if oid not in nosc_ids]     # R3: the order has its scan another way (Marg's link)
    lo = (now - dt.timedelta(days=PICK_DAYS)).replace(microsecond=0).isoformat()
    kept = [p for p in picks(con) if str(p.get("picked_at") or "") >= lo]
    return dict(now=now, stale=stale, rows=rows, ctx=ctx, redo=redo, wd=wd, pairs=pairs, kept=kept, nosc=nosc, conflict=conflict, na=na, nm=nm, sh=sh, done=done,
                asked=asked, pask=pask, lost=lost, marg=OT._marg_items(con), since=OT.since(con))


# ------------------------------------------------------------------ drawing
CSS = """
.wrap{max-width:1240px}
.s7top{display:flex;flex-direction:column;gap:10px}
.s7chips{display:flex;flex-wrap:wrap;gap:8px}
.s7chip{display:flex;align-items:center;gap:8px;min-height:44px;padding:6px 12px;background:#fff;border:1px solid #e4e0da;border-radius:22px;color:#1c1c1c;text-decoration:none;font-size:15px}
.s7chip b{font-size:18px}
.s7two{display:flex;gap:8px}.s7two>*{flex:1 1 0}
.s7btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 14px;border-radius:10px;background:#fff;color:#1f3864;border:1px solid #1f3864;font:700 15px system-ui,sans-serif;text-decoration:none;cursor:pointer}
.s7btn.g{background:#2e6b34;border-color:#2e6b34;color:#fff}.s7btn.n{background:#1f3864;color:#fff}
.s7btn.q{background:#f6f4f1;border-color:#c9c4bc;color:#1f3864;font-weight:600;font-size:14px;min-height:40px}
.s7btn[disabled]{opacity:.5;cursor:default}
.s7now{background:#fff8e8;border:1px solid #e8d3a3;border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:6px}
.s7now a{color:#1c1c1c;text-decoration:none;font-size:15.5px;min-height:32px;display:flex;gap:8px;align-items:baseline}
.s7cols{display:grid;grid-template-columns:minmax(0,1fr);gap:12px}
.s7col{display:flex;flex-direction:column;gap:12px;min-width:0}
@media (min-width:900px){.s7cols{grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;align-items:start}.s7wide{grid-column:1 / -1}}
details.s7sec{background:#fff;border:1px solid #e4e0da;border-radius:12px;overflow:hidden}
details.s7sec>summary{list-style:none;display:flex;align-items:center;gap:10px;min-height:56px;padding:10px 14px;cursor:pointer;font-weight:700;font-size:18px}
details.s7sec>summary::-webkit-details-marker{display:none}
details.s7sec>summary .dot{width:12px;height:12px;border-radius:6px;flex:0 0 auto}
details.s7sec>summary .t{flex:1 1 auto}
details.s7sec>summary .c{min-width:30px;height:30px;padding:0 8px;border-radius:15px;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:16px}
details.s7sec>summary .ch{font-size:18px;color:#4f4f4f;width:18px;text-align:center}
details.s7sec>summary .ch::before{content:"\\25B8"}details.s7sec[open]>summary .ch::before{content:"\\25BE"}
details.s7sec[open]>summary{border-bottom:1px solid #ece8e2}
.s7body{padding:10px 14px 14px;display:flex;flex-direction:column;gap:10px}
.s7s{font-size:14.5px;color:#4f4f4f}
.s7g{font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#4f4f4f;margin-top:4px}
.s7c{border:1px solid #e4e0da;border-radius:10px;padding:10px 12px;display:flex;flex-direction:column;gap:8px}
.s7c .h{display:flex;justify-content:space-between;gap:8px;align-items:baseline}.s7c .h b{font-size:17px}
.s7tag{font-size:13px;font-weight:700;color:#fff;background:#b3261e;border-radius:6px;padding:2px 8px;white-space:nowrap}
.s7red{color:#b3261e;font-weight:600}.s7amb{color:#8a5300;font-weight:600}.s7grn{color:#1f4d24;font-weight:700}
.s7ok{background:#e4f2e6;border:1px solid #2e6b34;border-radius:10px;padding:10px 12px;font-weight:700;color:#1f4d24;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.s7warn{background:#fff8e8;border:1px solid #e8d3a3;border-radius:10px;padding:10px 12px;font-weight:600;color:#8a5300}
.s7err{color:#b3261e;font-weight:600;font-size:14.5px}
.s7th{display:flex;gap:12px;align-items:flex-start}
.s7th img{width:70px;height:92px;object-fit:cover;border:1px solid #ccc;border-radius:4px;flex:0 0 auto;background:#fff}
.s7pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.s7pair>div{display:flex;flex-direction:column;gap:6px;align-items:stretch}
.s7pair img{width:100%;height:150px;object-fit:contain;border:1px solid #ccc;border-radius:6px;background:#fff}
.s7row{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:8px 0;border-bottom:1px solid #f0ece6;font-size:15px}
.s7row:last-child{border-bottom:0}
.s7dots{display:flex;flex-wrap:wrap;gap:4px 8px;font-size:12.5px;color:#3d3d3d}
.s7dots span{display:inline-flex;align-items:center;gap:4px}.s7dots i{display:inline-block;width:10px;height:10px;border-radius:5px}
details.s7more>summary{list-style:none;cursor:pointer;min-height:44px;display:flex;align-items:center;justify-content:center;border-radius:10px;background:#f6f4f1;border:1px solid #e4e0da;color:#1f3864;font-weight:700}
details.s7more>summary::-webkit-details-marker{display:none}
details.s7more[open]>summary{margin-bottom:10px}
details.s7more>div{display:flex;flex-direction:column;gap:10px}
details.s7l>summary{cursor:pointer;color:#1f3864;font-weight:600;font-size:14.5px;min-height:32px;display:flex;align-items:center}
.s7up{position:fixed;right:16px;bottom:16px;z-index:10;display:flex;align-items:center;gap:6px;min-height:52px;padding:0 16px;border-radius:26px;background:#1f3864;color:#fff;font:700 15px system-ui,sans-serif;text-decoration:none;box-shadow:0 3px 10px rgba(0,0,0,.25)}
#s7v{position:fixed;left:0;right:0;top:0;bottom:0;z-index:40;background:#fff;display:none;flex-direction:column}
#s7v.on{display:flex}
#s7v .vh{display:flex;align-items:center;gap:8px;background:#1f3864;color:#fff;padding:6px 10px;min-height:56px}
#s7v .vh .vt{flex:1 1 auto;min-width:0;font-weight:600;font-size:15px}
#s7v .vh button{min-height:44px;min-width:44px;padding:0 12px;border-radius:9px;border:1px solid #fff;background:transparent;color:#fff;font:600 14px system-ui,sans-serif;cursor:pointer}
#s7v .vb{flex:1 1 auto;overflow:auto;background:#eceae6;padding:12px;display:flex;flex-direction:column;gap:12px}
#s7v .vimg{display:flex;justify-content:center}
#s7v .vimg img{max-width:100%;height:auto;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.15)}
#s7v .vimg iframe{width:100%;height:78vh;border:0;background:#fff}
#s7v.zoom .vimg img{max-width:none;width:180%}
#s7v .vact{background:#fff;border:1px solid #e4e0da;border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:10px}
#s7v .vf{display:flex;gap:8px;padding:10px;border-top:1px solid #e4e0da;background:#fff}#s7v .vf button{flex:1 1 0;min-height:52px}
@media (min-width:900px){#s7v{left:auto;width:62vw;max-width:1000px;box-shadow:-6px 0 24px rgba(0,0,0,.16)}
 body.s7vo .wrap{margin-right:min(62vw,1000px);max-width:none}body.s7vo .s7cols{grid-template-columns:minmax(0,1fr)}
 body.s7vo .s7up{right:calc(min(62vw,1000px) + 16px)}#s7v .vimg iframe{height:calc(100vh - 260px)}}
@media (max-width:899px){#s7v .vimg iframe{display:none}#s7v #s7vfull{background:#1f3864;color:#fff;border-color:#1f3864;min-height:48px;font-size:15px}}
"""

JS = r"""
function s7sec(){return Array.prototype.slice.call(document.querySelectorAll('details.s7sec'));}
function s7save(){try{sessionStorage.setItem(location.pathname+'#s7',JSON.stringify(s7sec().filter(function(d){return d.open;}).map(function(d){return d.id;})));}catch(e){}}
function s7all(on){s7sec().forEach(function(d){d.open=on;});s7save();}
function s7go(id){var d=document.getElementById(id);if(d){d.open=true;s7save();d.scrollIntoView({behavior:'smooth',block:'start'});}return false;}
document.addEventListener('DOMContentLoaded',function(){
 try{var o=JSON.parse(sessionStorage.getItem(location.pathname+'#s7')||'[]');o.forEach(function(id){var d=document.getElementById(id);if(d)d.open=true;});}catch(e){}
 s7sec().forEach(function(d){d.addEventListener('toggle',s7save);});
});
async function s7act(btn,url,body){
 var card=document.querySelector('[data-card="'+btn.getAttribute('data-for')+'"]');
 btn.disabled=true;
 try{var r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
  var j=await r.json().catch(function(){return {};});
  if(!r.ok||!j.ok){btn.disabled=false;s7msg(card,j.message||j.error||('HTTP '+r.status));return;}
  if(card){var a=card.querySelector('.acts');if(a){if(j.html){a.innerHTML=j.html;}else{a.innerHTML='';var o=document.createElement('div');o.className='s7ok';o.textContent=btn.getAttribute('data-ok')||'✓';a.appendChild(o);}}card.setAttribute('data-done','1');}
  s7vfill();
 }catch(e){btn.disabled=false;s7msg(card,String(e));}
}
function s7msg(card,m){var a=card&&card.querySelector('.acts');var d=document.createElement('div');d.className='s7err';d.textContent=m;
 if(a){a.appendChild(d);}else{var g=document.getElementById('msg');if(g){g.textContent=m;g.style.display='block';}}s7vfill();}
var S7V={q:[],i:-1,el:null};
function s7q(){return Array.prototype.slice.call(document.querySelectorAll('[data-vq]'));}
function s7open(el){S7V.q=s7q();S7V.el=el;S7V.i=S7V.q.indexOf(el);var v=document.getElementById('s7v');v.classList.add('on');v.classList.remove('zoom');
 document.body.classList.add('s7vo');s7vfill();return false;}
function s7all1(){var q=s7q();if(q.length){var sec=q[0].closest('details.s7sec');if(sec&&!sec.open){sec.open=true;s7save();}s7open(q[0]);}return false;}
function s7close(){document.getElementById('s7v').classList.remove('on');document.body.classList.remove('s7vo');S7V.el=null;}
function s7step(k){if(!S7V.q.length)return;var i=S7V.i<0?0:(S7V.i+k+S7V.q.length)%S7V.q.length;S7V.i=i;S7V.el=S7V.q[i];
 var sec=S7V.el.closest('details');while(sec){sec.open=true;sec=sec.parentElement&&sec.parentElement.closest('details');}s7vfill();}
function s7zoom(){var v=document.getElementById('s7v');v.classList.toggle('zoom');document.getElementById('s7vz').textContent=v.classList.contains('zoom')?v.getAttribute('data-fit'):v.getAttribute('data-zoom');}
function s7vfill(){var v=document.getElementById('s7v');if(!v||!v.classList.contains('on')||!S7V.el)return;var el=S7V.el;
 document.getElementById('s7vpos').textContent=S7V.i>=0?(S7V.i+1)+' / '+S7V.q.length:'';
 document.getElementById('s7vt').textContent=el.getAttribute('data-vt')||'';
 var box=document.getElementById('s7vimg'),f=el.getAttribute('data-vf'),th=el.getAttribute('data-vth'),pdf=el.getAttribute('data-vpdf')==='1';
 if(box.getAttribute('data-src')!==f){box.setAttribute('data-src',f);box.innerHTML='';
  if(pdf&&window.matchMedia('(min-width:900px)').matches){var fr=document.createElement('iframe');fr.src=f+'#view=FitH';fr.title=el.getAttribute('data-vt')||'scan';box.appendChild(fr);}
  else if(pdf){var im=document.createElement('img');im.src=th;im.alt='';im.className='s7vth';box.appendChild(im);}
  else{var im2=document.createElement('img');im2.src=f;im2.alt=el.getAttribute('data-vt')||'scan';box.appendChild(im2);}}
  document.getElementById('s7vfull').href=f;
 var card=el.closest('[data-card]'),act=document.getElementById('s7vact');act.innerHTML='';
 if(card){var p=card.querySelector('.vp');if(p){var c=p.cloneNode(true);act.appendChild(c);}var a=card.querySelector('.acts');if(a){act.appendChild(a.cloneNode(true));}}
 var nav=S7V.i>=0&&S7V.q.length>1;document.getElementById('s7vprev').style.visibility=nav?'visible':'hidden';document.getElementById('s7vnext').style.visibility=nav?'visible':'hidden';}
document.addEventListener('keydown',function(e){var v=document.getElementById('s7v');if(!v||!v.classList.contains('on'))return;
 var tg=e.target&&e.target.tagName;if(tg==='INPUT'||tg==='TEXTAREA')return;
 if(e.key==='Escape')s7close();else if(e.key==='ArrowRight')s7step(1);else if(e.key==='ArrowLeft')s7step(-1);});
"""


def _e(s):
    return _p4().esc(s)


def _L(en, k, *a):
    return _w().L(en, k, *a)


def _ddmm(iso):
    return _os().ddmm(iso)


def _ago(en, iso, now):
    d = _dtm(iso)
    if not d:
        return ""
    try:
        n = (now.replace(tzinfo=None).date() - d.date()).days
    except (AttributeError, TypeError):
        return ""
    return _L(en, "s708_today") if n <= 0 else _L(en, "s708_days", n)


def _is_pdf(ctx, sid):
    s = ctx.scans.get(int(sid)) or {}
    return str(s.get("source_stored") or "").lower().endswith(".pdf")


def _vattrs(ctx, sid, title, queue=True, thumb=None):
    """The viewer's attributes on a 'View large' button: the scan's file, its thumb, PDF or not, the title; data-vq = in 'Check all'."""
    sid = int(sid)
    return ('data-vf="/scanapp/bills/%d/file" data-vth="%s" data-vpdf="%d" data-vt="%s"%s'
            % (sid, _e(thumb or ("/scanapp/bills/%d/thumb" % sid)), 1 if _is_pdf(ctx, sid) else 0, _e(title), ' data-vq="1"' if queue else ""))


def _bigbtn(en, ctx, sid, title, queue=True, thumb=None):
    return '<button type="button" class="s7btn q" %s onclick="return s7open(this)">%s</button>' % (_vattrs(ctx, sid, title, queue, thumb), _L(en, "s708_big"))


def _act(en, key, label, url, body, cls="", ok=""):
    """A door's button: posts body to url; the card's .acts then shows the server's html (or ok, for the older doors that send none)."""
    return ('<button type="button" class="s7btn %s" data-for="%s" data-ok="%s" onclick="s7act(this,\'%s\',%s)">%s</button>'
            % (cls, _e(key), _e(ok), P + url, _e(json.dumps(body)), _e(label)))


def _sec(sid, title, n, dot, cbg, cfg, body, wide=False):
    return ('<details class="s7sec%s" id="%s"><summary><span class="dot" style="background:%s"></span><span class="t">%s</span>'
            '<span class="c" style="background:%s;color:%s">%d</span><span class="ch" aria-hidden="true"></span></summary><div class="s7body">%s</div></details>'
            % (" s7wide" if wide else "", sid, dot, _e(title), cbg, cfg, n, body))


def _first(cards, en, k=3):
    if len(cards) <= k:
        return "".join(cards)
    return "".join(cards[:k]) + '<details class="s7more"><summary>%s</summary><div>%s</div></details>' % (_L(en, "s708_more", len(cards) - k), "".join(cards[k:]))


def _dots(en, s):
    P4, OT = _p4(), _ot()
    out = []
    for name, st in OT.dots(s):
        out.append('<span data-step="%s" data-state="%s"><i style="background:%s"></i>%s</span>'
                   % (_e(name), st, P4.S619_DOT.get(st, "#c9c4bc"), _e(name if en else P4.S619_STEP_HI.get(name, name))))
    return '<div class="s7dots">%s</div>' % "".join(out)


def _sub(en, s):
    P4, OS = _p4(), _os()
    sub = [P4._s619_via(en, s["via"])]
    if s.get("sent_at"):
        d = OS._dtm(s["sent_at"])
        sub.append(P4.L(en, "sent_ph", d.strftime("%H:%M") if d else ""))
    sub.append(P4.L(en, "dawa", s["n"]))
    if s["part"] or (s["arrived"] and s["came"] and s["came"] < s["n"]):
        sub.append(P4.L(en, "of_came", *((s["came"], s["n"]) if en else (s["n"], s["came"]))))
    if s["arrived"] and s["n"] and not s["came"] and s["short"] == s["n"]:
        sub.append(P4.L(en, "none_came"))
    if not s["arrived"] and not s["late"] and s.get("due_at"):
        sub.append(P4.L(en, "due_w", s["due_at"].strftime("%d-%m")))
    return " · ".join(sub)


def _when(s):
    return s["created"].strftime("%d-%m %H:%M") if s.get("created") else _ddmm(s["created_at"])


def _lines(con, en, s, marg, only=None):
    OT, P4 = _ot(), _p4()
    li = []
    for x in s["lines"]:
        st = x["state"]
        if only and st not in only:
            continue
        if st == "short":
            w, cls = "%s · %s" % (P4.L(en, "nm_short", x["item"], x["short_text"]), OT.short_words(con, s, x, en, marg)), "s7red"
        elif st in ("open", "part"):
            w, cls = "%s · %s%s" % (x["item"], P4.L(en, "awaited_w"), (" (%s)" % x["short_text"]) if st == "part" else ""), "s7amb"
        elif st == "awaiting":
            w, cls = x["item"], ""
        else:
            w, cls = "%s ✓" % x["item"], "s7grn"
        notes = "".join(" · %s" % _e(OT.W(k, en, *a)) for k, a in x.get("notes") or [])
        li.append('<div data-line="%d" data-state="%s"><span class="%s">%s</span><span class="s7amb">%s</span></div>' % (x["id"], st, cls, _e(w), notes))
    return "".join(li)


def _call(con, en, s):
    P4, OS = _p4(), _os()
    call, _wa, _shown, _on = OS.book_card(con, s["vendor"])
    if not call:
        return '<span class="s7amb">%s</span>' % P4.L(en, "nonum")
    return ('<a class="s7btn" href="tel:%s" onclick="s454(\'%s/api/s454/call\',{sn:%s},function(){})">📞 %s</a>'
            % (_e(P4._tel(call)), P, _e(json.dumps(s["sn"])), P4.L(en, "call")))


def _card_na(con, en, m, s, asker):
    P4 = _p4()
    late = '<span class="s7tag">%s</span>' % P4.L(en, "late_w") if s["late"] else ""
    lines = _lines(con, en, s, m["marg"])
    acts = ""
    if asker:
        acts = '<div class="s7two">%s<a class="s7btn g" href="%s/s454/maal/%d">%s</a></div>' % (
            _call(con, en, s), P, s["id"], P4.L(en, "baaki_aaya" if s["part"] else "maal_aaya"))
    return ('<div class="s7c" data-order="%d" data-key="%s"><div class="h"><b>%s · %s</b>%s</div><div class="s7s">%s</div>%s'
            '<details class="s7l"><summary>%s</summary><div class="s7s">%s</div></details>%s</div>'
            % (s["id"], s["key"], _e(s["vendor"]), _e(_when(s)), late, _e(_sub(en, s)), _dots(en, s), _L(en, "s708_lines"), lines, acts))


def _card_short(con, en, m, s):
    rest = _lines(con, en, s, m["marg"], only=("came", "awaiting", "open", "part"))
    big = ""
    if s.get("scans") and s.get("thumb"):
        h = int(s["scans"][0].get("head") or s["scans"][0]["scan"])
        big = _bigbtn(en, m["ctx"], h, "%s · %s" % (s["vendor"], _when(s)), queue=False, thumb=s["thumb"])
    return ('<div class="s7c" data-order="%d"><div class="h"><b>%s · %s</b></div><div class="s7s">%s</div><div>%s</div>'
            '<details class="s7l"><summary>%s</summary><div class="s7s">%s</div></details>%s</div>'
            % (s["id"], _e(s["vendor"]), _e(_when(s)), _e(_sub(en, s)), _lines(con, en, s, m["marg"], only=("short",)), _L(en, "s708_lines"), rest, big))


def _row(en, m, s, right):
    return '<div class="s7row" data-order="%d"><span>%s · %s</span><span>%s</span></div>' % (s["id"], _e(s["vendor"]), _e(_ddmm(s["created_at"])), right)


def _stamps(s):
    return ", ".join(x.get("head_stamp") or x.get("stamp") or "" for x in s.get("scans") or [])


# ---- the scan section's cards (each data-card = its own key; .vp = what the viewer shows; .acts = what changes after a tap)
def _pair_card(en, m, p, asker):
    ctx = m["ctx"]
    key = "pair-%d-%d" % (p["a"], p["b"])
    vend = (ctx.scans.get(int(p["a"])) or {}).get("vendor") or ""
    cols, acts = [], []
    for me, other, st in ((p["a"], p["b"], p["sa"]), (p["b"], p["a"], p["sb"])):
        sc = ctx.scans.get(int(me)) or {}
        at = sc.get("at")
        cols.append('<div><img loading="lazy" src="/scanapp/bills/%d/thumb" alt="%s"><div class="s7s"><b>%s</b>%s</div>%s</div>'
                    % (int(me), _e(st), _e(st), (" · " + at.strftime("%d-%m %H:%M")) if at else "",
                       _bigbtn(en, ctx, me, "%s · %s · %s" % (st, vend, p["bill"]))))
        if asker:
            acts.append(_act(en, key, "%s: %s" % (st, _L(en, "s708_keep")), "/api/s454/s708/pick", {"keep": int(me), "drop": int(other)}))
    bad = ""
    if asker:
        bad = ('<details class="s7l"><summary>%s</summary><div class="s7s">%s %s · %s %s</div></details>'
               % (_L(en, "s708_both_bad"), _e(p["sa"]), _p4()._s628_chips(en, p["a"]), _e(p["sb"]), _p4()._s628_chips(en, p["b"])))
    return ('<div class="s7c" data-card="%s" data-pair="%d-%d"><div class="h"><b>%s</b></div><div class="vp s7s">%s</div><div class="s7pair">%s</div>'
            '<div class="acts"><div class="s7two">%s</div>%s</div></div>'
            % (key, p["a"], p["b"], _e(vend), _e(_L(en, "s708_pair_q", p["bill"])), "".join(cols), "".join(acts), bad))


def _redo_ask_card(en, m, a, asker):
    P4, ctx = _p4(), m["ctx"]
    sq = P4._sq()
    key = "ask-%d" % a["id"]
    why = sq.words(a.get("reason"), "owner" if en else "shavez") if sq else a.get("reason")
    lost = m["lost"].get(("rescan", int(a["id"])))
    st = '<div class="s7amb">%s</div>' % _e(_L(en, "s708_with_rec", _ago(en, a.get("asked_at"), m["now"])))
    acts = ""
    if lost:
        st = '<div class="s7warn">%s</div>' % _e(_L(en, "s708_lost_l", _ddmm(lost["lost_at"])))
        if asker:
            acts = _act(en, key, _L(en, "s708_ask_again"), "/api/s454/s708/lost/clear", {"id": int(lost["id"])}, "g")
    if asker:
        acts += _act(en, key, _L(en, "s708_withdraw"), "/api/s454/rescan/withdraw", {"id": int(a["id"])}, ok=_L(en, "s708_withdrawn"))
    title = " · ".join(x for x in (a.get("stamp") or "", a.get("vendor") or "", _ddmm(a.get("date") or "")) if x)
    return ('<div class="s7c" data-card="%s" data-ask="%d" data-scan="%d"><div class="s7th"><img loading="lazy" src="%s" alt="">'
            '<div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:4px"><b>%s</b><div class="vp"><div class="s7red">%s</div>%s</div>%s</div></div>'
            '<div class="acts s7two">%s</div></div>'
            % (key, a["id"], a["scan"], _e(P4._s618_thumb(a)), _e(title), _e(why), st, _bigbtn(en, ctx, a["scan"], title), acts))


def _redo_card(en, m, r, asker):
    P4, ctx = _p4(), m["ctx"]
    sq = P4._sq()
    key = "redo-%d" % r["scan"]
    why = sq.words(r["code"], "owner" if en else "shavez", r["sum"], r["total"]) if sq else r["code"]
    title = "%s · %s · %s" % (r["stamp"], r["vendor"], _ddmm(r["date"]))
    acts = ""
    if asker and sq:
        acts = '<div class="s7s">%s</div><div style="display:flex;flex-wrap:wrap;gap:6px">%s</div>' % (P4.L(en, "send_back"), "".join(
            _act(en, key, sq.CHIP_WORDS[c][0 if en else 1], "/api/s454/rescan", {"asset_bill_id": int(r["scan"]), "reason": c}, ok=P4.L(en, "sent_back"))
            for c in sq.CHIPS))
    return ('<div class="s7c" data-card="%s" data-scan="%d" data-code="%s"><div class="s7th"><img loading="lazy" src="%s" alt="">'
            '<div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:4px"><b>%s</b><div class="vp s7red">%s</div>%s</div></div>'
            '<div class="acts">%s</div></div>'
            % (key, r["scan"], _e(r["code"]), _e(P4._s618_thumb(r)), _e(title), _e(why), _bigbtn(en, ctx, r["scan"], title), acts))


def _nosc_card(con, en, m, s, asker):
    key = "nosc-%d" % s["id"]
    ask = m["pask"].get(s["id"])
    lost = m["lost"].get(("paper", int(ask["id"]))) if ask else None
    line = _L(en, "s708_nosc_l", _L(en, "s708_nosc_marg") if s.get("in_marg") else "")
    bills = (" · " + _L(en, "s708_r_bills", ", ".join(s["bills"]))) if s.get("bills") else ""
    if lost:
        acts = '<div class="s7warn">%s</div>' % _e(_L(en, "s708_lost_l", _ddmm(lost["lost_at"])))
        if asker:
            acts += _act(en, key, _L(en, "s708_ask_again"), "/api/s454/s708/lost/clear", {"id": int(lost["id"])}, "g")
    elif ask and ask.get("scanned_at"):                      # S708 R2: reception has scanned it -- a person says which scan is this bill
        cand = candidates(con, m["ctx"], ask, s["vendor"])
        acts = '<div class="s7amb">%s</div>' % _e(_L(en, "s708_scanned_l", _ddmm(ask["scanned_at"])))
        if cand:
            for sid in cand:
                sc = m["ctx"].scans.get(sid) or {}
                st = sc.get("stamp_no") or "#%d" % sid
                acts += ('<div class="s7th" style="align-items:center"><img loading="lazy" src="/scanapp/bills/%d/thumb" alt=""><div style="display:flex;flex-direction:column;gap:6px">'
                         '<b>%s · %s</b>%s%s</div></div>' % (sid, _e(st), _e(sc["at"].strftime("%d-%m %H:%M") if sc.get("at") else ""),
                                                             _bigbtn(en, m["ctx"], sid, "%s · %s" % (st, s["vendor"])),
                                                             _act(en, key, _L(en, "s708_this_bill"), "/api/s454/s708/paper/tie", {"id": int(ask["id"]), "scan": sid}, "g")
                                                             if asker else ""))
        else:
            acts += '<div class="s7s">%s</div>' % _e(_L(en, "s708_no_cand"))
        if asker:
            acts += '<div class="s7two">%s%s</div>' % (_act(en, key, _L(en, "s708_reask"), "/api/s454/s708/paper/reask", {"id": int(ask["id"])}),
                                                       _act(en, key, _L(en, "s708_withdraw"), "/api/s454/s708/paper/withdraw", {"id": int(ask["id"])}))
    elif ask:
        acts = '<div class="s7ok">%s%s</div>' % (_e(_L(en, "s708_asked", _ddmm(ask["asked_at"]))),
                                               _act(en, key, _L(en, "s708_withdraw"), "/api/s454/s708/paper/withdraw", {"id": int(ask["id"])}) if asker else "")
    else:
        acts = _act(en, key, _L(en, "s708_ask_rec"), "/api/s454/s708/paper", {"order": int(s["id"])}, "g") if asker else ""
    meds = ", ".join(x["item"] for x in s.get("lines") or [])
    return ('<div class="s7c" data-card="%s" data-nosc="%d"><div class="h"><b>%s · %s</b></div><div class="vp"><div class="s7amb">%s</div><div class="s7s">%s</div></div>'
            '<div class="s7s">%s%s</div><div class="acts">%s</div></div>'
            % (key, s["id"], _e(s["vendor"]), _e(_ddmm(s["created_at"])), _e(line), _e(meds), _e(_sub(en, s)), _e(bills), acts))


def _wrong_card(con, en, m, w, asker):
    OT, ctx = _ot(), m["ctx"]
    key = "wrong-%d" % w["scan"]
    pk = OT.paper_dealer(con, ctx, w["scan"])
    title = "%s · %s" % (w["stamp"], _ddmm(w["date"]))
    say = ("saved as %s; the paper says %s" if en else "%s ke naam se save; kaagaz par %s") % (w["saved"], w["paper"])
    acts = ""
    if asker and pk:
        acts = _act(en, key, _p4().L(en, "fix_dealer", pk), "/api/s454/dealer_fix", {"scan": int(w["scan"])}, "g", ok=_L(en, "s708_dealer_ok2", pk))
    elif asker:
        ch = dealer_choices(con, ctx, w["scan"])
        if ch:
            acts = '<div class="s7s">%s</div><div style="display:flex;flex-wrap:wrap;gap:6px">%s</div>' % (_L(en, "s708_pick_d"), "".join(
                _act(en, key, name, "/api/s454/s708/dealer", {"scan": int(w["scan"]), "dealer": k}) for k, name in ch))
        else:
            acts = '<div class="s7amb">%s</div>' % _L(en, "s708_no_choice")
    return ('<div class="s7c" data-card="%s" data-wrong="%d"><div class="s7th"><img loading="lazy" src="/scanapp/bills/%d/thumb" alt="">'
            '<div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:4px"><b>%s</b><div class="vp s7s">%s</div>%s</div></div>'
            '<div class="acts">%s</div></div>' % (key, w["scan"], int(w["scan"]), _e(title), _e(say), _bigbtn(en, ctx, w["scan"], title), acts))


def _kept_card(en, m, p, asker):
    ctx = m["ctx"]
    key = "kept-%d" % p["id"]
    k, d = int(p["keep_id"]), int(p["drop_id"])
    sk = (ctx.scans.get(k) or {}).get("stamp_no") or "#%d" % k
    sd = (ctx.scans.get(d) or {}).get("stamp_no") or "#%d" % d
    vend = (ctx.scans.get(k) or {}).get("vendor") or ""
    undo = _act(en, key, _L(en, "s708_undo"), "/api/s454/s708/pick/undo", {"id": int(p["id"])}) if asker else ""
    return ('<div class="s7c" data-card="%s" data-kept="%d"><div class="s7th"><img loading="lazy" src="/scanapp/bills/%d/thumb" alt="">'
            '<div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:4px"><b>%s</b><div class="vp s7grn">%s</div><div class="s7s">%s</div>%s</div></div>'
            '<div class="acts">%s</div></div>'
            % (key, p["id"], k, _e(vend), _e(_L(en, "s708_kept", sk, sd)), _e(_ddmm(p.get("picked_at")) + " · " + str(p.get("picked_by") or "")),
               _bigbtn(en, ctx, k, "%s · %s" % (sk, vend), queue=False), undo))


def _conflict_card(en, m, s):
    x = (s.get("scans") or [{}])[0]
    h = int(x.get("head") or x.get("scan") or 0)
    st = x.get("head_stamp") or x.get("stamp") or ""
    big = _bigbtn(en, m["ctx"], h, "%s · %s" % (st, s["vendor"])) if h else ""
    return ('<div class="s7c" data-card="conf-%d" data-conflict="%d"><div class="h"><b>%s · %s</b></div><div class="vp s7amb">%s</div>%s<div class="acts"></div></div>'
            % (s["id"], s["id"], _e(s["vendor"]), _e(_ddmm(s["created_at"])), _e(_L(en, "s708_conflict", st)), big))


def _names(con, en, kind):
    """The owner's 'Names to confirm' (med_names, S628 D761) -- as S619 drew it, in a folded section of its own."""
    if kind != "owner":
        return ""
    P4 = _p4()
    try:
        import med_names                                      # noqa: PLC0415
        qs = med_names.questions(con)
    except Exception:                                         # noqa: BLE001
        return ""
    if not qs:
        return ""
    cards = "".join('<div class="s7c" data-nameq="%d"><div><b>%s</b></div><div class="s7two">'
                    '<button class="s7btn g" onclick="s454(\'%s/api/s454/name_answer\',{id:%d,yes:1})">%s</button>'
                    '<button class="s7btn" onclick="s454(\'%s/api/s454/name_answer\',{id:%d,yes:0})">%s</button></div></div>'
                    % (q["id"], _e(med_names.question_text(q, True)), P, q["id"], P4.L(en, "q_yes"), P, q["id"], P4.L(en, "q_no")) for q in qs)
    return _sec("sec_names", P4.L(en, "s_names"), len(qs), "#1f3864", "#e6ebf4", "#1f3864", cards, wide=True)


def page(con, u, kind, login, en):
    """The order list (S708). The caller (porders_s454.track_page) has checked the login; this draws and writes nothing."""
    P4 = _w()
    asker = P4._s618_asker(con, kind, login)
    m = model(con, en)
    rows, ctx = m["rows"], m["ctx"]
    late = [s for s in m["na"] if s["late"]]
    asks, redo = m["redo"].get("asks") or [], m["redo"].get("redo") or []
    nosc_open = [s for s in m["nosc"] if s["id"] not in m["pask"]]
    nosc_ids = {s["id"] for s in m["nosc"]}
    open_paper_ids = {int(a["id"]) for oid, a in m["pask"].items() if oid in nosc_ids}
    lost_n = sum(1 for (k, r) in m["lost"] if (k == "rescan" and r in {int(a["id"]) for a in asks}) or (k == "paper" and r in open_paper_ids))
    n_tie = sum(1 for s in m["nosc"] if (m["pask"].get(s["id"]) or {}).get("scanned_at"))
    n_scan = len(m["pairs"]) + len(asks) + len(redo) + len(m["nosc"]) + len(m["wd"]) + len(m["conflict"])
    h = ['<div class="s7top" id="top"><h1 id="trackh" style="margin:4px 0 0">%s</h1><div class="s7s">%s · %s</div>' % (
        P4.L(en, "track"), _e(_L(en, "s708_since", *((len(rows), _ddmm(m["since"])) if en else (_ddmm(m["since"]), len(rows))))), _L(en, "s708_hint"))]
    chips = (("sec_na", len(m["na"]), "#b3261e", P4.L(en, "t_na")), ("sec_short", len(m["sh"]), "#b3261e", P4.L(en, "t_short")),
             ("sec_scan", n_scan, "#8a5300", _L(en, "s708_scan_h").lower()), ("sec_marg", len(m["nm"]), "#1f3864", P4.L(en, "t_marg")))
    h.append('<div class="s7chips" id="tiles">%s</div>' % "".join(
        '<a class="s7chip" data-tile="%s" href="#%s" onclick="return s7go(\'%s\')"><b style="color:%s">%d</b>%s</a>' % (sid, sid, sid, col, n, _e(lab))
        for sid, n, col, lab in chips))
    h.append('<div class="s7two"><button type="button" class="s7btn" onclick="s7all(true)">%s</button><button type="button" class="s7btn" onclick="s7all(false)">%s</button></div>'
             % (_L(en, "s708_exp"), _L(en, "s708_col")))
    if asker:
        todo = []
        for n, k, sid in ((len(late), "s708_now_late", "sec_na"), (len(m["pairs"]), "s708_now_pair", "sec_scan"), (len(redo), "s708_now_redo", "sec_scan"),
                          (len(nosc_open), "s708_now_nosc", "sec_scan"), (n_tie, "s708_now_tie", "sec_scan"), (len(m["wd"]), "s708_now_wrong", "sec_scan"),
                          (lost_n, "s708_now_lost", "sec_scan"), (len(m["stale"]), "s708_now_stale", "sec_scan")):
            if n:
                todo.append('<a href="#%s" onclick="return s7go(\'%s\')"><span class="s7red">›</span>%s</a>' % (sid, sid, _e(_L(en, k, n))))
        h.append('<div class="s7now" id="todo"><b style="font-size:17px">%s</b>%s<!--s708all--></div>' % (_L(en, "s708_now"), "".join(todo) or
                 '<div class="s7grn">%s</div>' % _L(en, "s708_now_none")))
    h.append("</div>")
    nh = _names(con, en, kind)
    if nh:
        h.append('<div class="s7cols">%s</div>' % nh)
    # the sections
    na_cards = [_card_na(con, en, m, s, asker) for s in m["na"]]
    sh_cards = [_card_short(con, en, m, s) for s in m["sh"]]
    scan = ['<div class="s7s">%s</div>' % _L(en, "s708_scan_s"), "<!--s708all-->"]
    if m["pairs"]:
        scan.append('<div class="s7g" id="g_pair">%s · %d</div>' % (_L(en, "s708_g_pair"), len(m["pairs"])))
        scan += [_pair_card(en, m, p, asker) for p in m["pairs"]]
    if asks or redo:
        scan.append('<div class="s7g" id="g_redo">%s · %d</div>' % (_L(en, "s708_g_redo"), len(asks) + len(redo)))
        scan += [_redo_card(en, m, r, asker) for r in redo] + [_redo_ask_card(en, m, a, asker) for a in asks]
    if m["nosc"]:
        scan.append('<div class="s7g" id="g_nosc">%s · %d</div>' % (_L(en, "s708_g_nosc"), len(m["nosc"])))
        scan += [_nosc_card(con, en, m, s, asker) for s in m["nosc"]]
    if m["stale"] and asker:
        scan.append('<div class="s7g" id="g_stale">%s · %d</div>' % (_L(en, "s708_g_stale"), len(m["stale"])))
        for a in m["stale"]:
            key = "stale-%d" % a["id"]
            o = next((r for r in rows if r["id"] == a["order_id"]), None)
            name = "%s · %s" % (o["vendor"], _ddmm(o["created_at"])) if o else "#%d" % a["order_id"]
            scan.append('<div class="s7c" data-card="%s" data-stale="%d"><b>%s</b><div class="vp s7s">%s</div><div class="acts">%s</div></div>'
                        % (key, a["id"], _e(name), _e(_L(en, "s708_stale_l")),
                           _act(en, key, _L(en, "s708_withdraw"), "/api/s454/s708/paper/withdraw", {"id": int(a["id"])}, "g")))
    if m["kept"]:
        scan.append('<div class="s7g" id="g_kept">%s · %d</div>' % (_L(en, "s708_g_kept"), len(m["kept"])))
        scan += [_kept_card(en, m, p, asker) for p in m["kept"]]
    if m["wd"] or m["conflict"]:
        scan.append('<div class="s7g" id="g_wrong">%s · %d</div>' % (_L(en, "s708_g_wrong"), len(m["wd"]) + len(m["conflict"])))
        scan += [_wrong_card(con, en, m, w, asker) for w in m["wd"]] + [_conflict_card(en, m, s) for s in m["conflict"]]
    nm_rows = []
    for s in m["nm"]:
        x = (s.get("scans") or [{}])[0]
        hd = int(x.get("head") or x.get("scan") or 0)
        right = '<span class="s7s">%s · %s</span>' % (_e(_stamps(s)), _e(_ago(en, s.get("scan_at").isoformat() if hasattr(s.get("scan_at"), "isoformat") else s.get("scan_at"), m["now"])))
        if hd:
            right += " " + _bigbtn(en, ctx, hd, "%s · %s" % (_stamps(s), s["vendor"]), queue=False, thumb=s.get("thumb"))
        nm_rows.append(_row(en, m, s, right))
    done_rows = [_row(en, m, s, '<span class="s7grn">%s ✓</span>' % _e(_stamps(s))) for s in m["done"][:DONE_MAX]]
    if len(m["done"]) > DONE_MAX:
        done_rows.append('<div class="s7s">%s</div>' % _e(_L(en, "s708_older", len(m["done"]) - DONE_MAX)))
    colA = (_sec("sec_na", P4.L(en, "s_na"), len(m["na"]), "#b3261e", "#fbe9e7", "#b3261e", '<div class="s7s">%s</div>%s' % (_L(en, "s708_na_s"), _first(na_cards, en)))
            + _sec("sec_short", P4.L(en, "s_short"), len(m["sh"]), "#b3261e", "#fbe9e7", "#b3261e", '<div class="s7s">%s</div>%s' % (_L(en, "s708_sh_s"), _first(sh_cards, en))))
    colB = _sec("sec_scan", _L(en, "s708_scan_h"), n_scan, "#8a5300", "#fbf0dc", "#8a5300", "".join(scan))
    wide = (_sec("sec_marg", P4.L(en, "s_marg"), len(m["nm"]), "#1f3864", "#e6ebf4", "#1f3864", '<div class="s7s">%s</div><div>%s</div>' % (_L(en, "s708_marg_s"), "".join(nm_rows)), wide=True)
            + _sec("sec_done", P4.L(en, "s_done"), len(m["done"]), "#2e6b34", "#e4f2e6", "#1f4d24", '<div class="s7s">%s</div><div>%s</div>' % (_L(en, "s708_done_s"), "".join(done_rows)), wide=True))
    h.append('<div class="s7cols"><div class="s7col">%s</div><div class="s7col">%s</div>%s</div>' % (colA, colB, wide))
    h.append('<a class="s7up" href="#top" onclick="window.scrollTo({top:0,behavior:\'smooth\'});return false;">▲ %s</a>' % _L(en, "s708_up"))
    h.append('<div id="s7v" role="dialog" aria-modal="true" aria-label="scan" data-zoom="%s" data-fit="%s"><div class="vh"><b id="s7vpos"></b><span class="vt" id="s7vt"></span>'
             '<button type="button" id="s7vz" onclick="s7zoom()">%s</button><button type="button" aria-label="%s" onclick="s7close()">✕</button></div>'
             '<div class="vb"><div class="vimg" id="s7vimg"></div><a id="s7vfull" class="s7btn q" href="#" target="_blank" rel="noopener" style="align-self:flex-start">%s</a>'
             '<div class="vact" id="s7vact"></div></div><div class="vf"><button type="button" class="s7btn" id="s7vprev" onclick="s7step(-1)">%s</button>'
             '<button type="button" class="s7btn n" id="s7vnext" onclick="s7step(1)">%s</button></div></div>'
             % (_e(_L(en, "s708_v_zoom")), _e(_L(en, "s708_v_fit")), _L(en, "s708_v_zoom"), _L(en, "s708_v_close"), _L(en, "s708_v_full"), _L(en, "s708_v_prev"), _L(en, "s708_v_next")))
    body = "".join(h)
    nq = body.count('data-vq="1"')
    allb = ('<button type="button" class="s7btn n" onclick="return s7all1()">%s</button>' % _e(_L(en, "s708_all", nq))) if nq else ""
    body = body.replace("<!--s708all-->", allb)
    body = "<style>%s</style><script>%s</script>%s" % (CSS, JS, body)
    return P4.shell(con, u, P4.L(en, "track"), body, back=P, login=login)


# ------------------------------------------------------------------ reception
def reception_items(con, now=None):
    """Reception's scan work: [dict(kind, id, ...)] -- the open rescan asks (porders_s454.rescan_list, the ONE reader) and the open paper asks
    whose order still has no scan (S619's rows, worked out now). Writes nothing."""
    OT, OS, P4 = _ot(), _os(), _w()
    now = now or OS.now()
    x = P4.rescan_list(con)
    out = [dict(kind="rescan", id=int(a["id"]), a=a) for a in x.get("asks") or []]
    pask = paper_asks(con, reception_only=True)
    if pask:
        rows = {s["id"]: s for s in OT.light_all(con, now)}
        for oid, ask in sorted(pask.items(), key=lambda z: z[1]["id"]):
            s = rows.get(oid)
            if s is None:                                     # an order older than the list: its own row, the same fields
                r = con.execute("SELECT id, vendor, created_at FROM purchase_order WHERE id=?", (oid,)).fetchone()
                if r is None:
                    continue
                s = dict(id=r["id"], vendor=r["vendor"], created_at=r["created_at"], bills=[])
            out.append(dict(kind="paper", id=int(ask["id"]), ask=ask, s=s))
    return out


def open_paper_count(con, now=None):
    """The open paper asks (reception's home row) -- one COUNT, no reader run (S708 R1, cost)."""
    try:
        return int(con.execute("SELECT COUNT(DISTINCT order_id) " + RECEPTION_PAPER).fetchone()[0])
    except sqlite3.Error:
        return 0


def candidates(con, ctx, ask, order_vendor):
    """The scans that may be the asked order's bill: usable pharmacy scans (not a picked copy, not a rescan of another bill), untied,
    made at or after the ask, of the order's dealer (the scan's saved dealer, or the dealer the owner / Shavez chose for it). Newest
    first, at most 4. Shown for a person to choose from; never tied by itself."""
    OT = _ot()
    pa = OT._pa()
    want = pa.supplier_key(order_vendor or "")
    at = _dtm(ask.get("asked_at"))
    try:
        tied = {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM order_scan_tie")}
    except sqlite3.Error:
        tied = set()
    out = []
    for sid, sc in sorted(ctx.scans.items(), reverse=True):
        if sid in tied or sc.get("rescan_of") or not ctx.usable(sid) or not sc.get("at") or (at and sc["at"] < at):
            continue
        dealer = (getattr(ctx, "chosen", {}) or {}).get(int(sid)) or OT.pa_key(sc)
        if dealer != want:
            continue
        out.append(int(sid))
        if len(out) >= 4:
            break
    return out


def _intake_paper(s):
    q = dict(lane="pharmacy", vendor=str(s["vendor"])[:120], bill_month=str(s["created_at"])[:7], **{"from": P + "/s454/rescan"})
    return "/scanapp/intake?" + urlencode(q)


def reception(con, u, kind, login, en):
    """Phir se scan karo, rebuilt (S708): each card says what to find, how to scan it, who asked; Scan karo; Kaagaz nahi mila."""
    P4 = _w()
    sq = P4._sq()
    may = _may_mark(con, kind, login)
    items = reception_items(con)
    lost = lost_marks(con)
    h = ['<h1 style="margin:4px 0 0">%s</h1><div class="s7s">%s</div>' % (_L(en, "s708_r_title"), _L(en, "s708_r_top"))]
    how = {"cut": "s708_r_how_cut", "blurred": "s708_r_how_blur", "not_bill": "s708_r_how_not"}
    for it in items:
        if it["kind"] == "rescan":
            a = it["a"]
            key = "ask-%d" % a["id"]
            what = sq.words(a.get("reason"), "owner" if en else "reception") if sq else a.get("reason")
            by = sq.sent_by("owner" if a.get("by_owner") else "", a.get("asked_by") or "") if sq else (a.get("asked_by") or "")
            head = " · ".join(x for x in (a.get("vendor") or "", a.get("stamp") or "", _ddmm(a.get("date") or "")) if x)
            top = ('<div class="s7th"><img loading="lazy" src="%s" alt=""><div style="display:flex;flex-direction:column;gap:4px"><span class="s7s">%s</span>'
                   '<span class="s7red">%s</span><a href="/scanapp/bills/%d/file" target="_blank" rel="noopener" class="s7s">%s</a></div></div>'
                   % (_e(P4._s618_thumb(a)), _L(en, "s708_r_old"), _e(what), int(a["scan"]), _L(en, "s708_r_view")))
            tip = _L(en, how.get(str(a.get("reason")), "s708_r_how_cut"))
            sub = "%s · %s" % (by, _ddmm(a.get("asked_at") or ""))
            tag, tagc = _L(en, "s708_r_tag_redo"), "#b3261e"
            scan_href = P4._s618_intake(a.get("vendor") or "", a.get("month") or "", a["scan"], P + "/s454/rescan")
            lk = lost.get(("rescan", int(a["id"])))
            lkind = "rescan"
        else:
            s, ask = it["s"], it["ask"]
            key = "paper-%d" % ask["id"]
            head = "%s · %s" % (s["vendor"], _ddmm(s["created_at"]))
            bills = _L(en, "s708_r_bills", ", ".join(s["bills"])) if s.get("bills") else ""
            top = '<div class="s7amb">%s</div>%s' % (_L(en, "s708_r_new_what"), ('<div class="s7s">%s</div>' % _e(bills)) if bills else "")
            tip = _L(en, "s708_r_how_new", s["vendor"], _ddmm(s["created_at"]))
            who = str(ask.get("asked_by") or "")
            sub = _L(en, "s708_r_from", (sq.sent_by("owner" if who in P4._s618_owner_logins(con) else "", who) if sq else who), _ddmm(ask["asked_at"]))
            tag, tagc = _L(en, "s708_r_tag_new"), "#8a5300"
            scan_href = _intake_paper(s)
            lk = lost.get(("paper", int(ask["id"])))
            lkind = "paper"
        if lk:
            acts = ('<div class="s7warn">%s</div>' % _L(en, "s708_r_lost_ok")) + (
                _act(en, key, _L(en, "s708_r_found"), "/api/s454/s708/lost/clear", {"id": int(lk["id"])}) if may else "")
        else:
            acts = ('<div class="s7two"><a class="s7btn g" style="min-height:56px;font-size:18px;flex:2 1 0" href="%s">%s</a>%s</div>'
                    % (_e(scan_href), P4.L(en, "scankaro"),
                       _act(en, key, _L(en, "s708_r_lost"), "/api/s454/s708/lost", {"kind": lkind, "id": int(it["id"])}) if may else ""))
            if lkind == "paper" and may:                      # S708 R2: reception says it is scanned; Shavez or the owner then picks the scan
                acts += '<div style="margin-top:8px">%s</div>' % _act(en, key, _L(en, "s708_r_done"), "/api/s454/s708/paper/scanned", {"id": int(it["id"])}, "n")
        h.append('<div class="s7c" data-card="%s" data-%s="%d" style="background:#fff"><div class="h"><b>%s</b><span class="s7tag" style="background:%s">%s</span></div>%s'
                 '<div style="background:#f6f4f1;border-radius:10px;padding:10px 12px;font-size:15px"><b>%s</b> %s</div><div class="s7s">%s</div><div class="acts">%s</div></div>'
                 % (key, "ask" if lkind == "rescan" else "paper", it["id"], _e(head), tagc, _e(tag), top, _L(en, "s708_r_how"), _e(tip), _e(sub), acts))
    if not items:
        h.append('<div class="ok"><div class="t">%s</div></div>' % _L(en, "s708_r_none"))
    body = "<style>%s .wrap{max-width:640px}</style><script>%s</script>%s" % (CSS, JS, "".join(h))
    return P4.shell(con, u, _L(en, "s708_r_title"), body, back=P, login=login)


# ------------------------------------------------------------------ the doors (called by porders_s454's routes; each returns (dict, status))
def _ok(html):
    return dict(ok=True, html=html), 200


ERRS = {
    "not_asker": ("Yeh kaam sirf Doctor sahab aur Shavez ka hai.", "Only the owner and Shavez do this."),
    "bad_request": ("Kuchh galat bheja gaya — page dobara kholiye.", "Something was sent wrong — reload the page."),
    "not_a_pair": ("Yeh do scan ek hi bill ke nahi hain (ab).", "These two scans are not one paper scanned twice (any more)."),
    "already_picked": ("Is bill ka scan pehle hi chuna ja chuka hai — page dobara kholiye.", "A scan of this bill was already picked — reload the page."),
    "not_open": ("Yeh kaam ab khula nahi hai — page dobara kholiye.", "This is not open any more — reload the page."),
    "no_such_scan": ("Yeh scan nahi mila.", "No such scan."),
    "not_wrong": ("Yeh scan kisi aur dealer ke naam se save nahi hai.", "This scan is not saved under another dealer."),
    "paper_read": ("Kaagaz ka dealer padha gaya hai — “Dealer badliye” dabaiye.", "The paper's dealer is read — use Change dealer."),
    "not_a_choice": ("Yeh dealer is scan ki list mein nahi hai.", "That dealer is not one of this scan's choices."),
    "not_needed": ("Is order ka scan ho chuka hai, ya maal nahi aaya.", "This order has its scan, or has not arrived."),
    "already_asked": ("Yeh pehle se reception ke paas hai.", "It is already with reception."),
    "not_allowed": ("Yeh aapke login ka kaam nahi hai.", "Not for this login."),
    "already": ("Pehle se likha hai.", "Already marked."),
    "not_scanned": ("Reception ne abhi scan nahi bataya.", "Reception has not said it is scanned."),
    "not_a_cand": ("Yeh scan is order ka nahi ho sakta (ab).", "That scan cannot be this order's (any more)."),
    "tied_already": ("Is order ya is scan ka jod pehle se hai — page dobara kholiye.", "The order or the scan is already tied — reload the page."),
}


def _no(err, en, code=409):
    """A refusal in the screen's own language (Roman Hindi for the staff, English for the owner)."""
    w = ERRS.get(err, (err, err))
    return dict(ok=False, error=err, message=w[1 if en else 0]), code


def api_pick(con, u, kind, login, b):
    P4 = _w()
    en = kind == "owner"
    if not P4._s618_asker(con, kind, login):
        return _no("not_asker", en, 403)
    try:
        keep, drop = int(b.get("keep") or 0), int(b.get("drop") or 0)
    except (TypeError, ValueError):
        keep = drop = 0
    if not keep or not drop or keep == drop:
        return _no("bad_request", en, 400)
    OT = _ot()
    ctx = OT.Ctx(con)
    pairs = OT.same_paper(con, ctx, asked_too=True)
    p = next((p for p in pairs if {int(p["a"]), int(p["b"])} == {keep, drop}), None)
    if p is None:
        return _no("not_a_pair", en)
    ensure(con)
    w = P4.who(u)
    now = _os().now_iso()
    cur = con.execute("INSERT INTO s708_scan_pick (keep_id, drop_id, picked_by, picked_at) SELECT ?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM s708_scan_pick "
                      "WHERE undone_at IS NULL AND (drop_id IN (?,?) OR keep_id=?))", (keep, drop, w, now, keep, drop, drop))
    if not cur.rowcount:
        return _no("already_picked", en)
    pid = cur.lastrowid
    wd = con.execute("UPDATE scan_rescan_ask SET withdrawn_at=?, withdrawn_by=? WHERE asset_bill_id=? AND done_at IS NULL AND withdrawn_at IS NULL",
                     (now, "%s (S708 pick)" % login, drop)).rowcount if _has(con, "scan_rescan_ask") else 0
    _os().audit(con, w, "s708_scan_pick", pid, dict(keep=keep, drop=drop, asks_withdrawn=wd, kit=KIT))
    con.commit()
    sk = (ctx.scans.get(keep) or {}).get("stamp_no") or "#%d" % keep
    sd = (ctx.scans.get(drop) or {}).get("stamp_no") or "#%d" % drop
    key = "pair-%d-%d" % (int(p["a"]), int(p["b"]))
    html = '<div class="s7ok">%s%s %s</div>' % (_e(_L(en, "s708_kept", sk, sd)), _e(_L(en, "s708_kept_ask")) if wd else "",
                                                _act(en, key, _L(en, "s708_undo"), "/api/s454/s708/pick/undo", {"id": int(pid)}))
    return _ok(html)


def api_pick_undo(con, u, kind, login, b):
    P4 = _w()
    en = kind == "owner"
    if not P4._s618_asker(con, kind, login):
        return _no("not_asker", en, 403)
    try:
        pid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        pid = 0
    ensure(con)
    n = con.execute("UPDATE s708_scan_pick SET undone_at=?, undone_by=? WHERE id=? AND undone_at IS NULL", (_os().now_iso(), P4.who(u), pid)).rowcount
    if not n:
        return _no("not_open", en)
    _os().audit(con, P4.who(u), "s708_scan_pick_undone", pid, dict(kit=KIT))
    con.commit()
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_undone")))


def api_dealer(con, u, kind, login, b):
    """The 'pick the dealer' door: a scan of the wrong-dealer list whose paper is NOT read for sure, to a dealer of the server's own list."""
    P4 = _w()
    en = kind == "owner"
    if not P4._s618_asker(con, kind, login):
        return _no("not_asker", en, 403)
    try:
        sid = int(b.get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    want = str(b.get("dealer") or "")
    OT = _ot()
    ctx = OT.Ctx(con)
    s = ctx.scans.get(sid)
    if not sid or not s or str(s.get("lane") or "") != "pharmacy" or str(s.get("status") or "") == "rejected":
        return _no("no_such_scan", en, 404)
    if sid not in {int(w["scan"]) for w in OT.wrong_dealer(con, ctx)}:
        return _no("not_wrong", en)
    if OT.paper_dealer(con, ctx, sid):
        return _no("paper_read", en)
    ch = dict(dealer_choices(con, ctx, sid))
    if want not in ch:
        return _no("not_a_choice", en)
    res = P4._s708_put_dealer(con, u, sid, want, ctx, s, "s708_dealer_pick")
    if res.get("tie"):
        r = con.execute("SELECT created_at FROM purchase_order WHERE id=?", (res["tie"],)).fetchone()
        return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_dealer_to", ch[want], _ddmm(r[0]) if r else "#%s" % res["tie"])))
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_dealer_ok2", ch[want])))


def api_paper(con, u, kind, login, b):
    P4 = _w()
    en = kind == "owner"
    if not P4._s618_asker(con, kind, login):
        return _no("not_asker", en, 403)
    try:
        oid = int(b.get("order") or 0)
    except (TypeError, ValueError):
        oid = 0
    OT, OS = _ot(), _os()
    now = OS.now()
    rows = OT.light_all(con, now)
    if oid not in {s["id"] for s in never_scanned(rows, now)}:
        return _no("not_needed", en)
    ensure(con)
    if oid in paper_asks(con):
        return _no("already_asked", en)
    cur = con.execute("INSERT INTO s708_paper_ask (order_id, asked_by, asked_at) SELECT ?,?,? WHERE NOT EXISTS (SELECT 1 FROM s708_paper_ask "
                      "WHERE order_id=? AND withdrawn_at IS NULL)", (oid, login, OS.now_iso(), oid))
    if not cur.rowcount:
        return _no("already_asked", en)
    OS.audit(con, P4.who(u), "s708_paper_ask", cur.lastrowid, dict(order=oid, kit=KIT))
    con.commit()
    key = "nosc-%d" % oid
    return _ok('<div class="s7ok">%s%s</div>' % (_e(_L(en, "s708_asked", _ddmm(OS.now_iso()))),
                                                _act(en, key, _L(en, "s708_withdraw"), "/api/s454/s708/paper/withdraw", {"id": int(cur.lastrowid)})))


def api_paper_withdraw(con, u, kind, login, b):
    P4 = _w()
    en = kind == "owner"
    if not P4._s618_asker(con, kind, login):
        return _no("not_asker", en, 403)
    try:
        aid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        aid = 0
    ensure(con)
    n = con.execute("UPDATE s708_paper_ask SET withdrawn_at=?, withdrawn_by=? WHERE id=? AND withdrawn_at IS NULL", (_os().now_iso(), login, aid)).rowcount
    if not n:
        return _no("not_open", en)
    _os().audit(con, P4.who(u), "s708_paper_withdrawn", aid, dict(kit=KIT))
    con.commit()
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_withdrawn")))


def _ask_row(con, aid):
    try:
        r = con.execute("SELECT * FROM s708_paper_ask WHERE id=?", (aid,)).fetchone()
        return dict(r) if r else None
    except sqlite3.Error:
        return None


def _open_ask(con, aid):
    """The ask if it is open on the owner's page (not withdrawn, its order untied), else None."""
    a = _ask_row(con, aid)
    if not a or a.get("withdrawn_at"):
        return None
    if con.execute("SELECT 1 FROM order_scan_tie WHERE order_id=?", (a["order_id"],)).fetchone():
        return None
    if not con.execute("SELECT 1 FROM purchase_order WHERE id=? AND status IN ('sent','received')", (a["order_id"],)).fetchone():
        return None                                           # R3: a cancelled order's ask is not open
    return a


def _int(b, k):
    try:
        return int(b.get(k) or 0)
    except (TypeError, ValueError):
        return 0


def api_paper_scanned(con, u, kind, login, b):
    """Reception: "Scan ho gaya" on an open paper ask -- it leaves reception's list; the owner and Shavez then pick the scan."""
    P4 = _w()
    en = kind == "owner"
    if not _may_mark(con, kind, login):
        return _no("not_allowed", en, 403)
    aid = _int(b, "id")
    ensure(con)
    a = _open_ask(con, aid)
    if not a or a.get("scanned_at"):
        return _no("not_open", en)
    con.execute("UPDATE s708_paper_ask SET scanned_at=?, scanned_by=? WHERE id=? AND scanned_at IS NULL AND withdrawn_at IS NULL",
                (_os().now_iso(), P4.who(u), aid))
    _os().audit(con, P4.who(u), "s708_paper_scanned", aid, dict(order=a["order_id"], kit=KIT))
    con.commit()
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_r_done_ok")))


def api_paper_tie(con, u, kind, login, b):
    """The owner or Shavez: "This is its bill" -- the chosen scan (one of the server's own candidates) is tied to the asked order
    through order_sheet._tie (how='paper_ask'), as the S454 tie does."""
    P4, OT, OS = _w(), _ot(), _os()
    en = kind == "owner"
    if not P4._s618_asker(con, kind, login):
        return _no("not_asker", en, 403)
    aid, sid = _int(b, "id"), _int(b, "scan")
    ensure(con)
    a = _open_ask(con, aid)
    if not a or not a.get("scanned_at"):
        return _no("not_scanned" if a else "not_open", en)
    o = con.execute("SELECT * FROM purchase_order WHERE id=?", (a["order_id"],)).fetchone()
    if o is None:
        return _no("not_open", en)
    o = dict(o)
    ctx = OT.Ctx(con)
    if sid not in candidates(con, ctx, a, o["vendor"]):
        return _no("not_a_cand", en)
    sc = dict(ctx.scans[sid], id=sid)
    if con.execute("SELECT 1 FROM order_scan_tie WHERE order_id=? OR asset_bill_id=?", (o["id"], sid)).fetchone():
        return _no("tied_already", en)
    OS._tie(con, o, sc, "paper_ask", P4.who(u))
    con.commit()
    if not con.execute("SELECT 1 FROM order_scan_tie WHERE order_id=? AND asset_bill_id=?", (o["id"], sid)).fetchone():
        return _no("tied_already", en)
    try:
        OS._pa()._rematch(con, P4.who(u))                     # the scan links follow at once (as Change dealer does)
    except Exception:                                         # noqa: BLE001
        pass
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_tied_ok", sc.get("stamp_no") or "#%d" % sid)))


def api_paper_reask(con, u, kind, login, b):
    """The owner or Shavez: the paper back to reception -- the old ask withdrawn (kept, marked), a new one made (people's entries are never
    overwritten)."""
    P4, OS = _w(), _os()
    en = kind == "owner"
    if not P4._s618_asker(con, kind, login):
        return _no("not_asker", en, 403)
    aid = _int(b, "id")
    ensure(con)
    a = _open_ask(con, aid)
    if not a:
        return _no("not_open", en)
    now = OS.now_iso()
    if not con.execute("UPDATE s708_paper_ask SET withdrawn_at=?, withdrawn_by=? WHERE id=? AND withdrawn_at IS NULL", (now, "%s (S708 again)" % login, aid)).rowcount:
        return _no("not_open", en)
    cur = con.execute("INSERT INTO s708_paper_ask (order_id, asked_by, asked_at) VALUES (?,?,?)", (a["order_id"], login, now))
    OS.audit(con, P4.who(u), "s708_paper_reask", cur.lastrowid, dict(order=a["order_id"], old=aid, kit=KIT))
    con.commit()
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_asked", _ddmm(now))))


def _may_mark(con, kind, login):
    P4 = _p4()
    return P4._s618_asker(con, kind, login) or P4._s618_doer(con, login)


def api_lost(con, u, kind, login, b):
    """Reception's 'Kaagaz nahi mila' on an OPEN rescan ask or an OPEN paper ask (reception's own list decides what is open)."""
    P4 = _w()
    en = kind == "owner"
    if not _may_mark(con, kind, login):
        return _no("not_allowed", en, 403)
    k = str(b.get("kind") or "")
    try:
        rid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        rid = 0
    if not any(i["kind"] == k and i["id"] == rid for i in reception_items(con)):
        return _no("not_open", en)
    ensure(con)
    if (k, rid) in lost_marks(con):
        return _no("already", en)
    cur = con.execute("INSERT INTO s708_lost (kind, ref_id, lost_by, lost_at) VALUES (?,?,?,?)", (k, rid, P4.who(u), _os().now_iso()))
    _os().audit(con, P4.who(u), "s708_lost", cur.lastrowid, dict(kind=k, ref=rid, kit=KIT))
    con.commit()
    key = ("ask-%d" if k == "rescan" else "paper-%d") % rid
    return _ok('<div class="s7warn">%s</div>%s' % (_L(en, "s708_r_lost_ok"), _act(en, key, _L(en, "s708_r_found"), "/api/s454/s708/lost/clear", {"id": int(cur.lastrowid)})))


def api_lost_clear(con, u, kind, login, b):
    P4 = _w()
    en = kind == "owner"
    if not _may_mark(con, kind, login):
        return _no("not_allowed", en, 403)
    try:
        lid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        lid = 0
    ensure(con)
    n = con.execute("UPDATE s708_lost SET cleared_at=?, cleared_by=? WHERE id=? AND cleared_at IS NULL", (_os().now_iso(), P4.who(u), lid)).rowcount
    if not n:
        return _no("not_open", en)
    _os().audit(con, P4.who(u), "s708_lost_cleared", lid, dict(kit=KIT))
    con.commit()
    return _ok('<div class="s7ok">%s</div>' % _e(_L(en, "s708_r_found_ok")))


def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None
