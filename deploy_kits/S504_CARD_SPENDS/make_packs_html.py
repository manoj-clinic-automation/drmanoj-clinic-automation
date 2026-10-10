import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
assert hashlib.md5(b).hexdigest() == 'c857718c75b594f30419220f5a535432', 'FROM pin differs'
s = b.decode('utf-8')
def rep(a, c):
    global s
    n = s.count(a)
    assert n == 1, (n, a[:80])
    s = s.replace(a, c)

rep('''<details class="sec" id="d_amir">''', '''<!-- S504: the card spends -- every line of each card statement, proved against its own totals; two words per line (the owner's,
     the accountant's ledger); the merchants still to be named, named once here. -->
<details class="sec" id="d_cards"><summary>Card spends — <span id="mn2"></span> <span class="sm" id="s_cards"></span></summary><div class="in">
<div class="mut">Every line of each card statement dated in the month, read by the server and checked against the totals the statement itself prints. Each line has two words: what it is for you, and the ledger the accountants post it to. Name a merchant once below and every line of it — past and future — follows.</div>
<div id="cards">loading…</div></div></details>
<details class="sec" id="d_amir">''')

rep('''    fillSummaries(j);''', '''    fillSummaries(j);
    cardsView(j);''')

rep('''/* S434: the summaries -- what each folded section holds, in one line; the top card says what is missing */''', '''/* S504: the card spends */
function rs(p){var n=Math.abs(p||0)/100;return (p<0?"-":"")+"₹"+n.toLocaleString("en-IN",{minimumFractionDigits:2,maximumFractionDigits:2})}
function cardsView(j){var c=j.cards||{}, e=$("cards"); $("mn2").textContent=j.month_name||"";
  if(!c.statements){e.innerHTML='<span class="mut">The card reader is not on this server.</span>';$("s_cards").textContent="";return}
  var st=c.statements, un=c.unnamed||[], spent=(c.by_category||[]).filter(function(g){return g.category!=="repayment"}).reduce(function(a,g){return a+g.net_p},0);
  $("s_cards").textContent="· "+(st.length?st.length+" statement"+(st.length===1?"":"s")+(c.all_proved?", all proved":", "+st.filter(function(s){return !s.proof_ok}).length+" NOT proved")+" · spent "+rs(spent):"no card statement dated this month yet")+(un.length?" · "+un.length+" merchant"+(un.length===1?"":"s")+" to name":"");
  var h='<table><tr><th>Card</th><th>Statement dated</th><th>Lines</th><th>Checked against its own totals</th></tr>'+(st.length?st.map(function(s){return '<tr><td>'+esc(s.label)+(s.card_tail?' <span class="mut">…'+esc(s.card_tail)+'</span>':'')+'</td><td>'+esc(s.statement_date)+'</td><td>'+s.lines+'</td><td>'+(s.proof_ok?'<span class="ok">proved</span>':'<span class="bad">does not add up</span>')+' <span class="mut">'+esc(s.proof)+'</span></td></tr>'}).join(""):'<tr><td colspan="4" class="mut">none yet</td></tr>')+'</table>';
  h+='<h3 style="font-size:15px;margin:12px 0 4px">By what it is</h3><table><tr><th>For you</th><th>Accountant\\'s ledger</th><th>Spent</th><th>Credits</th><th>Net</th><th>Lines</th></tr>'+(c.by_category||[]).map(function(g){return '<tr><td>'+esc(g.owner_label)+'</td><td class="mut">'+esc(g.ledger)+'</td><td>'+rs(g.debit_p)+'</td><td>'+(g.credit_p?rs(g.credit_p):'')+'</td><td><b>'+rs(g.net_p)+'</b></td><td>'+g.lines+'</td></tr>'}).join("")+'</table>';
  if(un.length){var opts=(c.categories||[]).filter(function(k){return k.key!=="unnamed"}).map(function(k){return '<option value="'+esc(k.key)+'">'+esc(k.owner_label)+' — '+esc(k.ledger)+'</option>'}).join("");
    h+='<h3 style="font-size:15px;margin:12px 0 4px">Name these merchants (once — every line of each follows)</h3><table><tr><th>Merchant, as the card prints it</th><th>Lines</th><th>Amount (all statements)</th><th>What it is</th><th></th></tr>'+un.map(function(x,i){return '<tr><td>'+esc(x.merchant)+'</td><td>'+x.lines+'</td><td>'+rs(x.amount_p)+'</td><td><select id="cm'+i+'"><option value="">— choose —</option>'+opts+'</select></td><td><button class="ghost" onclick="nameMerchant('+i+')">Save</button></td></tr>'}).join("")+'</table>'}
  var ln=c.lines||[];
  h+='<details style="margin-top:10px"><summary class="mut">Every line ('+ln.length+')</summary><table><tr><th>Date</th><th>Card</th><th>Narration</th><th>For you</th><th>Ledger</th><th>Amount</th></tr>'+ln.map(function(l){return '<tr><td>'+esc(l.date.slice(8,10)+"-"+l.date.slice(5,7))+'</td><td class="mut">'+esc(l.card)+'</td><td>'+esc(l.description)+(l.intl?' <span class="mut">('+esc(l.intl)+')</span>':'')+'</td><td>'+esc(l.owner_label)+'</td><td class="mut">'+esc(l.ledger)+'</td><td>'+(l.credit?'<span class="ok">'+rs(l.amount_p)+' CR</span>':rs(l.amount_p))+'</td></tr>'}).join("")+'</table></details>';
  e.innerHTML=h; CU=un}
var CU=[];
function nameMerchant(i){var x=CU[i], k=$("cm"+i).value; if(!x||!k){alert("choose what it is first");return}
  post("/finance/packs/api/card-merchant",{merchant:x.merchant,category:k}).then(function(j){if(!j.ok){alert(j.message||j.error);return} flash("Named — every line of "+x.merchant+" follows."); load()})}
/* S434: the summaries -- what each folded section holds, in one line; the top card says what is missing */''')

rep('''["d_pack","d_shelf","d_amir","d_chk","d_pw"]''', '''["d_pack","d_shelf","d_cards","d_amir","d_chk","d_pw"]''')
open(dst, 'wb').write(s.encode('utf-8'))
print('built', hashlib.md5(s.encode('utf-8')).hexdigest())
