const fs=require('fs'),vm=require('vm'),crypto=require('crypto');
const src=fs.readFileSync('gas/WebApp.gs','utf8');
let props={DASH_KEY:'MASTER-k',AKEY_11:'shavez-k',AKEY_14:'alisha-k'}, cache={}, fetchLog=[], nextResp=null;
const ctx={console,JSON,String,Object,Date,Math,RegExp,Array,Number,
 PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]??null})},
 CacheService:{getScriptCache:()=>({get:k=>cache[k]??null,put:(k,v)=>{cache[k]=v}})},
 LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})},
 Utilities:{DigestAlgorithm:{SHA_256:1},computeDigest:(a,s)=>[...crypto.createHash('sha256').update(s).digest()],
   base64EncodeWebSafe:b=>Buffer.from(b.map(x=>x&255)).toString('base64url')},
 UrlFetchApp:{fetch:(u,o)=>{fetchLog.push([u,o]);return nextResp}},
 SpreadsheetApp:{openById:()=>{throw new Error('no sheet')}},
 HtmlService:{}, Logger:{log(){}}, CFG:{SHEET_ID_PROP:'SHEET_ID'}};
vm.createContext(ctx); vm.runInContext(src,ctx);
const R=(code,body)=>({getResponseCode:()=>code,getContentText:()=>JSON.stringify(body)});
let n=0; const ok=(c,l)=>{if(!c){console.log('RED',l);process.exit(1)} n++};
const P='abc_DEF-1.sig_2-x';
nextResp=R(200,{ok:true,user:'shavez',role:'staff'}); let r=ctx.ssoExchange(P);
ok(r.ok&&r.key==='shavez-k','shavez gets his own key');
ok(fetchLog[0][0]==='https://followup.dr-manoj.in/portal/sso/tracker-redeem'&&fetchLog[0][1].payload.p===P,'asks the portal with the pass');
r=ctx.ssoExchange(P); ok(!r.ok&&r.reason==='used','second use refused'); ok(fetchLog.length===1,'second use never asks the portal');
nextResp=R(200,{ok:true,user:'manoj',role:'doctor'}); r=ctx.ssoExchange(P+'a'); ok(r.ok&&r.key==='MASTER-k','doctor gets the master key');
nextResp=R(200,{ok:true,user:'manoj',role:'staff'}); r=ctx.ssoExchange(P+'b'); ok(!r.ok,'manoj without doctor role refused');
nextResp=R(200,{ok:true,user:'shivani',role:'staff'}); r=ctx.ssoExchange(P+'c'); ok(!r.ok&&r.reason==='not linked','shivani with no AKEY_12 -> not linked');
nextResp=R(200,{ok:true,user:'bhawna',role:'doctor'}); r=ctx.ssoExchange(P+'d'); ok(!r.ok,'unmapped user refused');
nextResp=R(200,{ok:false}); r=ctx.ssoExchange(P+'e'); ok(!r.ok,'portal says no');
nextResp=R(502,{}); r=ctx.ssoExchange(P+'f'); ok(!r.ok,'portal down');
nextResp={getResponseCode:()=>200,getContentText:()=>'<html>'}; r=ctx.ssoExchange(P+'g'); ok(!r.ok,'portal html');
ctx.UrlFetchApp.fetch=()=>{throw new Error('dns')}; r=ctx.ssoExchange(P+'h'); ok(!r.ok,'fetch throws');
for(const b of ['',null,'nodot','a.b.c','<x>.y','a'.repeat(700)+'.b']){ r=ctx.ssoExchange(b); ok(!r.ok,'malformed '+String(b).slice(0,6)); }
props.SSO_USER_EXT='{"shivani":"14"}'; ctx.UrlFetchApp.fetch=()=>R(200,{ok:true,user:'Shivani',role:'staff'});
r=ctx.ssoExchange(P+'i'); ok(r.ok&&r.key==='alisha-k','Script Property map wins (and case-insensitive)');
props.SSO_USER_EXT='{bad json'; ctx.UrlFetchApp.fetch=()=>R(200,{ok:true,user:'shavez',role:'staff'});
r=ctx.ssoExchange(P+'j'); ok(r.ok&&r.key==='shavez-k','bad property -> built-in map');
// old paths untouched
ok(ctx.dashRole_('MASTER-k')==='full'&&ctx.dashRole_('shavez-k')==='staff'&&ctx.dashRole_('nope')==='none','dashRole_ unchanged');
console.log('GAS HARNESS OK '+n+'/'+n);
