<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import catalog from '../../generated/catalog.json';
const props = defineProps({ limit: { type: Number, default: 10 }, archive: Boolean });
const articles = ref(catalog.articles);
const query = ref('');
const category = ref('');
const page = ref(0);
const categories = catalog.categories;
const filtered = computed(() => articles.value.filter((a) => (props.archive || a.category !== '使用与维护') && (!category.value || a.category === category.value) && (!query.value || `${a.title} ${a.description} ${a.board} ${a.tags.join(' ')}`.toLowerCase().includes(query.value.toLowerCase()))));
const visible = computed(() => filtered.value.slice(page.value * props.limit, (page.value + 1) * props.limit));
watch([query,category], () => { page.value=0; });
onMounted(async () => {
  try {
    const response = await fetch('/api/articles?limit=100');
    if (response.ok) { const result = await response.json(); if (result.total <= 100 && Array.isArray(result.articles)) articles.value = result.articles; }
  } catch { /* Build-time records remain readable when the API is unavailable. */ }
});
</script>
<template>
  <div class="article-index">
    <div v-if="archive" class="archive-tools">
      <input v-model="query" type="search" placeholder="筛选标题、板卡或关键词" aria-label="筛选文章">
      <select v-model="category" aria-label="文章分类"><option value="">全部分类</option><option v-for="name in categories" :key="name" :value="name">{{ name }}</option></select>
    </div>
    <ul class="article-list">
      <li v-for="article in visible" :key="article.slug">
        <a class="article-title" :href="article.url">{{ article.title }}</a>
        <p class="article-excerpt">{{ article.description }}</p>
        <div class="article-byline"><time :datetime="article.date">{{ article.date }}</time><span>{{ article.category }}</span><span>{{ article.board }}</span></div>
      </li>
    </ul>
    <p v-if="!visible.length" class="empty-list">没有找到匹配的文章。</p>
    <div v-if="archive && filtered.length > limit" class="article-pagination"><button :disabled="page===0" @click="page--">上一页</button><span>{{ page+1 }} / {{ Math.ceil(filtered.length / limit) }}</span><button :disabled="(page+1)*limit>=filtered.length" @click="page++">下一页</button></div>
    <p v-if="!archive" class="archive-link"><a href="/archive">查看全部 {{ articles.length }} 篇文章 →</a></p>
  </div>
</template>
