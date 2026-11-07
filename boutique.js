/* Advisory service alignment, deliberately separate from A/B/C and facility services. */
(function(root){
  'use strict';
  function filter(rows,profiles,options={}){
    const minimum=Number(options.minimum||0);
    const fold=value=>String(value||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
    const words=fold(options.query).trim().split(/\s+/).filter(Boolean);
    return rows.filter(row=>{
      const p=profiles[row.id];if(!p)return false;
      if(words.length){const text=(options.texts?.get(row.id)||fold([row.name,row.company_id,row.city,row.country,...(row.categories||[])].join(' ')))+' '+fold((p.research_terms||[]).join(' '));if(!words.every(w=>text.includes(w)))return false;}
      return (!options.region||p.region===options.region)&&(!options.specialisation||p.signals[options.specialisation])&&(!options.cinematics||p.signals.cinematics)&&(!options.realtime||p.signals.realtime)&&(!options.performance||p.signals.character||p.signals.pipeline)&&(!options.size||p.size_claim===options.size)&&p.score>=minimum&&(!options.status||p.research_status===options.status);
    });
  }
  const api={filter};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.MotionXBoutique=api;
})(globalThis);
