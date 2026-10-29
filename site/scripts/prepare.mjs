import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readArticles, publicMetadata, siteRoot } from './catalog.mjs';
const root=path.dirname(siteRoot.replace(/\/$/,''));
const read=(file)=>JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
const continuous=read('evidence/continuous-fd5m-20261030.json');
const channels=read('evidence/channels-20261030.json');
const smoke=read('evidence/published-cli-smoke-20261030.json');
const five=JSON.parse(fs.readFileSync(path.join(siteRoot,'data/5io-snapshot.json'),'utf8'));
let frames=0;
if(continuous.status!=='pass'||continuous.data_bps!==5000000)throw Error('Unexpected USB test evidence');
for(const stage of continuous.stages){
  if(!stage.pass_integrity||stage.malformed||stage.unexpected)throw Error('USB integrity failure');
  for(const flow of Object.values(stage.flows)){
    if(flow.sent!==flow.received||['missing','duplicates','payload_errors','out_of_order'].some(k=>flow[k]!==0))throw Error('USB flow integrity failure');
    frames+=flow.received;
  }
}
if(frames!==143076||channels.channels[2].physical_peer_test!=='not_connected_not_run')throw Error('Board scope mismatch');
if(smoke.status!=='pass'||Object.values(smoke.flows).reduce((n,f)=>n+f.received,0)!==4565)throw Error('CLI smoke mismatch');
if(five.stages.reduce((n,s)=>n+s.frames,0)!==12386944||five.stages.reduce((n,s)=>n+s.seconds,0)!==1830||five.strict_acceptance!=='failed')throw Error('5IO historical scope mismatch');
const articles=readArticles();
if(new Set(articles.map(a=>a.slug)).size!==articles.length)throw Error('Duplicate article slug');
for(const a of articles){if(!/^\d{4}-\d{2}-\d{2}$/.test(a.date))throw Error('Missing article date: '+a.slug);}
const categories=[...new Set(articles.map(a=>a.category))];
const generated=path.join(siteRoot,'generated');fs.mkdirSync(generated,{recursive:true});
const catalog={articles:articles.map(publicMetadata),categories};
fs.writeFileSync(path.join(generated,'catalog.json'),JSON.stringify(catalog,null,2)+'\n');
fs.writeFileSync(path.join(generated,'backend-articles.mjs'),'export default '+JSON.stringify(articles.map(a=>({...publicMetadata(a),content:a.content})))+';\n');
const sourceCommit=execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
fs.writeFileSync(path.join(generated,'site-info.mjs'),'export default '+JSON.stringify({sourceCommit,framework:'VitePress 1.6.4 + Vue 3 / Hono 4',articleCount:articles.length})+';\n');
const publicDir=path.join(siteRoot,'public');
for(const dir of ['data','downloads'])fs.mkdirSync(path.join(publicDir,dir),{recursive:true});
for(const name of ['continuous-fd5m-20261030.json','published-cli-smoke-20261030.json','channels-20261030.json','battery-power-switch-20261030.json'])fs.copyFileSync(path.join(root,'evidence',name),path.join(publicDir,'data',name));
fs.copyFileSync(path.join(siteRoot,'data/5io-snapshot.json'),path.join(publicDir,'data/5io-snapshot.json'));
fs.copyFileSync(path.join(root,'docs/CAN0-CAN1-FD5M-20261030.pdf'),path.join(publicDir,'downloads/CAN0-CAN1-FD5M-20261030.pdf'));
console.log(`Prepared ${articles.length} published articles; USB / 5IO evidence boundaries verified`);
