import { Hono } from 'hono';
import articles from '../generated/backend-articles.mjs';
import siteInfo from '../generated/site-info.mjs';
const metadata=({content,...item})=>item;
const normalize=(value)=>String(value).normalize('NFKC').toLocaleLowerCase('zh-CN');
const searchable=articles.map(a=>({article:a,text:normalize([a.title,a.description,a.board,a.tags.join(' '),a.content].join('\n'))}));
export const app=new Hono();
app.use('/api/*',async(c,next)=>{
  c.header('X-Content-Type-Options','nosniff');
  c.header('Content-Security-Policy',"default-src 'none'; frame-ancestors 'none'");
  c.header('Cache-Control','public, max-age=60');
  if(!['GET','HEAD'].includes(c.req.method))return c.json({error:'Method not allowed'},405,{'Allow':'GET, HEAD'});
  return next();
});
app.get('/api/health',(c)=>c.json({status:'ok',mode:'read-only wiki',...siteInfo},200,{'Cache-Control':'no-store'}));
app.get('/api/categories',(c)=>c.json({categories:[...new Set(articles.map(a=>a.category))].map(name=>({name,count:articles.filter(a=>a.category===name).length}))}));
function list(c,searchRequired=false){
  const q=(c.req.query('q')||'').trim();
  const limitText=c.req.query('limit')||'20',offsetText=c.req.query('offset')||'0';
  if(q.length>160||!/^[0-9]+$/.test(limitText)||!/^[0-9]+$/.test(offsetText))return c.json({error:'Invalid query'},400);
  const limit=Number(limitText),offset=Number(offsetText);
  if(limit<1||limit>100||offset>100000||!Number.isSafeInteger(offset))return c.json({error:'Invalid pagination'},400);
  if(searchRequired&&!q)return c.json({error:'Search query required'},400);
  const category=c.req.query('category'),board=c.req.query('board');
  const terms=normalize(q).split(/\s+/u).filter(Boolean);
  const selected=searchable.filter(({article:a,text})=>(!category||a.category===category)&&(!board||a.board===board)&&terms.every(term=>text.includes(term)));
  return c.json({articles:selected.slice(offset,offset+limit).map(({article})=>metadata(article)),total:selected.length,limit,offset});
}
app.get('/api/articles',(c)=>list(c));
app.get('/api/search',(c)=>list(c,true));
app.get('/api/articles/*',(c)=>{
  let slug;try{slug=decodeURIComponent(c.req.path.slice('/api/articles/'.length));}catch{return c.json({error:'Invalid article slug'},400);}
  const article=articles.find(a=>a.slug===slug);
  return article?c.json(article):c.json({error:'Article not found'},404);
});
app.notFound(c=>c.json({error:'Not found'},404));
export default {
  async fetch(request,env,ctx){
    if(new URL(request.url).pathname.startsWith('/api/'))return app.fetch(request,env,ctx);
    return env.ASSETS.fetch(request);
  }
};
