// Run with Playwright installed. Starts its own server and closes browser/server on failure.
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const server=spawn('python3',['-m','http.server','8097','--bind','127.0.0.1','--directory',path.join(root,'public')],{stdio:'ignore'});
const base='http://127.0.0.1:8097';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 let browser;
 try {
  for(let i=0;i<30;i++){try{if((await fetch(base)).ok)break;}catch{}if(i===29)throw Error('Preview server did not start');await sleep(200);}
  browser=await chromium.launch();
  fs.mkdirSync(path.join(root,'qa-screenshots'),{recursive:true});
  const problems=[];
  for(const width of [1440,390,320]){
   const page=await browser.newPage({viewport:{width,height:1000}});
   page.on('pageerror',e=>problems.push(e.message));
   page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)problems.push(`${r.status()} ${r.url()}`);});
   for(const route of ['/','/start-here/','/tools/','/tools/student-budget/','/tools/roommate-bill-splitter/','/posts/best-credit-card-for-college-students-with-no-credit-history/','/categories/credit-cards/']){
    const response=await page.goto(base+route,{waitUntil:'networkidle'});assert.equal(response.status(),200);
    assert.equal(await page.locator('h1').count(),1,`one H1 on ${route}`);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),`No horizontal overflow at ${width}: ${route}`);
    assert.ok(await page.locator('.site-nav').isVisible());
    const images=await page.locator('img').evaluateAll(imgs=>imgs.filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src));assert.deepEqual(images,[]);
    if(route==='/'){
     await page.screenshot({path:path.join(root,'qa-screenshots',`home-${width}.png`),fullPage:true});
     if(width!==320){
      const preview=await page.screenshot({type:'jpeg',quality:45,fullPage:false});
      console.log(`DRF_IMAGE_${width}_BEGIN`);
      for(const chunk of preview.toString('base64').match(/.{1,4000}/g))console.log(chunk);
      console.log(`DRF_IMAGE_${width}_END`);
     }
    }
   }
   await page.goto(base+'/tools/student-budget/',{waitUntil:'networkidle'});
   await page.waitForFunction(()=>document.querySelector('#result-balance').textContent==='$100.00');
   await page.locator('#housing').fill('900');
   await page.waitForFunction(()=>document.querySelector('#result-balance').textContent==='-$150.00');
   await page.locator('#income').fill('');
   await page.waitForFunction(()=>document.querySelector('#budget-download').disabled);
   assert.notEqual(await page.locator('#budget-error').textContent(),'');
   await page.locator('#income').fill('1500');
   const downloadEvent=page.waitForEvent('download');await page.locator('#budget-download').click();
   const download=await downloadEvent;assert.equal(download.suggestedFilename(),'my-student-budget.csv');
   await page.goto(base+'/tools/roommate-bill-splitter/',{waitUntil:'networkidle'});
   await page.waitForFunction(()=>document.querySelector('#roommate-total').textContent==='$120.00');
   assert.equal(await page.locator('#roommate-payments li').count(),2);
   await page.locator('#roommate-count').selectOption('2');
   await page.waitForFunction(()=>document.querySelector('#roommate-payments').textContent.includes('$30.00'));
   await page.locator('#roommate-name-1').fill('Alex');
   await page.waitForFunction(()=>document.querySelector('#roommate-error').textContent.includes('different'));
   await page.locator('#roommate-name-1').fill('<b>Sam</b>');
   assert.equal(await page.locator('#roommate-payments b').count(),0);
   assert.ok((await page.locator('#roommate-summary').inputValue()).includes('<b>Sam</b>'));
   await page.goto(base+'/search/',{waitUntil:'networkidle'});
   await page.locator('#searchInput').fill('credit');
   await page.waitForFunction(()=>document.querySelectorAll('#searchResults li').length>0);
   await page.close();
  }
  assert.deepEqual(problems,[]);
  console.log('Browser QA passed: 3 viewport sizes, navigation, 21 page loads, no overflow, images, search, calculators, invalid input, exact bill splits, safe names, and downloads.');
 } finally {if(browser)await browser.close();server.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
