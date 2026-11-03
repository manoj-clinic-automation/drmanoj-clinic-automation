#!/usr/bin/env python3
"""make_s703.py -- kit S703_CALLS_PLAYER (the parent, S382, 03-Nov-2026). Builds the new /root/portal/calls_console.py
from the live one (a0f58fec, S698's) by counted edits; the installer re-runs it on the box's live file and the result
must be the kit's own copy byte for byte.
  python3 make_s703.py <live calls_console.py> <out>
THE CHANGE (the owner, 10:45 IST 03-Nov: "when I tap on it, only the color changes, and I do not know whether it is
working or not. So need a progress bar there when it is playing"): a player bar at the foot of the screen while a
recording is open -- 'Loading...' until the sound starts, a progress bar with the time played and the length, pause and
play on the same button (and on the row's own button), tap the bar to jump, a clear line when the recording cannot be
fetched; the row's button shows the time and fills as it plays. Nothing else on the page changes; no route changes."""
import hashlib, sys

FROM = "a0f58fec929be96d02cfc278776bd631"

CSS_OLD = ".toast{position:fixed;left:50%;bottom:18px;"
CSS_NEW = (
    "/* S703: the recording player */\n"
    ".play,.btn.soft{background-image:linear-gradient(to right,rgba(31,95,74,.22) var(--pp,0%),transparent var(--pp,0%))}\n"
    ".play.on{background-image:linear-gradient(to right,rgba(255,255,255,.38) var(--pp,0%),transparent var(--pp,0%))}\n"
    ".play.load,.btn.load{opacity:.75}\n"
    ".pl{position:fixed;left:0;right:0;bottom:0;z-index:8;display:none;background:var(--paper);border-top:3px solid var(--accent);"
    "box-shadow:0 -4px 14px rgba(0,0,0,.12);padding:10px 16px calc(12px + env(safe-area-inset-bottom))}\n"
    ".pl .plrow{display:flex;align-items:center;gap:12px;max-width:1100px;margin:0 auto}\n"
    ".pl .plbtn{flex:none;width:46px;height:46px;border-radius:50%;border:0;background:var(--accent);color:var(--accent-ink);"
    "font-size:19px;cursor:pointer}\n"
    ".pl .pllab{flex:1;min-width:0;font-size:15px;color:var(--fg);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n"
    ".pl .pltime{flex:none;font-family:var(--mono);font-size:16px;font-weight:600;color:var(--fg)}\n"
    ".pl .plx{flex:none;border:1px solid var(--line);background:var(--paper);color:var(--muted);border-radius:8px;"
    "font-size:20px;line-height:1;padding:6px 11px;cursor:pointer}\n"
    ".pl .plt{max-width:1100px;margin:10px auto 0;height:12px;border-radius:6px;background:var(--line);cursor:pointer;"
    "position:relative;overflow:hidden}\n"
    ".pl .plf{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--accent);border-radius:6px}\n"
    ".pl.loading .plf{width:100%!important;background:repeating-linear-gradient(45deg,var(--line) 0 10px,#c9c5b9 10px 20px)}\n"
    ".pl .plmsg{max-width:1100px;margin:8px auto 0;font-size:15px;display:none}\n"
    ".pl.err{border-top-color:var(--bad)}.pl.err .plmsg{display:block;color:var(--bad);font-weight:600}\n"
    ".pl.err .plt,.pl.err .plbtn{display:none}\n"
    "body.plon .toast{bottom:var(--plh,140px)}\n"
    ".toast{position:fixed;left:50%;bottom:18px;")

HTML_OLD = '<div class="toast" id="toast"></div>\n'
HTML_NEW = (
    '<div class="pl" id="pl" role="region" aria-label="Recording player">'
    '<div class="plrow"><button type="button" class="plbtn" id="plbtn" onclick="plToggle()" aria-label="Play or pause">&#9654;</button>'
    '<span class="pllab" id="pllab">Recording</span><span class="pltime" id="pltime">Loading…</span>'
    '<button type="button" class="plx" onclick="plClose()" aria-label="Close the player">&times;</button></div>'
    '<div class="plt" id="plt" onclick="plSeek(event)" title="Tap to jump"><div class="plf" id="plf"></div></div>'
    '<div class="plmsg" id="plmsg"></div></div>\n'
    '<div class="toast" id="toast"></div>\n')

JS_OLD = """var _pa=null,_pb=null;
function playJk(jk,b){
  if(_pb===b&&_pa){ if(_pa.paused){_pa.play();b.classList.add('on');}else{_pa.pause();b.classList.remove('on');} return; }
  if(_pa){ _pa.pause(); if(_pb)_pb.classList.remove('on'); }
  _pa=new Audio('/portal/rec/'+jk); _pb=b; b.classList.add('on');
  _pa.play().catch(function(){ toast('The recording could not be played.'); b.classList.remove('on'); });
  _pa.onended=function(){ b.classList.remove('on'); };
}
"""
JS_NEW = """var _pa=null,_pb=null;
/* S703: the recording player -- the bar at the foot of the screen and the row's own button both show what is happening */
function _f(s){ if(!isFinite(s)||s<0) return '–:––'; s=Math.floor(s); return Math.floor(s/60)+':'+('0'+(s%60)).slice(-2); }
function _el(i){ return document.getElementById(i); }
function _plState(st,msg){
  var p=_el('pl'); p.classList.toggle('loading',st==='loading'); p.classList.toggle('err',st==='err');
  _el('plmsg').textContent=msg||''; p.style.display='block'; document.body.classList.add('plon');
  document.body.style.paddingBottom=(p.offsetHeight+24)+'px'; document.documentElement.style.setProperty('--plh',(p.offsetHeight+12)+'px');
  if(st==='loading'){ _el('pltime').textContent='Loading…'; }
  _el('plbtn').innerHTML=(st==='playing'||st==='loading')?'&#10074;&#10074;':'&#9654;';
}
function _btnRestore(b){
  if(!b) return; b.classList.remove('on','load','ps'); b.style.removeProperty('--pp');
  if(b.dataset.orig!==undefined){ b.innerHTML=b.dataset.orig; }
}
function _tick(){
  if(!_pa) return; var d=_pa.duration, t=_pa.currentTime, pct=(isFinite(d)&&d>0)?Math.min(100,t/d*100):0;
  _el('plf').style.width=pct+'%'; _el('pltime').textContent=_f(t)+' / '+_f(d);
  if(_pb){ _pb.style.setProperty('--pp',pct+'%'); _pb.innerHTML=(_pa.paused?'&#9654; ':'&#10074;&#10074; ')+_f(t)+' / '+_f(d); }
}
function _fail(a){
  if(a!==_pa) return;
  var b=_pb; _pa=null; _pb=null; try{ a.pause(); }catch(e){}
  _btnRestore(b);
  _plState('err','This recording could not be played — it is not on the server yet, or its link has expired. Try again later.');
  _el('pltime').textContent='';
}
function _label(b){
  var p=b.closest('details.p'), r=b.closest('.tl')||b.closest('.ny')||b.closest('tr')||b.closest('li')||b.parentNode, nm='', tm='';
  if(p){ var w=p.querySelector('summary .who b'); nm=w?w.textContent:''; }
  if(r){ var t=r.querySelector('.tm'); tm=(t&&t!==b)?t.textContent:''; if(!nm){ var bb=r.querySelector('b'); nm=bb?bb.textContent:''; } }
  if(!nm&&r){ var out=[], tw=document.createTreeWalker(r,NodeFilter.SHOW_TEXT,null), n;
    while((n=tw.nextNode())){ if(n.parentNode&&n.parentNode.closest('button,select,option,form,script')) continue; var s=n.nodeValue.trim(); if(s) out.push(s); }
    nm=out.join(' '); }
  var lab=[nm.replace(/\\s+/g,' ').trim(), (tm||'').trim()].filter(Boolean).join(' · ');
  return 'Recording — '+(lab||'call').slice(0,80);
}
function playJk(jk,b){
  if(_pb===b&&_pa){ plToggle(); return; }
  plClose(true);
  var a=new Audio('/portal/rec/'+encodeURIComponent(jk)); a.preload='auto';
  _pa=a; _pb=b; if(b.dataset.orig===undefined) b.dataset.orig=b.innerHTML;
  b.classList.add('on','load');
  _el('pllab').textContent=_label(b); _el('plf').style.width='0';
  _plState('loading');
  function mine(fn){ return function(){ if(a===_pa) fn(); }; }
  a.addEventListener('waiting',mine(function(){ _plState('loading'); _pb&&_pb.classList.add('load'); }));
  a.addEventListener('playing',mine(function(){ _plState('playing'); _pb.classList.remove('load','ps'); _pb.classList.add('on'); _tick(); }));
  a.addEventListener('pause',mine(function(){ if(a.ended) return; _plState('paused'); _pb.classList.remove('on','load'); _pb.classList.add('ps'); _tick(); }));
  a.addEventListener('timeupdate',mine(_tick)); a.addEventListener('loadedmetadata',mine(_tick)); a.addEventListener('durationchange',mine(_tick));
  a.addEventListener('ended',mine(function(){ _tick(); _plState('paused'); _el('pltime').textContent='Finished · '+_f(a.duration);
    _el('plf').style.width='100%'; var b2=_pb; _btnRestore(b2); }));
  a.addEventListener('error',function(){ _fail(a); });
  var pr=a.play(); if(pr&&pr.catch) pr.catch(function(e){ if(a===_pa&&!(e&&e.name==='AbortError')) _fail(a); });
}
function plToggle(){
  var a=_pa; if(!a) return;
  if(a.paused||a.ended){ if(a.ended) a.currentTime=0; if(_pb){ _pb.classList.add('on'); }
    var pr=a.play(); if(pr&&pr.catch) pr.catch(function(e){ if(a===_pa&&!(e&&e.name==='AbortError')) _fail(a); }); }
  else { a.pause(); }
}
function plSeek(ev){
  var a=_pa; if(!a||!isFinite(a.duration)||a.duration<=0) return;
  var r=_el('plt').getBoundingClientRect(), x=(ev.clientX-r.left)/r.width;
  a.currentTime=Math.max(0,Math.min(1,x))*a.duration; _tick();
}
function plClose(keep){
  var a=_pa, b=_pb; _pa=null; _pb=null;
  if(a){ try{ a.pause(); a.removeAttribute('src'); a.load(); }catch(e){} }
  _btnRestore(b);
  if(!keep){ var p=_el('pl'); p.style.display='none'; p.className='pl'; document.body.style.paddingBottom=''; document.body.classList.remove('plon'); }
}
"""

FOOT_OLD = "The recording plays in place; the transcript opens under its row."
FOOT_NEW = ("The recording plays in the player at the foot of the screen (pause, tap the bar to jump); "
            "the transcript opens under its row.")

EDITS = [(CSS_OLD, CSS_NEW, 1), (HTML_OLD, HTML_NEW, 1), (JS_OLD, JS_NEW, 1), (FOOT_OLD, FOOT_NEW, 1)]


def build(src):
    if hashlib.md5(src).hexdigest() != FROM:
        raise SystemExit("make_s703: the live file is %s, not %s" % (hashlib.md5(src).hexdigest()[:8], FROM[:8]))
    t = src.decode("utf-8")
    for i, (old, new, n) in enumerate(EDITS, 1):
        c = t.count(old)
        if c != n:
            raise SystemExit("make_s703: edit %d expects %d place(s), found %d" % (i, n, c))
        t = t.replace(old, new)
    return t.encode("utf-8")


if __name__ == "__main__":
    out = build(open(sys.argv[1], "rb").read())
    open(sys.argv[2], "wb").write(out)
    print("make_s703: %d edits, %s" % (len(EDITS), hashlib.md5(out).hexdigest()))
