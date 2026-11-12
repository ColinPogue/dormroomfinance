(function(){
 'use strict';
 function cents(value){
  const text=String(value).trim();
  if(!/^(?:\d{1,7}(?:\.\d{0,2})?|\.\d{1,2})$/.test(text))throw Error('Enter a nonnegative amount with no more than two decimal places.');
  const n=Number(text);
  if(n>1000000)throw Error('Keep each amount at $1,000,000 or less.');
  return Math.round(n*100);
 }
 function settle(people){
  if(!Array.isArray(people)||people.length<2||people.length>6)throw Error('Choose two to six roommates.');
  const names=new Set();
  const rows=people.map((p,i)=>{
   const name=String(p.name||'').trim()||`Roommate ${i+1}`;
   if(name.length>40||names.has(name.toLowerCase()))throw Error('Use a different short name for each roommate.');
   names.add(name.toLowerCase());return {name,paid:cents(p.paid)};
  });
  const total=rows.reduce((sum,p)=>sum+p.paid,0),base=Math.floor(total/rows.length),remainder=total%rows.length;
  rows.forEach((p,i)=>{p.share=base+(i<remainder?1:0);p.balance=p.paid-p.share;});
  const creditors=rows.filter(p=>p.balance>0).map(p=>({name:p.name,left:p.balance}));
  const debtors=rows.filter(p=>p.balance<0).map(p=>({name:p.name,left:-p.balance}));
  const transfers=[];let i=0,j=0;
  while(i<debtors.length&&j<creditors.length){
   const amount=Math.min(debtors[i].left,creditors[j].left);
   transfers.push({from:debtors[i].name,to:creditors[j].name,cents:amount});
   debtors[i].left-=amount;creditors[j].left-=amount;
   if(!debtors[i].left)i++;if(!creditors[j].left)j++;
  }
  return {total,rows,transfers};
 }
 if(typeof module!=='undefined'&&module.exports)module.exports={settle,cents};
 if(typeof document==='undefined')return;
 const form=document.getElementById('roommates-form');if(!form)return;
 const count=document.getElementById('roommate-count'),list=document.getElementById('roommate-payments'),summary=document.getElementById('roommate-summary'),error=document.getElementById('roommate-error');
 const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(n/100);
 function update(){
  const n=Number(count.value);
  for(let i=0;i<6;i++)document.getElementById(`roommate-row-${i}`).hidden=i>=n;
  list.replaceChildren();summary.value='';document.getElementById('roommate-copy-status').textContent='';
  try{
   const result=settle(Array.from({length:n},(_,i)=>({name:form.elements[`name-${i}`].value,paid:form.elements[`paid-${i}`].value})));
   error.textContent='';document.getElementById('roommate-total').textContent=money(result.total);
   document.getElementById('roommate-status').textContent=result.transfers.length?'Here is one way to settle the balance.':'Everyone is square. No transfers needed.';
   for(const t of result.transfers){const li=document.createElement('li');li.textContent=`${t.from} pays ${t.to} ${money(t.cents)}`;list.append(li);}
   const shares=result.rows.map(p=>`${p.name}: paid ${money(p.paid)}, share ${money(p.share)}`).join('\n');
   summary.value=`Shared total: ${money(result.total)}\nEqual split among ${n} roommates\n\n${shares}\n\n`+(result.transfers.map(t=>`${t.from} pays ${t.to} ${money(t.cents)}`).join('\n')||'Everyone is square.');
  }catch(e){error.textContent=e.message;document.getElementById('roommate-total').textContent='—';document.getElementById('roommate-status').textContent='Check the names and amounts to calculate your split.';}
 }
 form.addEventListener('input',update);form.addEventListener('change',update);form.addEventListener('submit',e=>e.preventDefault());
 document.getElementById('roommate-copy').addEventListener('click',async()=>{
  if(!summary.value)return;
  try{await navigator.clipboard.writeText(summary.value);document.getElementById('roommate-copy-status').textContent='Summary copied.';}
  catch{summary.focus();summary.select();document.getElementById('roommate-copy-status').textContent='Select and copy the summary below.';}
 });
 update();
})();
