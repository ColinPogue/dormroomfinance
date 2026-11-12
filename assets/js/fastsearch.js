// Search uses safe DOM text and handles typing, pasting, and clearing the field.
const input=document.getElementById('searchInput');
const list=document.getElementById('searchResults');
const status=document.getElementById('searchStatus');
let index=null;
function render(){
 if(!input||!list)return;
 list.replaceChildren();
 const terms=input.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
 if(!terms.length){status.textContent='Search the article library by topic or question.';return;}
 if(!index){status.textContent='Loading the article index…';return;}
 const results=index.map(item=>{
  const title=item.title.toLocaleLowerCase(),body=(item.summary+' '+item.content).toLocaleLowerCase();
  const match=terms.every(term=>title.includes(term)||body.includes(term));
  const score=terms.reduce((n,t)=>n+(title.includes(t)?5:0),0);
  return {item,match,score};
 }).filter(x=>x.match).sort((a,b)=>b.score-a.score).slice(0,20);
 for(const {item} of results){const li=document.createElement('li'),a=document.createElement('a');a.href=item.permalink;a.textContent=item.title;li.append(a);list.append(li);}
 status.textContent=results.length ? `${results.length} results shown. Refine your search for a closer match.` : 'No matches. Try a broader phrase such as credit, budget, or internship.';
}
if(input&&list){
 input.addEventListener('input',render);input.addEventListener('search',render);
 fetch('/index.json').then(r=>{if(!r.ok)throw Error('Index unavailable');return r.json();}).then(data=>{index=data.filter(x=>new URL(x.permalink,location.href).pathname.startsWith('/posts/'));render();}).catch(()=>{status.textContent='Search is temporarily unavailable. Browse all articles using the navigation above.';});
 render();
}
