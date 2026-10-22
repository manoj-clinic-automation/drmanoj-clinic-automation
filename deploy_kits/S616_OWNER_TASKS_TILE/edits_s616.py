#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s616.py -- kit S616 (session S336, 22-Oct-2026): exact, counted edits on two live files.
    python3 edits_s616.py portal LIVE OUT [KIT]     /root/portal/portal.py      3be15f45 -> the S616 file
    python3 edits_s616.py panel  LIVE OUT [KIT]     /root/finance/aaj_panel.html 36bd57bc -> the S616 file
(exit 0 only if every anchor occurs exactly once and OUT = KIT)

THE OWNER, his board note of 06:21 IST 22-Oct: "we developed a messaging and tasks app and connected with voiceapp,
cant see it in my portal".  It is built and live -- his panel's Tasks (S493/S495: give a task, the staff answer done /
can't / a note, he replies or closes) and the Voicenotes lines (S514: 36 waiting since 12/14-Oct) -- but his portal
home had no door to it: the staff have 'Aaj ka kaam'; his home has Today, which opens the console.
  portal: a 'Tasks & messages' tile on the owner's home, above the strip, with a live line ('36 Voicenotes lines waiting
          . 2 tasks open . 1 answered by staff'). It stays hidden unless the Voicenotes door answers this login as the panel's
          owner -- so Dr Bhawna, the staff, or a finance outage see the home exactly as before.
  panel:  /finance/aaj?tab=tasks opens on Tasks; the page is named 'Staff lists & tasks'.
"""
import hashlib
import sys

TILE_HTML = '''  <style>
  .tasktile{display:block;text-decoration:none;background:#14456e;color:#fff;border-radius:14px;padding:14px 16px 12px;margin:0 0 12px}
  .tasktile[hidden]{display:none}
  .tasktile .tk-h{font-size:17px;font-weight:700;margin:0 0 6px}
  .tasktile .tk-l{font-size:15px;line-height:1.45}
  .tasktile .tk-l b{color:#ffe08a;font-weight:700}
  .tasktile .tk-f{margin-top:8px;font-size:13px;color:#c9dcea}
  </style>
  <a class="tasktile" id="taskTile" href="/finance/aaj?tab=tasks" target="_blank" rel="noopener" hidden>
    <div class="tk-h">&#x1F4DD; Tasks &amp; messages</div>
    <div class="tk-l" id="taskLine">Give a task &middot; read the staff&rsquo;s answers</div>
    <div class="tk-f">Open tasks &rarr;</div>
  </a>
  <div class="strip">
'''

TILE_JS = '''/* S616: the owner's 'Tasks & messages' tile -- his panel's Tasks (S493/S495) and the Voicenotes lines (S514). Hidden until
   the Voicenotes door answers this login as the panel's owner; for anyone else, or with finance down, the home is as before. */
(function(){
  var t=document.getElementById('taskTile'), l=document.getElementById('taskLine');
  if(!t||!l)return;
  var dot=' '+String.fromCharCode(183)+' ', parts=[];
  function draw(){ if(parts.length)l.innerHTML=parts.map(function(x){return '<span style="white-space:nowrap">'+x+'</span>';}).join(dot); }
  fetch('/finance/aaj/api/vn',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||!d.ok)return;
     t.hidden=false;
     var n=(d.items||[]).length;
     if(n)parts.push('<b>'+n+'</b> Voicenotes line'+(n>1?'s':'')+' waiting');
     draw();
     fetch('/finance/aaj/api/switch?panel=1',{credentials:'same-origin'})
      .then(function(r){return r.ok?r.json():null;})
      .then(function(j){
        var ts=(j&&j.ok&&j.panel&&j.panel.tasks)||[], op=0, an=0;
        ts.forEach(function(x){ if(x.state==='open')op++; else if(x.state==='done'||x.state==='cant')an++; });
        if(op)parts.push('<b>'+op+'</b> task'+(op>1?'s':'')+' open');
        if(an)parts.push('<b>'+an+'</b> answered by staff');
        draw();
      })
      .catch(function(){});
   })
   .catch(function(){});
})();
/* S481: the owner's Today tile.'''

EDITS = {
    "portal": [
        ('  <div class="strip">\n', TILE_HTML),
        ("/* S481: the owner's Today tile.", TILE_JS),
    ],
    "panel": [
        ('<title>Staff daily lists</title>', '<title>Staff lists &amp; tasks</title>'),
        ('<h1>Staff daily lists</h1>', '<h1>Staff lists &amp; tasks</h1>'),
        ('      var t=recall("aaj.tab"); if(',
         '      var t=(/[?&]tab=tasks(&|$)/.test(location.search)?"tasks":recall("aaj.tab")); if('),   # S616: the tile opens on Tasks
    ],
}


def main():
    which, live, out = sys.argv[1], sys.argv[2], sys.argv[3]
    kit = sys.argv[4] if len(sys.argv) > 4 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS[which], 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: %s edit %d's anchor occurs %d times (expected 1)" % (which, i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %s: %d edits applied · rebuilt %s" % (which, len(EDITS[which]), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
