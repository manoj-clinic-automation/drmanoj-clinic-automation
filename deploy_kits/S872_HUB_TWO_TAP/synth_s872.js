// synth_s872.js <finance_approvals.html>  -- kit S872 proof: the page parses; the S869 block has no confirm dialog; the two-tap arms on the
// first tap and sends on the second (3 buttons); an un-armed timer puts the words back. Last line: 'SYNTH S872: n PASS, m FAIL'.
const fs=require('fs'); const h=fs.readFileSync(process.argv[2],'utf8'); let P=0,F=0;
function ok(c,w){ if(c){P++;console.log('PASS',w);} else {F++;console.log('FAIL',w);} }
const m=h.match(/<script>([\s\S]*)<\/script>/); let js=m?m[1]:'';
try{ new Function(js); ok(true,'T1 the page script parses'); }catch(e){ ok(false,'T1 parse: '+e.message); }
const blk=js.slice(js.indexOf('KIT_S869'), js.indexOf('end KIT_S869'));
ok(blk.length>1000 && !/window\.confirm/.test(blk), 'T2 no confirm dialog left in the Hub\'s S869/S872 block');
ok(/s869ReceivedAll\('\+U\.length\+',this\)/.test(js) && /s869Accept\(\\''\+r\.date\+'\\',this\)/.test(js) && /s869Remove\('\+e\.id\+'[^)]*,this\)/.test(js), 'T3 the three buttons pass themselves to the two-tap');
// run the two-tap in isolation
const sent=[]; const fn=new Function('s869Post','s869Refresh','$','dayDetail','alert', blk.slice(blk.indexOf('var S872_ARM'), blk.lastIndexOf('/*')) + '\nreturn {s872TwoTap,s869ReceivedAll,s869Accept,s869Remove};');
const api=fn((u,b)=>{sent.push(u);return Promise.resolve({n:14});}, ()=>{}, ()=>null, ()=>{}, (t)=>{sent.push('ALERT '+t)});
const btn={textContent:'Mark all 14 received',disabled:false};
api.s869ReceivedAll(14,btn);
ok(sent.length===0 && btn.textContent==='Tap again to mark all 14 received', 'T4 first tap arms the button, sends nothing');
api.s869ReceivedAll(14,btn);
ok(sent.length===1 && sent[0].endsWith('/received-all') && btn.disabled===true, 'T5 second tap sends received-all once');
const b2={textContent:'Accept (write off)'}; api.s869Accept('2026-10-17',b2); ok(sent.length===1 && /Tap again to write off/.test(b2.textContent),'T6 Accept arms');
api.s869Accept('2026-10-17',b2); ok(sent.length===2 && sent[1].endsWith('/owner/decide'),'T7 Accept sends on the second tap');
const a3={textContent:'remove'}; api.s869Remove(5,'2026-11-14','dd-x',a3); ok(sent.length===2 && a3.textContent==='tap again to remove','T8 remove arms');
api.s869Remove(5,'2026-11-14','dd-x',a3); ok(sent.length===3 && sent[2].endsWith('/day-entry/remove'),'T9 remove sends on the second tap');
const b4={textContent:'Accept (write off)'}; api.s869Accept('2026-10-01',b4);
setTimeout(()=>{ ok(b4.textContent==='Accept (write off)' && sent.length===3, 'T10 an armed button left alone goes back to its words after 5 s, nothing sent');
  console.log('SYNTH S872: '+P+' PASS, '+F+' FAIL'); process.exit(F?1:0); }, 5200);
