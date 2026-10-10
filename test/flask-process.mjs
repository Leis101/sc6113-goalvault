import {spawn} from 'node:child_process';
import net from 'node:net';
export async function startFlask(rpcUrl,deploymentFile){
 const probe=net.createServer();await new Promise(r=>probe.listen(0,'127.0.0.1',r));const port=probe.address().port;await new Promise(r=>probe.close(r));
 const child=spawn(process.env.PYTHON||'python3',['-m','gunicorn','app:app','--bind',`127.0.0.1:${port}`,'--workers','1','--threads','4'],{env:{...process.env,RPC_URL:rpcUrl,DEPLOYMENT_FILE:deploymentFile,CONTRACT_ADDRESS:'',CHAIN_ID:'',DEPLOYMENT_BLOCK:''},stdio:['ignore','pipe','pipe']});
 let log='',failure;child.stdout.on('data',x=>log+=x);child.stderr.on('data',x=>log+=x);child.on('error',e=>failure=e);
 const url=`http://127.0.0.1:${port}`;
 for(let n=0;n<100;n++){if(failure||child.exitCode!==null)throw failure||Error(log);try{if((await fetch(url+'/healthz')).ok)return {url,close:()=>new Promise(resolve=>{child.once('exit',resolve);child.kill('SIGTERM');})};}catch{}await new Promise(r=>setTimeout(r,100));}
 child.kill('SIGTERM');throw Error('Flask startup timeout: '+log);
}
