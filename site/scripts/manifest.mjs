import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { build } from 'esbuild';
import { siteRoot } from './catalog.mjs';
import siteInfo from '../generated/site-info.mjs';
const out=path.join(siteRoot,'dist');
const walk=(dir)=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);
const inlineHashes=new Set();
for(const file of walk(out).filter(f=>f.endsWith('.html'))){
 const text=fs.readFileSync(file,'utf8');
 for(const match of text.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)){
  if(!/\bsrc\s*=/.test(match[1])&&match[2])inlineHashes.add("'sha256-"+createHash('sha256').update(match[2]).digest('base64')+"'");
 }
}
const csp="default-src 'self'; script-src 'self' "+[...inlineHashes].join(' ')+"; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'";
fs.writeFileSync(path.join(out,'_headers'),`/*\n  Content-Security-Policy: ${csp}\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  Cache-Control: public, max-age=0, must-revalidate\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n`);
fs.writeFileSync(path.join(out,'_redirects'),'/usb-canfd /can/usb-canfd-5m 301\n/usb-canfd/ /can/usb-canfd-5m 301\n/5io /can/5io-canfd-5m 301\n/5io/ /can/5io-canfd-5m 301\n/method /guide/test-method 301\n/method/ /guide/test-method 301\n');
await build({entryPoints:[path.join(siteRoot,'backend/index.mjs')],outfile:path.join(out,'_worker.js'),bundle:true,format:'esm',platform:'browser',target:'es2022',minify:true});
fs.writeFileSync(path.join(out,'_routes.json'),JSON.stringify({version:1,include:['/api/*'],exclude:[]})+'\n');
const manifest={};
for(const file of walk(out)){
 const name=path.relative(out,file).split(path.sep).join('/');
 if(['build-info.json','_worker.js','_headers','_redirects','_routes.json'].includes(name))continue;
 manifest[name]=createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}
fs.writeFileSync(path.join(out,'build-info.json'),JSON.stringify({source_commit:siteInfo.sourceCommit,updated:'2026-10-30',framework:siteInfo.framework,article_count:siteInfo.articleCount,site:'https://ymbot-hardware-test.pages.dev',artifacts_sha256:manifest},null,2)+'\n');
console.log(`Built Hono backend, ${inlineHashes.size} inline script hashes and ${Object.keys(manifest).length} public assets`);
