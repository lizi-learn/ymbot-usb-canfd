import DefaultTheme from 'vitepress/theme';
import { h } from 'vue';
import ArticleMeta from './ArticleMeta.vue';
import ArticleIndex from './ArticleIndex.vue';
import './custom.css';
import { tokenize } from './tokenize.js';
export default {
  extends: DefaultTheme,
  Layout: () => h(DefaultTheme.Layout, null, { 'doc-before': () => h(ArticleMeta) }),
  enhanceApp({ app, siteData }) {
    app.component('ArticleIndex', ArticleIndex);
    if (!import.meta.env.SSR) {
      siteData.value.themeConfig.search.options.miniSearch.options={tokenize};
    }
  }
};
