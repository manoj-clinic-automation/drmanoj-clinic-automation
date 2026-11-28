const fs=require('fs'), {JSDOM}=require(process.env.HOME+'/s542/node_modules/jsdom');
const html=fs.readFileSync(process.argv[2],'utf8'), desk=JSON.parse(fs.readFileSync(process.argv[3],'utf8')), v10=process.argv[4]!=='v9';
if(!v10){delete desk.v10;}
const rows={ok:true,at:'2026-11-28T12:30',reports:{purchase_to:'25-11-2026',closing_as_on:'27-11-2026',closing_at:'x',kind_word:'',sale_to:'',closing_printed:'',built_at:''},rows:[],counts:[],totals:{}};
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,beforeParse(w){
  w.fetch=function(u){var b=u.indexOf('/api/desk')>=0?desk:(u.indexOf('/api/rows')>=0?rows:{ok:false});return Promise.resolve({json:function(){return Promise.resolve(JSON.parse(JSON.stringify(b)));}});};}});
setTimeout(function(){const d=dom.window.document, R=[];
  function ok(n,c,x){R.push(!!c);console.log((c?'PASS':'FAIL')+'  '+n+(c?'':'  -- '+String(x).slice(0,200)));}
  if(v10){
  const b1=d.querySelectorAll('#band1 details.row'), b2=[].slice.call(d.querySelectorAll('#band2 > details.row')).slice(0,desk.band2.length);
  ok('D1 band 1 draws every write-off waiting for Amir, first on the page', b1.length===desk.band1.length && d.querySelector('#desk .card').id==='band1', b1.length+' / '+desk.band1.length);
  ok('D2 band 1 shows the 3-step track and the month total + the loss register link', d.querySelectorAll('#band1 .trk').length===desk.band1.length && /cost ₹/.test(d.querySelector('#band1 .lossl').textContent) && d.querySelector('#band1 a[href="/finance/stockcheck/losses"]'));
  ok('D3 band 2 draws every count of today (then the earlier ones waiting, then the week folded), second', d.querySelectorAll('#band2 > details.row').length===desk.band2.length+desk.earlier.length && d.querySelectorAll('#band2 details.sub details.row').length===desk.week.length && d.querySelectorAll('#desk > .card')[1].id==='band2');
  const sur=b2.filter(function(x){return /more than Marg/.test(x.textContent);});
  ok('D4 a surplus says never a loss; the delivery line appears from Marg\'s purchases-to day', sur.length && sur.every(function(x){return /likely a delivery not yet in Marg/.test(x.textContent);}), sur.length);
  ok('D5 the earlier allowance rows stay visible with the group button', d.querySelector('#band2 button[data-act="allow"]') && d.querySelectorAll('#band2 > details.row').length>=desk.band2.length+desk.earlier.length);
  const f3=['b3way','b3old','b3rec','b3inq'].filter(function(i){return d.getElementById(i);});
  ok('D6 band 3: the boxes as folds, all closed', f3.length>=3 && [].slice.call(d.querySelectorAll('#band3 > details')).every(function(x){return !x.open;}), f3.join(','));
  ok('D7 no box 1 drawn (band 2 carries it); box numbers gone from the folds', !d.getElementById('dk1') && !/[0-9] · On its way/.test(d.getElementById('band3').innerHTML));
  const n1=[].slice.call(d.querySelectorAll('#band1 details.row .sumit')).map(function(e){return e.textContent;}), nw=[].slice.call(d.querySelectorAll('#b3way details.row')).filter(function(x){return !/band 1 above/.test(x.textContent);}).map(function(x){return x.querySelector('.sumit').textContent;});
  const twice=n1.filter(function(k){return nw.indexOf(k)>=0;});
  ok('D8 no write-off row twice (band 1 vs the on-their-way fold)', twice.length===0, twice.length+' twice');
  ok('D9 the chips: write-offs, counted today, on their way, old counts', /your write-offs/.test(d.querySelector('#desk .chips').textContent) && /counted today/.test(d.querySelector('#desk .chips').textContent));
  const opn=d.getElementById('b3rec'); if(opn){opn.open=true; dom.window.renderDesk(); ok('D10 a fold left open stays open when the page redraws (after a tap)', d.getElementById('b3rec').open);} else ok('D10 fold', false, 'no b3rec');
  ok('D11 no confirm / alert / prompt in the page', !/confirm\(|alert\(|prompt\(/.test(html));
  } else {
  ok('E1 without the bands the page draws the boxes as before (renderDeskV9)', d.getElementById('dk1') && d.getElementById('dk2') && !d.getElementById('band1'));
  }
  console.log('DOM '+R.filter(Boolean).length+'/'+R.length);},1500);
