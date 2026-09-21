const fs=require('fs'),vm=require('vm');
const h=fs.readFileSync('gas/Dashboard.html','utf8');
const a=h.indexOf('  google.script.url.getLocation(function(loc){'); const b=h.indexOf('  });',a)+5;
const block=h.slice(a,b);
let n=0; const ok=(c,l)=>{if(!c){console.log('RED',l);process.exit(1)} n++};
function run(param, store, exch){
  const calls=[]; const ls=Object.assign({},store);
  const ctx={String,localStorage:{getItem:k=>ls[k]??null},
    tryKey:(k,x)=>calls.push('try:'+k), showLogin:x=>calls.push('login'),
    google:{script:{url:{getLocation:f=>f({parameter:param})},
      run:{withSuccessHandler(s){this.s=s;return this},withFailureHandler(f){this.f=f;return this},
           ssoExchange(p){calls.push('exch:'+p); if(exch==='throw') this.f(new Error('x')); else this.s(exch);}}}}};
  vm.createContext(ctx); vm.runInContext(block,ctx); return calls.join(' ');
}
ok(run({sso:'P1'},{}, {ok:true,key:'K'})==='exch:P1 try:K','pass -> signed in with the key');
ok(run({sso:'P1'},{clinicSignedOut:'1'},{ok:true,key:'K'})==='exch:P1 try:K','fresh tap beats an earlier sign-out');
ok(run({sso:'P1'},{clinicSignedOut:'1'},{ok:false})==='exch:P1 login','used pass after sign-out -> login');
ok(run({sso:'P1'},{clinicDashKey:'OLD'},{ok:false})==='exch:P1 try:OLD','used pass -> remembered key as before');
ok(run({sso:'P1'},{},'throw')==='exch:P1 login','server error -> login');
ok(run({},{},null)==='login','no pass, no key -> login (old)');
ok(run({k:'KK'},{},null)==='try:KK','?k= still works (old)');
ok(run({},{clinicDashKey:'OLD'},null)==='try:OLD','remembered key still works (old)');
ok(run({k:'KK'},{clinicSignedOut:'1'},null)==='login','signed out ignores ?k= (old F-11)');
console.log('PAGE HARNESS OK '+n+'/'+n);
