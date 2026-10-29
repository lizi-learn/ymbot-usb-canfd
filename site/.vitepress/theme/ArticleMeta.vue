<script setup>
import { computed } from 'vue';
import { useData } from 'vitepress';
const { frontmatter } = useData();
const meta = computed(() => frontmatter.value);
</script>
<template>
  <div v-if="meta.category" class="article-meta">
    <span>{{ meta.category }}</span><span v-if="meta.board">{{ meta.board }}</span><time v-if="meta.date" :datetime="String(meta.date)">{{ meta.date }}</time>
  </div>
</template>
