import test from 'node:test';
import assert from 'node:assert/strict';
import { app } from './index.mjs';
test('published catalog supports pagination and Unicode category filters',async()=>{
 const page=await (await app.request('/api/articles?limit=2&offset=1')).json();assert.equal(page.articles.length,2);assert.ok(page.total>=9);
 const filtered=await (await app.request('/api/articles?category='+encodeURIComponent('CAN 验证'))).json();assert.ok(filtered.total>=4);assert.ok(filtered.articles.every(a=>a.category==='CAN 验证'));
 const draft=await app.request('/api/articles/templates/record');assert.equal(draft.status,404);
});
test('full-text Chinese search and article lookup preserve board scope',async()=>{
 const result=await (await app.request('/api/search?q='+encodeURIComponent('抢读'))).json();assert.ok(result.articles.some(a=>a.slug==='can/usb-canfd-5m'));
 const article=await (await app.request('/api/articles/can/usb-canfd-5m')).json();assert.equal(article.board,'自研 USB CAN 板');assert.ok(article.content.includes('143,076'));assert.ok(!article.content.includes('12,386,944'));
});
test('malformed queries and write requests cannot alter content',async()=>{
 for(const query of ['limit=0','limit=101','offset=-1','limit=NaN'])assert.equal((await app.request('/api/articles?'+query)).status,400);
 assert.equal((await app.request('/api/search')).status,400);
 const write=await app.request('/api/articles',{method:'POST',body:'{}'});assert.equal(write.status,405);
 assert.equal((await app.request('/api/articles/missing')).status,404);
});
