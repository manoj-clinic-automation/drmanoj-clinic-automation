const fs=require('fs');
const p=process.env.HOME+'/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits/S211_HONESTERRORS/finance_approvals.html';
const src=fs.readFileSync(p,'utf8');
// pull the two shipped functions out of the shipped bytes
const cut=(name)=>{const i=src.indexOf('function '+name+'(');if(i<0)throw new Error('missing '+name);
  let d=0,j=src.indexOf('{',i);for(let k=j;k<src.length;k++){if(src[k]==='{')d++;else if(src[k]==='}'){d--;if(!d)return src.slice(i,k+1)}}};
const code=cut('srvJSON')+'\n'+cut('mpDismiss')+'\n';
let alerts=[],reloaded=0;
function run(fetchImpl){alerts=[];reloaded=0;
  const sandbox={alert:m=>alerts.push(String(m)),prompt:()=>'stray 12-June report',
                 loadPushes:()=>{reloaded++},fetch:fetchImpl,JSON,console};
  const fn=new Function('alert','prompt','loadPushes','fetch','JSON',code+';return mpDismiss;');
  return fn(sandbox.alert,sandbox.prompt,sandbox.loadPushes,sandbox.fetch,JSON);}
const resp=(status,body)=>Promise.resolve({status,text:()=>Promise.resolve(body)});
const checks=[];
const check=(n,c)=>{checks.push([n,c]);console.log((c?'  ok   ':'  FAIL ')+n)};
(async()=>{
 // 1 -- the exact fault Dr Manoj hit: a 500 HTML page from a database lock
 let d=run(()=>resp(500,'<!doctype html><html><title>500 Internal Server Error</title><body>sqlite3.OperationalError: database is locked</body></html>'));
 d(10); await new Promise(r=>setTimeout(r,30));
 check('500 HTML no longer says "network"', !/network/i.test(alerts.join(' ')));
 check('500 HTML reports the real status', /server error 500/.test(alerts.join(' ')));
 check('500 HTML shows the server\'s own words', /database is locked/.test(alerts.join(' ')));
 // 2 -- a 404, the other possibility we could not tell apart
 d=run(()=>resp(404,'<html><title>404 Not Found</title></html>'));
 d(10); await new Promise(r=>setTimeout(r,30));
 check('404 reports HTTP 404, not "network"', /server error 404/.test(alerts.join(' ')) && !/network/i.test(alerts.join(' ')));
 // 3 -- the route answering honestly in JSON still reads as before
 d=run(()=>resp(409,'{"ok":false,"error":"not_pending","message":"only a pending push can be removed; this one is applied"}'));
 d(10); await new Promise(r=>setTimeout(r,30));
 check('a real JSON refusal still shows the server sentence', /only a pending push/.test(alerts.join(' ')));
 // 4 -- success
 d=run(()=>resp(200,'{"ok":true,"id":10,"status":"dismissed"}'));
 d(10); await new Promise(r=>setTimeout(r,30));
 check('success still says "removed"', alerts.join(' ')==='removed');
 check('success still refreshes the list', reloaded===1);
 // 5 -- a GENUINE network failure must still be named as one
 d=run(()=>Promise.reject(new TypeError('Failed to fetch')));
 d(10); await new Promise(r=>setTimeout(r,30));
 check('a real network failure says the server was not reached at all', /could not be reached at all/.test(alerts.join(' ')));
 const bad=checks.filter(c=>!c[1]).length;
 console.log('\nREHEARSAL: '+(checks.length-bad)+'/'+checks.length+(bad?' -- FAILED':' -- ALL PASS'));
 process.exit(bad?1:0);
})();
