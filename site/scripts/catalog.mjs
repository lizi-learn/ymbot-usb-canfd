import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';

export const siteRoot = fileURLToPath(new URL('../', import.meta.url));
export const contentRoot = path.join(siteRoot, 'content');
export const categoryOrder = ['CAN 验证', 'RS485 验证', '电源与电池', '系统与桌面', '使用与维护'];
function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? walk(path.join(dir, entry.name)) : entry.name.endsWith('.md') ? [path.join(dir, entry.name)] : []);
}
export function readArticles({ drafts = false } = {}) {
  return walk(contentRoot).flatMap((file) => {
    const { data, content } = matter(fs.readFileSync(file, 'utf8'));
    if (!data.title || !data.category || (data.draft && !drafts)) return [];
    const relative = path.relative(contentRoot, file).split(path.sep).join('/');
    const url = '/' + relative.replace(/\.md$/, '').replace(/\/index$/, '/');
    return [{
      slug: url.slice(1), url, file: relative,
      title: String(data.title), navTitle: String(data.navTitle || data.title),
      category: String(data.category), board: String(data.board || '通用'),
      date: String(data.date || ''), order: Number(data.order || 100),
      result: String(data.result || ''), description: String(data.description || ''),
      tags: Array.isArray(data.tags) ? data.tags.map(String) : [],
      draft: Boolean(data.draft), content
    }];
  }).sort((a,b) => b.date.localeCompare(a.date) || a.order-b.order || a.title.localeCompare(b.title,'zh-CN'));
}
export function publicMetadata(article) {
  const { content, draft, file, order, navTitle, ...metadata } = article;
  return metadata;
}
