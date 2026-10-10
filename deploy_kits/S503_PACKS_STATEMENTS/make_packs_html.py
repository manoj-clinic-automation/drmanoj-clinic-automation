"""S503 builder: packs.html (73ff8c2f) -> S503, anchored edits on the live bytes."""
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
assert hashlib.md5(b).hexdigest() == '73ff8c2f06a6e070c0ff293afb2e3ff6', 'FROM pin differs'
t = b.decode('utf-8')
def rep(old, new):
    global t
    n = t.count(old)
    assert n == 1, (n, old[:80])
    t = t.replace(old, new)
rep('''<div class="mut">Only for password-locked PDFs (the banks' e-statements). Not needed while the branch sends each month's statements unlocked. One password per Yes Bank account — each account's e-statement has its own; the three bank rows below take any other.''',
    '''<div class="mut">For every password-locked PDF — the banks' e-statements and the credit-card statements. One box per Yes Bank account, per ICICI account and per card; the three bank rows at the end take any other. The shelf opens the files itself; nothing waits on an outside script.''')
rep('''      (c.twin_missing?'<br><span class="warn">newest original has no decrypted twin</span>':'')+'</div>'}).join("");''',
    '''      (c.twin_missing?'<br><span class="warn">newest original has no decrypted twin</span>':'')+
      (c.copies&&c.copies.length?'<br><span class="mut">also on the shelf: '+c.copies.map(function(x){return '<a href="/finance/packs/file/'+x.id+'" target="_blank">'+esc(x.what)+'</a> ('+esc(x.read_status||"not read")+(x.matched_status?' · '+esc(x.matched_status):'')+')'}).join(' · ')+'</span>':'')+'</div>'}).join("");''')
rep('''      '<div class="mut" style="margin-top:6px">Locked files still closed: '+sc.locked_open+(sc.no_password?' ('+sc.no_password+' that no stored password opens)':'')+' · opened by the shelf so far: '+sc.opened+'</div>';''',
    '''      '<div class="mut" style="margin-top:6px">Locked files still closed: '+sc.locked_open+(sc.no_password?' ('+sc.no_password+' that no stored password opens)':'')+' · opened by the shelf so far: '+sc.opened+'</div>'+
      ((sc.locked_files||[]).length?'<table style="margin-top:6px"><tr><th>Locked file, waiting for its password</th><th>Arrived</th><th>State</th><th></th></tr>'+sc.locked_files.map(function(x){return '<tr><td><b>'+esc(x.what)+'</b>'+(x.card?' <span class="mut">('+esc(x.card)+')</span>':'')+'<br><span class="mut">'+esc(x.name)+'</span></td><td class="mut">'+esc(x.arrived)+'</td><td class="mut">'+esc(x.why)+'</td><td><button class="ghost" onclick="setAside('+x.id+',false)">Set aside — not needed</button></td></tr>'}).join("")+'</table>':'')+
      ((sc.set_aside||[]).length?'<div class="mut" style="margin-top:6px">Set aside (never tried, never counted): '+sc.set_aside.map(function(x){return esc(x.what)+' <a href="#" onclick="setAside('+x.id+',true);return false">put back</a>'}).join(' · ')+'</div>':'');''')
rep('''  $("s_pw").textContent="· "+(set?set+" set":"none set")+" · "+sc.locked_open+" locked copies set aside";''',
    '''  $("s_pw").textContent="· "+(set?set+" set":"none set")+" · "+sc.locked_open+" locked, waiting for a password"+((sc.set_aside||[]).length?" · "+sc.set_aside.length+" set aside":"");''')
rep('''function assign(fid){''', '''/* S503: a locked file the owner does not need is set aside (never tried, never counted); one tap puts it back */
function setAside(fid,back){if(!back&&!confirm("Set this file aside? It will not be tried or counted. You can put it back later."))return;
  post("/finance/packs/api/set-aside",{file:fid,back:!!back}).then(function(j){if(!j.ok){alert(j.message||j.error||"not saved");return} flash(back?"Put back — it is tried again on the next run.":"Set aside."); load()})}
function assign(fid){''')
open(dst, 'w', encoding='utf-8').write(t)
print('built', hashlib.md5(t.encode()).hexdigest())
