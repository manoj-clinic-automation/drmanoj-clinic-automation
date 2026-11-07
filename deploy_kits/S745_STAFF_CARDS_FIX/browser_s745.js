// browser_s742.js -- the rendered walk page in Chromium at PC and phone widths (made-up data only).
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const html=fs.readFileSync(process.argv[2],'utf8');const b=await chromium.launch();let red=0;
 function ck(n,ok){console.log((ok?'ok   ':'RED  ')+n);if(!ok)red++;}
 for(const w of [1366,1920,390]){const p=await b.newPage({viewport:{width:w,height:900}});const errs=[];p.on('pageerror',e=>errs.push(String(e)));
  await p.setContent(html,{waitUntil:'load'});
  const r=await p.evaluate(()=>({sw:document.documentElement.scrollWidth,h:document.documentElement.scrollHeight,
     open:[...document.querySelectorAll('details')].filter(d=>d.open).length,n:document.querySelectorAll('details').length,
     fu:Math.round(document.querySelector('#followups').getBoundingClientRect().top),ckb:Math.round(document.querySelector('#ckb').getBoundingClientRect().bottom)}));
  ck(w+'px: no sideways scroll ('+r.sw+')', r.sw<=w);
  ck(w+'px: every section folded on opening ('+r.open+' of '+r.n+' open)', r.open===0 && r.n>5);
  if(w>=1366) ck(w+'px: follow-ups and Call ke baad on the first screen (top '+r.fu+', ckb ends '+r.ckb+', page '+r.h+')', r.fu<300);
  await p.evaluate(()=>expandAll()); const o=await p.evaluate(()=>[...document.querySelectorAll('details')].filter(d=>d.open).length);
  ck(w+'px: expand all opens every section', o===r.n);
  await p.evaluate(()=>foldAll()); const f=await p.evaluate(()=>[...document.querySelectorAll('details')].filter(d=>d.open).length);
  ck(w+'px: fold all folds them again', f===0);
  await p.click('button[data-f="wa"]'); const vis=await p.evaluate(()=>[...document.querySelectorAll('details.p')].filter(d=>d.style.display!=='none').length);
  const want=await p.evaluate(()=>[...document.querySelectorAll('details.p')].filter(d=>+d.dataset.wa>0).length);
  const all=await p.evaluate(()=>document.querySelectorAll('details.p').length);
  ck(w+'px: the WhatsApp chip filters people ('+vis+' of '+all+')', vis===want && vis>0 && vis<all);
  ck(w+'px: no script error', errs.length===0);
  await p.close();}
 await b.close();console.log(red?'BROWSER RED '+red:'BROWSER OK');process.exit(red?1:0);})();
