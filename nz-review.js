(function(){
  'use strict';
  function matches(text,status,query,state,source='',selectedSource=''){
    return text.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())&&(!state||status===state)&&(!selectedSource||source===selectedSource);
  }
  if(typeof module!=='undefined')module.exports={matches};
  if(typeof document==='undefined')return;
  const q=document.getElementById('q'),state=document.getElementById('state'),source=document.getElementById('source');if(!q||!state||!source)return;
  const rows=[...document.querySelectorAll('#observations tr')];
  function update(){let count=0;for(const row of rows){row.hidden=!matches(row.textContent,row.dataset.status,q.value,state.value,row.dataset.source,source.value);if(!row.hidden)count++;}document.getElementById('count').textContent=count+' of '+rows.length+' observations';}
  for(const control of [q,state,source])control.addEventListener(control===q?'input':'change',update);update();
}());
