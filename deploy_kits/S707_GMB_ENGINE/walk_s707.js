// walk_s707.js — kit S707 (05-Nov-2026, the parent, session S385). Loads a GMB page's script in a bare DOM, draws
// thousands of presses across every language, relation, problem and tick, and measures the plan's rules (claude/S385_GMB_PLAN.md).
// usage: node walk_s707.js <page.html> [presses-per-language] [x] [posted-reviews.txt ...]
//   posted-reviews files (optional, kept OUT of the repository — they hold patients' public review texts):
//   D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S385\GMB_OWN_LISTING_ALL_2026-11-05.txt and GMB_REVIEWS_RAW_2026-11-05.txt
// verdict line: WALK OK ... | WALK RED ... ; exit 0 / 1.
const fs=require('fs'),vm=require('vm');
const file=process.argv[2]||'new7.html';
const html=fs.readFileSync(file,'utf8');
const js=html.split('<script>')[1].split('</script>')[0];
const ft={value:''};
const doc={getElementById:(id)=>id==='freetext'?ft:({value:'',style:{},textContent:'',innerHTML:'',checked:false,classList:{add(){},remove(){},toggle(){}},scrollIntoView(){}}),querySelectorAll:()=>[],querySelector:()=>null,addEventListener(){}};
const ctx={document:doc,window:{},navigator:{},Math,console,setTimeout(){},localStorage:{getItem(){return null},setItem(){}}};
vm.createContext(ctx); vm.runInContext(js,ctx);
function run(st){ return vm.runInContext(st+';mkRevs()',ctx); }
const shuf=a=>a.slice().sort(()=>Math.random()-.5);
const P=['knee','back','cervical','hip_pain','hip_fracture','frozen','tennis','plantar','rheumatoid','as','sports','shoulder_prb','general','fracture'];
const G=['pain','walking','explained','reports','nosurg','plaster','surg','recov','physio_gp','charges','staff','fac'];
const Q=['exp','person','listens','nosurgrush','calm','caring'];
const K=['bilateral','exercises','prp','viscosup','metabolic','weightmgmt','physio','home_ex','nutrition'];
const R=['self','mother','father','wife','husband','child','elderly','relative'];
const BONE=['wrist','hand','forearm','elbow','upper_arm','shoulder','leg','ankle','foot','knee','thigh','spine','rib'];
const SURG={fracture:['complex_ia','mifs'],hip_fracture:['hip_pfn','hemi','hip_mifs'],hip_pain:['thr'],knee:['tkr']};
const STOP=new Set(('के की का में से और है हैं था थी थे को ने भी ही तो पर एक हो गया गई गए हुआ हुई हुए कर किया दिया लिए साथ अब फिर वो उन्हें उनका उनकी मेरे मेरी मुझे हम हमें यह ये ke ki ka mein me se aur hai hain tha thi the ko ne bhi hi to par ek ho gaya gayi hua hui kar kiya diya liye saath ab phir wo unhe unka unki mere meri mujhe hum hume the a an and of to in is was were for with it at on by be has had have we our my his he she they them their her him i am dr dr. manoj agarwal sir मनोज अग्रवाल डॉ. डॉ डॉक्टर साहब सर नहीं कोई क्या बहुत कुछ सब सही अच्छा अच्छे अच्छी nahi nhi koi kya bahut bohot kuch sab sahi achha achhe acha ache achhi very not no any all good doctor जी ji').split(/\s+/));
function reps(t){const w=t.toLowerCase().replace(/[।.,;:!?()\-—–"'’🙏]/g,' ').split(/\s+/).filter(x=>x.length>1&&!STOP.has(x));const m={};w.forEach(x=>m[x]=(m[x]||0)+1);return Object.entries(m).filter(([k,v])=>v>1).reduce((n,[k,v])=>n+v-1,0);}
const wc=t=>t.trim().split(/\s+/).filter(Boolean).length;
const norm=s=>s.toLowerCase().replace(/[^\p{L}\p{N} ]/gu,'').replace(/\s+/g,' ').trim();
const sents=t=>t.replace(/(^|\s)(dr|डॉ)\./gi,'$1$2').split(/[।.!?]\s+|\n/).map(norm).filter(s=>s.split(' ').length>=3);
// the 337 posted reviews
const posted=new Set();
for(const f of process.argv.slice(5)){ if(!fs.existsSync(f)) continue;
  for(const b of fs.readFileSync(f,'utf8').split('\n### ')){ const t=b.split('\n').slice(1).join(' '); sents(t).forEach(s=>posted.add(s)); } }
const postedArr=[...posted].filter(q=>q.split(' ').length>=4);
const N=+process.argv[3]||400;
const stats={n:0,bad:[],wcOut:{short:0,medium:0,long:0},reps:{short:0,medium:0,long:0},name2:0,bare:0,noName:{short:0,medium:0,long:0},shared:0,postedHit:0,noClose:0,emoji:0,endNoDot:0};
const namesRe=/dr\.? manoj agarwal|डॉ\. मनोज अग्रवाल|डॉक्टर मनोज अग्रवाल/gi;
const samples=[];
for(const L of ['Hindi','Mixed','Hinglish','English']){
  for(let i=0;i<N;i++){
    const p=shuf(P).slice(0,chance(0.25)?2:1); const r=pick(R);
    const sudden=p.some(x=>['fracture','hip_fracture','sports'].includes(x));
    const g=shuf(G).slice(0,1+Math.floor(Math.random()*4)), q=shuf(Q).slice(0,Math.floor(Math.random()*3));
    const ko=p.includes('knee')?shuf(K).slice(0,Math.floor(Math.random()*4)):[];
    const bone=sudden&&chance(0.7)?pick(BONE):null, side=bone&&chance(0.5)?pick(['left','right']):null;
    const surg={}; for(const pid of p){ if(SURG[pid]&&chance(0.4)) surg[pid]=pick(SURG[pid]); }
    ft.value=chance(0.1)?'Osteoporosis':'';
    const st=`sR='${r}';sL='${L}';sP=${JSON.stringify(p)};sG=${JSON.stringify(g)};sQ=${JSON.stringify(q)};sKneeOpts=${JSON.stringify(ko)};sAy=${chance(0.15)};sBone=${JSON.stringify(bone)};sSide=${JSON.stringify(side)};Object.keys(sSurg).forEach(k=>delete sSurg[k]);Object.assign(sSurg,${JSON.stringify(surg)})`;
    let r3; try{ r3=run(st); }catch(e){ stats.bad.push('THROW '+e.message+' @ '+st); continue; }
    const lim={short:[8,20],medium:[30,50],long:[60,90]};
    const ss={};
    for(const sz of ['short','medium','long']){
      const t=r3[sz]; stats.n++;
      if(!t||/undefined|«|»|(^|\s)(ko ko|को को|ne ne|ने ने|ka ka|का का)(\s|$)|  /.test(t)) stats.bad.push(sz+': '+t+' @ '+st);
      // S385 cold review: English pronouns, an untold fall, an untold number, slashes, Mixed punctuation, a doubled noun
      if(L==='English'&&/\bhim (gave|is|was|did|actually|said|put|went|looked|explained|listens|knows|hears|puts|genuinely|does|operated|replaced|set)\b|,\s*(him|he)\s*[.!?]?$|,\s*him\.|\b(me|her|him|them) (was|were|is)\b/.test(t)) stats.bad.push('PRONOUN '+sz+': '+t);
      if(/\bfall\b|\bfell\b|gir kar|गिर/i.test(t)) stats.bad.push('FALL '+sz+': '+t);
      if(/\b(24|48|72)\b|\b\d+\s*(ghante|घंटे|hours)/i.test(t)) stats.bad.push('NUMBER '+sz+': '+t);
      if(/ \/ /.test(t)) stats.bad.push('SLASH '+sz+': '+t);
      if(L==='Mixed'&&/।/.test(t)&&/[\u0900-\u097F]\.(\s|$)/.test(t.replace(/डॉ\./g,'डॉ'))) stats.bad.push('PUNCT '+sz+': '+t);
      if(/(तकलीफ|takleef|problem)\s+(और|aur)\s+\S+\s+(की|ki)\s+(तकलीफ|takleef|problem)/i.test(t)) stats.bad.push('DOUBLE '+sz+': '+t);
      const w=wc(t); if(w>lim[sz][1]) stats.wcOut[sz]++; if(sz==='short'&&w>22) stats.s22=(stats.s22||0)+1; if(w<lim[sz][0]) stats.under=(stats.under||0)+1;
      stats.reps[sz]+=reps(t); if(sz==='long'&&reps(t)>3) stats.rep3=(stats.rep3||0)+1;
      const nm=(t.match(namesRe)||[]).length; if(nm>1) stats.name2++; if(nm===0) stats.noName[sz]++;
      if(/bareilly|बरेली/i.test(t)) stats.bare++;
      if(/🙏/.test(t)) stats.emoji++;
      if(!/[।.!?🙏]$/u.test(t)) stats.endNoDot++;
      ss[sz]=sents(t);
      for(const s of ss[sz]){ if(posted.has(s)) { stats.postedHit++; stats.bad.push('POSTED: '+s); } else if(s.split(' ').length>=4){ for(const q of postedArr){ if(q.includes(s)||s.includes(q)){ stats.postedHit++; stats.bad.push('POSTED~ '+s+'  ⊂  '+q.slice(0,120)); break; } } } }
    }
    if(wc(r3.long)<wc(r3.medium)) stats.order=(stats.order||0)+1;
    if(ss.short.some(s=>ss.medium.includes(s)||ss.long.includes(s))||ss.medium.some(s=>ss.long.includes(s))){ stats.shared++; const sh=[...ss.short,...ss.medium].find(s=>ss.long.includes(s)||(ss.medium.includes(s)&&ss.short.includes(s))); stats.sharedEx=(stats.sharedEx||[]); if(stats.sharedEx.length<8) stats.sharedEx.push(sh+' @ '+st.slice(0,90)); }
    if(i<2) samples.push(L+' | '+r+' '+JSON.stringify(p)+' '+JSON.stringify(g)+' '+JSON.stringify(q)+' '+JSON.stringify(ko)+' '+bone+'\n  [S] '+r3.short+'\n  [M] '+r3.medium+'\n  [L] '+r3.long);
  }
}
function chance(p){return Math.random()<p} function pick(a){return a[Math.floor(Math.random()*a.length)]}
const tot=stats.n/3;
console.log('presses',tot,'drafts',stats.n);
console.log('over size limit:',stats.wcOut,' repeats/draft:',Object.fromEntries(Object.entries(stats.reps).map(([k,v])=>[k,(v/tot).toFixed(2)])));
console.log('name twice:',stats.name2,' no name:',stats.noName,' Bareilly rate:',(stats.bare/stats.n).toFixed(2),' emoji rate:',(stats.emoji/stats.n).toFixed(2),' end without stop:',(stats.endNoDot/stats.n).toFixed(2));
console.log('presses with a shared sentence:',stats.shared,' sentences equal to a posted review:',stats.postedHit);
console.log('long drafts with >3 repeats:',stats.rep3||0,' shorts over 22 words:',stats.s22||0,' drafts under the minimum:',stats.under||0);
const hits={}; stats.bad.filter(b=>b.startsWith('POSTED')).forEach(b=>{const k=b.split('  ⊂  ')[0]; hits[k]=(hits[k]||0)+1;}); console.log('distinct posted hits',Object.keys(hits).length); Object.entries(hits).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>console.log('   ',v,k.slice(0,150)));
(stats.sharedEx||[]).forEach(x=>console.log('  shared:',x));
console.log('BAD',stats.bad.length); stats.bad.slice(0,12).forEach(b=>console.log('  ',b.slice(0,300)));
if(process.argv[4]==='samples') samples.forEach(s=>console.log(s+'\n'));
const reds=[];
if(stats.bad.length) reds.push(stats.bad.length+' broken or posted');
if(stats.name2) reds.push('name twice '+stats.name2);
if(Object.values(stats.noName).some(v=>v)) reds.push('no name');
if(stats.shared) reds.push('shared sentence '+stats.shared);
if(stats.postedHit) reds.push('posted sentence '+stats.postedHit);
if(Object.values(stats.wcOut).some(v=>v)) reds.push('over size '+JSON.stringify(stats.wcOut));
if((stats.rep3||0)>tot*0.01) reds.push('long >3 repeats '+stats.rep3);
if((stats.order||0)>tot*0.01) reds.push('long shorter than medium '+stats.order);
console.log('posted texts checked:',posted.size,'sentences');
console.log(reds.length?'WALK RED '+reds.join(' · '):'WALK OK '+stats.n+' drafts, every rule green');
process.exit(reds.length?1:0);
