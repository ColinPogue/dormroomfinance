(function (root) {
  'use strict';
  const fields = ['income','housing','food','transport','bills','debt','flexible','savings','annual'];
  function calculate(values) {
    for (const key of fields) {
      if (!Number.isFinite(values[key]) || values[key] < 0 || values[key] > 10000000) throw new Error('Enter a number from 0 to 10,000,000 for every field.');
    }
    const expenses = ['housing','food','transport','bills','debt','flexible'].reduce((sum,key)=>sum+values[key],0);
    const monthlyIrregular = values.annual / 12;
    return {income:values.income,expenses,monthlyIrregular,savings:values.savings,balance:Math.round((values.income-expenses-monthlyIrregular-values.savings + Number.EPSILON)*100)/100 || 0};
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {calculate};
  if (typeof document === 'undefined') return;
  const form = document.getElementById('budget-form');
  if (!form) return;
  const money = n => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(n);
  let current = null;
  function update() {
    try {
      const values = Object.fromEntries(fields.map(key=>{const el=form.elements[key]; return [key,el.value.trim()==='' ? NaN : Number(el.value)];}));
      current=calculate(values);
      document.getElementById('budget-error').textContent='';
      for (const key of ['income','expenses','monthlyIrregular','savings','balance']) document.getElementById('result-'+key).textContent=money(current[key]);
      document.getElementById('result-note').textContent=current.balance<0 ? 'Your plan is over budget. Revisit flexible spending, housing, or income before committing. Borrowing does not make a recurring shortfall disappear.' : current.balance===0 ? 'Every dollar has a job. Check that your irregular costs and cash cushion are realistic.' : 'This amount is still unassigned. Consider upcoming costs, a cash cushion, or extra debt payments before treating it as spending money.';
      document.getElementById('budget-download').disabled=false;
    } catch (error) {
      current=null;
      document.getElementById('budget-error').textContent=error.message;
      document.getElementById('result-balance').textContent='—';
      document.getElementById('result-note').textContent='Complete all fields to see your budget. Use 0 for a cost you do not have.';
      for (const key of ['income','expenses','monthlyIrregular','savings']) document.getElementById('result-'+key).textContent='—';
      document.getElementById('budget-download').disabled=true;
    }
  }
  form.addEventListener('input',update);
  form.addEventListener('submit',e=>{e.preventDefault();update();});
  document.getElementById('budget-download').addEventListener('click',()=>{
    if(!current) return;
    const rows=[['Monthly student budget','Amount USD'],...fields.map(k=>[k,form.elements[k].value]),['monthly irregular reserve',current.monthlyIrregular.toFixed(2)],['unassigned monthly balance',current.balance.toFixed(2)]];
    const blob=new Blob([rows.map(r=>r.join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='my-student-budget.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  update();
})(typeof globalThis !== 'undefined' ? globalThis : this);
