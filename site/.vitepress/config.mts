import { defineConfig } from 'vitepress';
import { fileURLToPath } from 'node:url';
import { tokenize } from './theme/tokenize.js';
import { readArticles, categoryOrder } from '../scripts/catalog.mjs';

const articles = readArticles();
const categories = [...new Set([...categoryOrder, ...articles.map((a) => a.category)])];
const sidebar = [
  { text: '开始阅读', items: [ { text: 'Wiki 首页', link: '/' }, { text: '全部文章', link: '/archive' } ] },
  ...categories.map((text) => ({ text, collapsed: false, items: articles.filter((a) => a.category === text).sort((a,b)=>a.order-b.order).map((a)=>({text:a.navTitle,link:a.url})) })).filter((group)=>group.items.length)
];
export default defineConfig({
  lang: 'zh-CN',
  title: 'YMBOT 硬件 Wiki',
  description: '按主题整理硬件调试、接口验证与系统优化的实测记录。',
  srcDir: 'content',
  outDir: 'dist',
  srcExclude: readArticles({drafts:true}).filter((a)=>a.draft).map((a)=>a.file),
  cleanUrls: true,
  sitemap: { hostname:'https://ymbot-hardware-test.pages.dev' },
  head: [['link',{rel:'icon',type:'image/svg+xml',href:'/favicon.svg'}],['meta',{name:'theme-color',content:'#315fcd'}]],
  vite: { publicDir:fileURLToPath(new URL('../public',import.meta.url)) },
  themeConfig: {
    logo: {src:'/favicon.svg',alt:'YMBOT'},
    nav: [{text:'文章归档',link:'/archive'},{text:'5IO 原手册',link:'https://ymbot-5io-wiki.pages.dev/'}],
    sidebar,
    socialLinks: [{icon:'github',link:'https://github.com/lizi-learn/ymbot-usb-canfd',ariaLabel:'GitHub 源码'}],
    outline: {level:[2,3],label:'本文目录'},
    sidebarMenuLabel:'文章目录',
    returnToTopLabel:'返回顶部',
    darkModeSwitchLabel:'切换主题',
    lightModeSwitchTitle:'切换为浅色',
    darkModeSwitchTitle:'切换为深色',
    docFooter:{prev:'上一篇',next:'下一篇'},
    editLink:{pattern:'https://github.com/lizi-learn/ymbot-usb-canfd/edit/main/site/content/:path',text:'在 GitHub 编辑本文'},
    search:{provider:'local',options:{
      translations:{button:{buttonText:'搜索文章',buttonAriaLabel:'搜索文章'},modal:{displayDetails:'显示详细结果',resetButtonTitle:'清空',backButtonTitle:'关闭搜索',noResultsText:'没有找到相关记录',footer:{selectText:'选择',navigateText:'切换',closeText:'关闭'}}},
      miniSearch:{searchOptions:{prefix:true,fuzzy:false,combineWith:'AND'},
        *_splitIntoSections(file) {
          const article=articles.find((item)=>file.replaceAll('\\','/').endsWith('/content/'+item.file));
          if(article) yield {anchor:'',titles:[article.title],text:tokenize(article.content+' '+article.description).join(' ')};
        }
      }
    }},
    notFound:{title:'没有找到这篇文章',quote:'可以从左侧目录继续阅读，或搜索关键词。',linkLabel:'返回 Wiki 首页',linkText:'返回 Wiki 首页'}
  }
});
