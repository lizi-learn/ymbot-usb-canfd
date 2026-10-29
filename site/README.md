# YMBOT 硬件 Wiki

地址：<https://ymbot-hardware-test.pages.dev/>。使用 VitePress 1.6.4 / Vue 3 前端与 Hono 4 内容接口，部署到 Cloudflare Pages 项目 `ymbot-hardware-test`。左侧按主题列文章，点开进入正文；全文搜索、文章目录、代码复制和移动端菜单使用文档框架提供的功能。

## 本地开发

需要 Node.js 20+、npm 和 Python 3；本次使用 Node.js 22。

```sh
cd site
npm ci
npm run dev
npm test
npm run build
```

`npm run build` 生成 `site/dist`，包含预渲染正文和 Hono Worker。完整本地运行（包括 API）使用：

```sh
npx --yes wrangler@4.152.0 pages dev dist --port 8788
```

`npm run preview` 可查看正文静态文件；完整接口验证使用 Wrangler。HTML、公开 JSON、PDF 和 Worker 构建时接受链接、内容范围、哈希和脚本策略检查。

## 文章与导航

一篇 `content/**/*.md` 对应一篇文章。复制 `templates/record.md` 后填写元数据和正文；左侧目录、归档、搜索和后端接口自动从已发布文章生成。

- `category`：左侧分类；新分类也会自动出现。
- `navTitle`：侧边栏短标题。
- `date`：实际测试 / 整理日期；用引号包裹的 YYYY-MM-DD。
- `board`：本篇对应板卡。
- `draft: true`：不进入生产正文、目录或接口。

维护说明也可在站点的“使用与维护 → 文章编写与维护”阅读。正文使用 GitHub Markdown 管理，当前版本没有网页登录编辑器。

## 内容接口

`backend/index.mjs` 使用 Hono，提供只读 HTTP 接口；文章数据由构建阶段从同一批公开 Markdown 生成。

- `GET /api/health`
- `GET /api/articles?category=分类&board=板卡&q=关键词&limit=20&offset=0`
- `GET /api/articles/<slug>`
- `GET /api/categories`
- `GET /api/search?q=关键词`

只路由 `/api/*` 到 Worker，正文和附件继续由 Pages 静态资源服务。接口不调用设备控制、不接受内容写入；归档页面从接口读取目录，接口不可用时仍可读预渲染记录。

## 验证结论的归属

自研 USB CAN 板与 5IO 板分别归档。USB CAN0/CAN1 FD 5M 有限台架通过，CAN2 未接线；5IO 的 30 分钟严格验收失败保留。12,386,944 帧总数包含 60,000 帧 / 30 秒基线。

电源与电池分类另收录 1003、1008 两次独立的电池输出关闭 / 恢复试验，公开附件只包含提取的测量与内部源文件指纹。

原 [5IO 系统优化 Wiki](https://ymbot-5io-wiki.pages.dev/) 保留。本次前后端重构没有运行新的硬件测试。

## 发布和回退

使用现有 Cloudflare 账户的 Pages Write 令牌，在本机环境配置 `CLOUDFLARE_API_TOKEN` 和 `CLOUDFLARE_ACCOUNT_ID`。不要把令牌写入源码、输出或日志。

```sh
npm ci
npm run build
npx --yes wrangler@4.152.0 pages deploy dist \
  --project-name ymbot-hardware-test --branch main
```

`wrangler.jsonc` 固定 Pages 输出和 Worker 兼容日期。旧的 `/usb-canfd/`、`/5io/`、`/method/` 地址重定向到新文章。发布后检查 `/build-info.json` 的源码提交、正文、搜索、API、JSON 与 PDF。需要回退时从 Cloudflare Pages 历史生产部署选择上一版，或重新构建对应 Git 提交。
