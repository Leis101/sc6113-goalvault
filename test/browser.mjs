// Local EIP-1193 test adapter, NOT the MetaMask extension and NOT Sepolia.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import ganache from 'ganache';
import {JsonRpcProvider,ContractFactory} from 'ethers';
import {chromium} from 'playwright';
import {startFlask} from './flask-process.mjs';
const chain=ganache.server({chain:{chainId:31337,hardfork:'shanghai'},wallet:{deterministic:true},logging:{quiet:true}});
await chain.listen(0,'127.0.0.1');
const rpcUrl=`http://127.0.0.1:${chain.address().port}`;
const p=new JsonRpcProvider(rpcUrl,undefined,{cacheTimeout:-1});
const a=JSON.parse(fs.readFileSync('artifacts/GoalVault.json'));
const c=await new ContractFactory(a.abi,a.bytecode,await p.getSigner(0)).deploy();
const deployment=await c.deploymentTransaction().wait();
const f='artifacts/ui-test-deployment.json';
fs.writeFileSync(f,JSON.stringify({address:await c.getAddress(),chainId:31337,deploymentBlock:deployment.blockNumber}));
const app=await startFlask(rpcUrl,f);
const url=app.url;
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||undefined,args:['--no-sandbox']});
const results=[];const pass=x=>{results.push({test:x,status:'PASS'});console.log('PASS',x);};
try{
 const missing=await browser.newPage({viewport:{width:1360,height:1100}});
 await missing.goto(url);await missing.locator('#network').filter({hasText:'Local test chain'}).waitFor();await missing.click('#connect');await missing.locator('#status').filter({hasText:'not installed'}).waitFor();pass('Missing MetaMask produces actionable error');await missing.close();
 const context=await browser.newContext({viewport:{width:1360,height:1140}});
 await context.exposeFunction('localRpc',async({method,params=[]})=>{
  if(method==='eth_requestAccounts')method='eth_accounts';
  return chain.provider.request({method,params});
 });
 await context.addInitScript(()=>{
  const handlers={};window.walletTest={reject:false,wrongNetwork:false,emit:(event,value)=>(handlers[event]||[]).forEach(f=>f(value))};
  window.ethereum={request:async(args)=>{if(window.walletTest.reject&&['eth_requestAccounts','eth_sendTransaction'].includes(args.method)){const e=new Error('User rejected request');e.code=4001;throw e;}if(args.method==='eth_chainId'&&window.walletTest.wrongNetwork)return '0x1';return window.localRpc(args);},on:(event,fn)=>{(handlers[event]??=[]).push(fn);}};
 });
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.locator('#network').filter({hasText:'Local test chain'}).waitFor();
 await page.evaluate(()=>window.walletTest.wrongNetwork=true);await page.click('#connect');await page.locator('#status').filter({hasText:'Wrong network'}).waitFor();pass('Wrong chain blocks wallet connection');
 await page.evaluate(()=>{window.walletTest.wrongNetwork=false;window.walletTest.reject=true;});await page.click('#connect');await page.locator('#status').filter({hasText:'rejected'}).waitFor();pass('Wallet rejection is handled');
 await page.evaluate(()=>window.walletTest.reject=false);await page.click('#connect');await page.locator('#status').filter({hasText:'Wallet connected.'}).waitFor();pass('EIP-1193 adapter connects to real local EVM');
 const date=new Date(Date.now()+10*60000);const localDate=new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);
 await page.fill('#label','Learning fund');await page.fill('#target','0');await page.fill('#unlock',localDate);await page.check('#agree');await page.click('#create-button');await page.locator('#status').filter({hasText:'greater than zero'}).waitFor();pass('Zero target rejected before signing');
 await page.fill('#target','0.05');await page.click('#create-button');await page.locator('#status.success').waitFor({timeout:30000});assert.equal(await c.nextId(),1n);pass('UI creates actual on-chain goal');
 await page.locator('.actions input').fill('-1');await page.locator('[data-action="deposit"]').click();await page.locator('#status.error').waitFor();pass('Negative deposit rejected');
 await page.locator('.actions input').fill('0.02');await page.locator('[data-action="deposit"]').click();await page.locator('#status.success').waitFor({timeout:30000});assert.equal((await c.goals(0)).balance,20000000000000000n);assert.equal(await page.locator('#history tr').count(),2);pass('UI deposit updates chain balance and event history');
 await page.screenshot({path:'evidence/01-local-funded-goal.png',fullPage:true});
 await page.reload();await page.click('#connect');await page.locator('#status').filter({hasText:'Wallet connected.'}).waitFor();assert.equal(await page.locator('#history tr').count(),2);pass('History survives page reload via blockchain reads');
 await chain.provider.request({method:'evm_increaseTime',params:[700]});await chain.provider.request({method:'evm_mine',params:[]});await page.click('#refresh');await page.locator('[data-action="withdraw"]').waitFor();await page.locator('[data-action="withdraw"]').click();await page.locator('#status.success').waitFor({timeout:30000});assert.equal((await c.goals(0)).closed,true);assert.equal(await page.locator('#history tr').count(),3);pass('UI withdraws below-target funds after local time advance');await page.screenshot({path:'evidence/02-local-withdrawn-goal.png',fullPage:true});
 await page.evaluate(()=>window.walletTest.emit('accountsChanged',[]));assert.equal(await page.locator('#create-button').isDisabled(),true);await page.locator('#status').filter({hasText:'Reconnect'}).waitFor();pass('Account change clears stale wallet state');
 await page.click('#connect');await page.locator('#status').filter({hasText:'Wallet connected.'}).waitFor();await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:'evidence/03-mobile-local-view.png',fullPage:true});pass('390px mobile layout has no horizontal page overflow');
 assert.deepEqual(errors,[]);pass('No uncaught browser JavaScript errors');
 const owner=await(await p.getSigner(0)).getAddress();const history=await(await fetch(url+'/api/history/'+owner)).json();
 fs.writeFileSync('evidence/ui-chain-history.json',JSON.stringify({scope:'Local Ganache EVM; EIP-1193 test adapter, not MetaMask or Sepolia',deployment:{hash:deployment.hash,block:deployment.blockNumber,address:await c.getAddress()},history},null,2));
 fs.writeFileSync('evidence/browser-results.json',JSON.stringify({scope:'Python Flask/Gunicorn backend with local EVM and injected test provider; actual MetaMask not tested',results},null,2));
}finally{await browser.close();await app.close();p.destroy();await chain.close();fs.unlinkSync(f);}
