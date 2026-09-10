(function(root){
'use strict';
const day=t=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(t));
function blank(){return {status:'未学习',seconds:0,wrong:0,answers:0,correct:0,notes:[],highlights:[],attempts:[]};}
function reduce(events){
  const s={units:{},days:{},settings:{}};
  const ordered=[...new Map(events.map(e=>[e.id,e])).values()].sort((a,b)=>(a.seq||Infinity)-(b.seq||Infinity));
  for(const e of ordered){
    const p=e.payload||{};
    if(e.kind==='settings'){Object.assign(s.settings,p);continue;}
    if(e.kind==='plan'){Object.assign(s.days[p.day]??={seconds:0},{plan:p});continue;}
    if(!e.unit_id)continue;
    const u=s.units[e.unit_id]??=blank();
    if(e.kind==='status')u.status=p.value;
    if(e.kind==='note')u.notes.push({text:p.text,id:e.id,at:e.created_at});
    if(e.kind==='bookmark')u.bookmark=p.value;
    if(e.kind==='highlight'&&!u.highlights.includes(p.text))u.highlights.push(p.text);
    if(e.kind==='answer'){
      u.answers++;u.correct+=p.correct?1:0;u.wrong+=p.correct?0:1;u.lastCorrect=p.correct;
      u.attempts.push({question_id:p.question_id,response:p.response,correct:p.correct,type:p.type,at:e.created_at});
      const days=Number(p.review_days)||(p.correct?3:1);
      u.due=new Date(new Date(e.created_at).getTime()+days*86400000).toISOString();
    }
    if(e.kind==='time'){
      u.seconds+=p.seconds||0;
      const d=day(e.created_at);(s.days[d]??={seconds:0}).seconds+=p.seconds||0;
    }
  }
  return s;
}
const api={day,reduce};if(typeof module!=='undefined')module.exports=api;else root.TQModel=api;
})(typeof window!=='undefined'?window:globalThis);
