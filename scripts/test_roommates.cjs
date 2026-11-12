const assert=require('node:assert/strict');
const {settle,cents}=require('../static/tools/roommates.js');
const example=settle([{name:'Alex',paid:'90'},{name:'Sam',paid:'30'},{name:'Jordan',paid:'0'}]);
assert.equal(example.total,12000);assert.deepEqual(example.transfers,[{from:'Sam',to:'Alex',cents:1000},{from:'Jordan',to:'Alex',cents:4000}]);
assert.equal(cents('0.29'),29);assert.equal(cents('.50'),50);
assert.deepEqual(settle([{name:'A',paid:'10'},{name:'B',paid:'10'}]).transfers,[]);
assert.deepEqual(settle([{name:'A',paid:'0'},{name:'B',paid:'0.01'},{name:'C',paid:'0'}]).transfers,[{from:'A',to:'B',cents:1}]);
for(const value of ['','-1','NaN','Infinity','1.001','1000001','<script>'])assert.throws(()=>cents(value));
assert.throws(()=>settle([{name:'Alex',paid:0},{name:'alex',paid:0}]));
assert.throws(()=>settle([{name:'A',paid:1}]));
for(let n=2;n<=6;n++)for(let scenario=0;scenario<100;scenario++){
 const people=Array.from({length:n},(_,i)=>({name:`P${i}`,paid:((scenario*7919+i*12347)%100003/100).toFixed(2)}));
 const result=settle(people);assert.equal(result.rows.reduce((x,p)=>x+p.share,0),result.total);
 for(const row of result.rows){
  const outgoing=result.transfers.filter(t=>t.from===row.name).reduce((a,t)=>a+t.cents,0);
  const incoming=result.transfers.filter(t=>t.to===row.name).reduce((a,t)=>a+t.cents,0);
  assert.equal(row.paid+outgoing-incoming,row.share);
 }
 assert.ok(result.transfers.length<=n-1);
}
console.log('Roommate splitter: examples, odd cents, invalid inputs, and 500 settlement-conservation scenarios passed.');
