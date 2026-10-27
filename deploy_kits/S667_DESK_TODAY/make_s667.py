"""make_s667.py -- kit S667_DESK_TODAY (the parent, session 358, 27-Oct-2026). The owner (12:32 IST): "the X-ray section
says no patient or no parchi saved today" though one was saved this morning.
Read live as shavez: X-ray 1420 and OPD 19858, typed 27-Oct 11:26, sat on 26-Oct. The desk page fixes its `day` when it
loads and never moves it: a desk left open overnight kept 26-Oct as "Aaj" and filed the morning's parchis as late
entries for yesterday (slip_log.log_slip, day != today).
  /root/finance/parchi_desk.py   db5fd07f -> TO   5 counted edits:
    E1 api_save: a save the page made from "Aaj" (today_pick) whose day is no longer today is refused with the day's
       state for today -- nothing is filed under an old day by accident. A deliberate late entry (Kal / a date) is as before.
       A desk opened before this kit (no today_pick) saving for another day is refused: "press F5 once".
    E2 the page: onToday remembers the "Aaj" choice; fillDays() rebuilds the day list from the real today
    E3 draw(): on "Aaj", a state whose today is newer moves the page to the new today (the 8-second poll, and on wake)
    E4 both saves send today_pick; E5 a refused save draws the state it carries (the move happens at once)
  slip_log.py NOT touched. The data step (fix_s667_day.py) moves the two parchis typed 27-Oct onto 27-Oct.
Usage: python make_s667.py <dir holding parchi_desk.py at db5fd07f> <out dir>"""
import hashlib, os, sys

FROM = "db5fd07f8417881fd743b6353b3fa3a2"
src, out = sys.argv[1], sys.argv[2]
b = open(os.path.join(src, "parchi_desk.py"), "rb").read()
assert hashlib.md5(b).hexdigest() == FROM, "the live parchi_desk.py is not %s" % FROM[:8]
T = [b.decode("utf-8")]
N = [0]


def rep(old, new):
    assert T[0].count(old) == 1, "anchor not found exactly once: %r" % old[:90]
    T[0] = T[0].replace(old, new, 1)
    N[0] += 1


# E1 -- the server refuses a stale "Aaj"
rep('''    day = _day_arg(f.get("day"))
    if day is None:
        return _j(ok=False, err="Din sahi chunein — aaj se %d din pehle tak." % SL.LATE_DAYS)
    form = {}''', '''    day = _day_arg(f.get("day"))
    if day is None:
        return _j(ok=False, err="Din sahi chunein — aaj se %d din pehle tak." % SL.LATE_DAYS)
    if f.get("today_pick") and day != SL._today():            # S667: the page said "Aaj" but its day is an old one
        return _j(ok=False, err=("The page was still on %s -- it is on today now. Press Save again." if eng else
                                 "Page abhi tak %s par tha -- ab Aaj par hai. Dobara Save dabayein.") % SL._dmy(day)[:6],
                  state=state(con, SL._today(), SL._who(u)))
    if "today_pick" not in f and day != SL._today():          # S667: a desk opened before this kit -- one F5 makes it the new page
        return _j(ok=False, err=("This page is out of date -- press F5 once, then Save again." if eng else
                                 "Yeh page purana hai -- ek baar F5 dabayein, phir Save karein."))
    form = {}''')
# E2 -- the page remembers "Aaj" and can rebuild its day list
rep('''var day=S.day;
var ds=$('day');B.days.forEach(function(d){var o=document.createElement('option');o.value=d[0];o.textContent=d[1];if(d[0]===day)o.selected=true;ds.appendChild(o);});
ds.addEventListener('change',function(){day=ds.value;refresh(true);});''', '''var day=S.day;var onToday=(S.day===S.today);   /* S667: on "Aaj", the desk follows the real day */
var ds=$('day');B.days.forEach(function(d){var o=document.createElement('option');o.value=d[0];o.textContent=d[1];if(d[0]===day)o.selected=true;ds.appendChild(o);});
function fillDays(today){var n=B.days.length;ds.innerHTML='';var t=new Date(today+'T12:00:00');
 for(var i=0;i<n;i++){var d=new Date(t.getTime()-i*864e5);var iso=d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2);
  var o=document.createElement('option');o.value=iso;o.textContent=i===0?(EN?'Today':'Aaj'):(i===1?(EN?'Yesterday':'Kal'):(iso.slice(8,10)+'-'+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()]));
  if(iso===day)o.selected=true;ds.appendChild(o);}}
ds.addEventListener('change',function(){day=ds.value;onToday=(ds.selectedIndex===0);refresh(true);});''')
# E3 -- draw() moves a stale "Aaj" to the new today
rep('''function draw(st){S=st;var opdTouched''', '''function draw(st){if(onToday&&st.today&&st.today>day){day=st.today;fillDays(st.today);if(st.day!==st.today){refresh(true);return;}}
 S=st;var opdTouched''')
# E4 -- both saves say whether they were made on "Aaj"
rep('''clinic_id:$('opd_id').value.trim(),day:day,''', '''clinic_id:$('opd_id').value.trim(),day:day,today_pick:onToday,''')
rep('''clinic_id:$('xp_id').value.trim(),day:day,''', '''clinic_id:$('xp_id').value.trim(),day:day,today_pick:onToday,''')
# E5 -- a refused save draws the state it carries
rep('''  else{msg(false,r.err);askFor('opd_ask',''', '''  else{msg(false,r.err);if(r.state)draw(r.state);askFor('opd_ask',''')
rep('''  else{msg(false,r.err);askFor('xp_ask',''', '''  else{msg(false,r.err);if(r.state)draw(r.state);askFor('xp_ask',''')
assert N[0] == 7, N[0]
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "parchi_desk.py"), "wb").write(T[0].encode("utf-8"))
print("parchi_desk.py", hashlib.md5(T[0].encode("utf-8")).hexdigest())
