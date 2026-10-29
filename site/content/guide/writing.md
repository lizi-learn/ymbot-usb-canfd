---
title: 如何新增和维护验证文章
navTitle: 文章编写与维护
category: 使用与维护
board: 通用
date: '2026-10-30'
order: 20
result: 维护说明
description: 一篇 Markdown 对应一篇文章，按分类自动生成左侧目录、归档与检索数据。
tags: [Wiki, Markdown, 维护, 文档]
---
# 如何新增和维护验证文章

每次独立验证写成一篇 Markdown，放在 Wiki 的 `site/content/` 对应目录。文章、原始证据、附件与代码一同留版本。

左侧目录按文章的 `category` 自动分组；正文、搜索、归档和后端目录都使用同一份内容来源。

## 新文章怎么写

复制 `site/templates/record.md`，按主题放到 `content/can/`、`content/rs485/`、`content/system/` 或新的目录。文件名用简短英文，例如 `new-board-canfd.md`。

文章开头填写元数据：

```yaml
---
title: 某板卡：某接口验证
navTitle: 某板卡 · 某接口
category: CAN 验证
board: 具体板卡与版本
date: '2026-10-30'
order: 50
result: 按原始结果填写
description: 用一句话写清测试对象、条件和结论。
tags: [CAN FD, 5M]
draft: false
---
```

`draft: true` 的文章不会进入生产正文、目录或 API。完成后改为 `false` 再发布。日期填写实际测试或整理日期，避免把网页更新时间当作新硬件测试日期。

## 正文保留什么

建议按下列顺序组织，保持结论简明，过程可复现：

1. **结论**：本次通过什么、失败什么、哪些没测。
2. **测试对象**：板卡、芯片、软件版本、固件来源和实装差异。
3. **条件与操作**：接线、终端、波特率、载荷、窗口与命令。
4. **实测结果**：成功发送、实际接收、错误增量、吞吐和持续时间。
5. **原始证据**：JSON、日志、截图、PDF 和源码固定提交。
6. **待验证项**：尚缺的测量、后续定位方向。

只有文件存在或配置读回，不应写成实际收发已经通过；旧失败记录保留，并说明新旧条件。

## 附件和公开范围

附件使用明确列出的公开文件。不要把私有工作目录、原固件备份、设备口令、令牌或客户设备标识直接加入站点。

目前自动带入本仓库公开的 USB CAN JSON 与 PDF，生成逻辑位于 `site/scripts/prepare.mjs`。新增附件时更新该清单，构建后核对文件哈希。

## 预览和发布

在 `site/` 目录运行：

```sh
npm ci
npm run dev
# 生成生产文件并校验
npm run build
```

生产输出为 `site/dist`，部署到现有 Cloudflare Pages 项目 `ymbot-hardware-test`。发布后核对正文、目录、搜索、PDF / JSON 和 `/build-info.json`。

## 框架和内容接口

前端使用 VitePress 1.6.4 / Vue 3 的文档主题，后端使用 Hono 4 的只读内容接口，部署在 Cloudflare Pages 的 Worker 运行时。

- `/api/articles`：分页文章目录，可按分类、板卡和关键词查询。
- `/api/articles/<slug>`：指定文章的公开元数据与 Markdown。
- `/api/categories`：分类统计。
- `/api/search?q=关键词`：公开文章全文检索。

正文源文件由 GitHub 管理。本版没有部署网页登录编辑器；维护入口为每篇底部的“在 GitHub 编辑本文”。
