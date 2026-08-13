/* wa_widget.js — clinic portal shared WhatsApp composer (S172, Phase A.1)
   Served from /root/wa/wa_portal/wa_widget.js — edit + drop, no restart.
   API:  WAWidget.open({ phone, name, template, values, minimal, onsent })
     phone/name   prefill the mobile + any name field
     template     preselect a template by name
     values       {key:value} prefill specific fields (e.g. from casepack/console)
     minimal      true -> fields already supplied via values are locked (read-only),
                  so contextual sends show only the part that needs editing
     onsent(res)  callback after a successful send
   Date/number fields render as native pickers and are converted to the
   WABA-safe display format ("05 Aug 2026", "07 Aug 2026, 6:30 PM"). */
(function () {
  var TPL = null, DRY = true, loaded = false;
  var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function mask(p){var d=(''+p).replace(/\D/g,'');
    return d.length>=4?'\u2022\u2022\u2022\u2022'+d.slice(-4):'\u2022\u2022\u2022\u2022';}
  function fmtDate(iso){ if(!iso) return ''; var p=iso.split('-');
    if(p.length<3) return iso; return p[2]+' '+(MON[(+p[1])-1]||'')+' '+p[0]; }
  function fmtDT(v){ if(!v) return ''; var a=v.split('T');
    if(a.length<2) return fmtDate(a[0]); var t=a[1].split(':'); var h=+t[0], m=t[1]||'00';
    var ap=h>=12?'PM':'AM'; var h12=(h%12)||12; return fmtDate(a[0])+', '+h12+':'+m+' '+ap; }
  function daysOverdue(iso){ if(!iso) return ''; var d=new Date(iso+'T00:00:00');
    if(isNaN(d)) return ''; var n=new Date();
    var t=new Date(n.getFullYear(),n.getMonth(),n.getDate());
    var diff=Math.round((t-d)/86400000); return diff>0?String(diff):'0'; }

  function styleOnce(){
    if(document.getElementById('wawidget-css')) return;
    var s=document.createElement('style'); s.id='wawidget-css';
    s.textContent=".waw-ov{position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;"
    +"align-items:flex-start;justify-content:center;padding:18px 10px;overflow:auto;z-index:9999}"
    +".waw-box{background:#2F3E3D;color:#E7EEEC;border:1px solid #3D4F4D;border-radius:14px;"
    +"max-width:520px;width:100%;padding:16px;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif}"
    +".waw-box h3{margin:0 0 4px;font-size:17px}.waw-sub{color:#9DB0AC;font-size:12.5px;margin-bottom:10px}"
    +".waw-dry{background:rgba(224,179,106,.14);color:#E0B36A;border-radius:8px;padding:7px 10px;font-size:12.5px;margin-bottom:10px}"
    +".waw-l{display:block;font-size:12px;color:#9DB0AC;margin:9px 0 3px}"
    +".waw-in,.waw-sel{width:100%;box-sizing:border-box;padding:9px 10px;border:1px solid #3D4F4D;"
    +"border-radius:9px;background:#26332F;color:#E7EEEC;font-size:14px}"
    +".waw-in[readonly]{opacity:.7}"
    +".waw-in::-webkit-calendar-picker-indicator{filter:invert(.8)}"
    +".waw-prev{background:#26332F;border:1px solid #3D4F4D;border-radius:10px;padding:10px;"
    +"font-size:13px;line-height:1.5;margin-top:8px;white-space:pre-wrap;color:#CDE0DA}"
    +".waw-row{display:flex;gap:8px;margin-top:14px}"
    +".waw-btn{flex:1;padding:11px;border-radius:10px;border:none;font-size:14px;font-weight:700;cursor:pointer}"
    +".waw-send{background:#25D366;color:#053}.waw-send:disabled{opacity:.5;cursor:default}"
    +".waw-cancel{background:transparent;color:#9DB0AC;border:1px solid #3D4F4D}"
    +".waw-fb{display:block;text-align:center;margin-top:12px;font-size:12.5px;color:#9DB0AC}"
    +".waw-fb a{color:#25D366;text-decoration:none;font-weight:600}"
    +".waw-toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#12201F;"
    +"color:#fff;padding:10px 16px;border-radius:20px;font-size:13px;z-index:10000;max-width:88%;text-align:center}";
    document.head.appendChild(s);
  }
  function toast(msg){var t=document.createElement('div');t.className='waw-toast';t.textContent=msg;
    document.body.appendChild(t);setTimeout(function(){t.remove();},4200);}
  function load(cb){
    if(loaded){cb();return;}
    fetch('/portal/wa/templates').then(function(r){return r.json();}).then(function(j){
      TPL=j.templates||[]; DRY=!!j.dry; loaded=true; cb();
    }).catch(function(){alert('Could not load WhatsApp templates.');});
  }
  function renderPreview(t,vals){
    var p=t.preview||'';
    t.fields.forEach(function(f){
      var v=vals[f.key]; p=p.split('{'+f.key+'}').join(v?v:('['+f.label+']'));
    });
    return p;
  }

  function open(opts){
    opts=opts||{}; styleOnce();
    load(function(){
      var ov=document.createElement('div'); ov.className='waw-ov';
      var box=document.createElement('div'); box.className='waw-box'; ov.appendChild(box);
      var groups={}; TPL.forEach(function(t){(groups[t.group]=groups[t.group]||[]).push(t);});
      var optHTML=''; Object.keys(groups).forEach(function(g){
        optHTML+='<optgroup label="'+esc(g)+'">';
        groups[g].forEach(function(t){optHTML+='<option value="'+esc(t.name)+'">'+esc(t.title)+'</option>';});
        optHTML+='</optgroup>';});
      box.innerHTML=
        '<h3>Send WhatsApp</h3>'
        +'<div class="waw-sub">from the clinic business number \u00b7 9358008080</div>'
        +(DRY?'<div class="waw-dry">\u26a0 TEST MODE — nothing is actually sent. Sends are logged only.</div>':'')
        +'<label class="waw-l">Patient mobile</label>'
        +'<input class="waw-in" id="waw-phone" inputmode="numeric" placeholder="10-digit mobile" value="'+esc(opts.phone||'')+'">'
        +'<label class="waw-l">Message template</label>'
        +'<select class="waw-sel" id="waw-tpl">'+optHTML+'</select>'
        +'<div id="waw-fields"></div>'
        +'<div class="waw-l">Preview</div><div class="waw-prev" id="waw-prev"></div>'
        +'<div class="waw-row"><button class="waw-btn waw-cancel" id="waw-cancel">Cancel</button>'
        +'<button class="waw-btn waw-send" id="waw-send">Send</button></div>'
        +'<div class="waw-fb">Can\u2019t use a template? '
        +'<a id="waw-fb" target="_blank" rel="noopener">Send via your own WhatsApp \u2192</a></div>';
      document.body.appendChild(ov);

      var sel=box.querySelector('#waw-tpl'), fld=box.querySelector('#waw-fields'),
          prev=box.querySelector('#waw-prev'), phone=box.querySelector('#waw-phone'),
          fb=box.querySelector('#waw-fb');
      if(opts.template && TPL.some(function(t){return t.name===opts.template;})) sel.value=opts.template;

      function cur(){return TPL.filter(function(t){return t.name===sel.value;})[0];}
      function rawOf(key){var el=box.querySelector('#waw-f-'+key);return el?el.value:'';}
      function vals(){var t=cur(),o={};t.fields.forEach(function(f){
        var raw=rawOf(f.key);
        if(f.type==='date')o[f.key]=fmtDate(raw);
        else if(f.type==='datetime')o[f.key]=fmtDT(raw);
        else o[f.key]=(raw||'').trim();});return o;}
      function pad(n){return (n<10?'0':'')+n;}
      function todayISO(){var d=new Date();return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}
      function nowISO(){var d=new Date();return todayISO()+'T'+pad(d.getHours())+':'+pad(d.getMinutes());}
      function fieldInput(f){
        var id='waw-f-'+f.key, ro=(opts.minimal && opts.values && opts.values[f.key]!=null)?' readonly':'';
        var pre='', given=(opts.values && opts.values[f.key]!=null)?String(opts.values[f.key]):'';
        if(given) pre=given; else if(f.prefill_name && opts.name) pre=opts.name;
        if(f.type==='date'){
          var dv=/^\d{4}-\d{2}-\d{2}/.test(given)?given.slice(0,10):todayISO();   // default today, calendar picker
          return '<input type="date" class="waw-in" id="'+id+'" value="'+dv+'"'+ro+'>';
        }
        if(f.type==='datetime'){
          var tv=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(given)?given.slice(0,16):nowISO(); // default now
          return '<input type="datetime-local" class="waw-in" id="'+id+'" value="'+tv+'"'+ro+'>';
        }
        if(f.type==='number')   return '<input type="number" inputmode="numeric" class="waw-in" id="'+id+'" value="'+esc(pre)+'"'+ro+'>';
        return '<input class="waw-in" id="'+id+'" value="'+esc(pre)+'"'+ro+'>';
      }
      function drawFields(){
        var t=cur(),h='';
        t.fields.forEach(function(f){
          if(opts.minimal && opts.values && opts.values[f.key]!=null && f.type!=='date' && f.type!=='datetime'){
            return; // fully supplied non-date field: hide in minimal mode
          }
          h+='<label class="waw-l">'+esc(f.label)+'</label>'+fieldInput(f);
        });
        fld.innerHTML=h;
        t.fields.forEach(function(f){
          var el=box.querySelector('#waw-f-'+f.key); if(!el) return;
          function onchg(){
            t.fields.forEach(function(g){
              if(g.auto_from===f.key){
                var ael=box.querySelector('#waw-f-'+g.key);
                if(ael && f.type==='date') ael.value=daysOverdue(rawOf(f.key));
              }});
            upd();
          }
          el.addEventListener('input',onchg); el.addEventListener('change',onchg);
        });
        upd();
      }
      function waLink(){
        var ph=(phone.value||'').replace(/\D/g,'');
        if(ph.length===10) ph='91'+ph; else if(ph.length===11&&ph[0]==='0') ph='91'+ph.slice(1);
        fb.href='https://wa.me/'+ph+'?text='+encodeURIComponent(renderPreview(cur(),vals()));
      }
      function upd(){ prev.textContent=renderPreview(cur(),vals()); waLink(); }

      sel.addEventListener('change',drawFields);
      phone.addEventListener('input',waLink);
      box.querySelector('#waw-cancel').onclick=function(){ov.remove();};
      ov.addEventListener('click',function(e){if(e.target===ov)ov.remove();});
      box.querySelector('#waw-send').onclick=function(){
        var ph=phone.value.trim(), t=cur(), v=vals();
        for(var i=0;i<t.fields.length;i++){
          if(!v[t.fields[i].key]){toast('Fill in: '+t.fields[i].label);return;}
        }
        if(!confirm((DRY?'[TEST] ':'')+'Send "'+t.title+'" to '+mask(ph)+' from the clinic WhatsApp?'))return;
        var b=box.querySelector('#waw-send'); b.disabled=true; b.textContent='Sending\u2026';
        fetch('/portal/wa/send',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({phone:ph,template:t.name,values:v})})
          .then(function(r){return r.json();}).then(function(j){
            if(j.ok){toast((j.mode==='DRY'?'\u2705 TEST logged (not sent): ':'\u2705 Sent: ')+t.title);
              ov.remove(); if(opts.onsent)opts.onsent(j);}
            else{toast('\u274c '+(j.error||'send failed'));b.disabled=false;b.textContent='Send';}
          }).catch(function(){toast('\u274c network error');b.disabled=false;b.textContent='Send';});
      };
      drawFields();
    });
  }
  window.WAWidget={open:open};
})();
