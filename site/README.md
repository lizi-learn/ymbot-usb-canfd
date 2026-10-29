# YMBOT 硬件验证站点

生产地址：<https://ymbot-hardware-test.pages.dev/>。静态 Cloudflare Pages 站点，项目名 `ymbot-hardware-test`，生产分支 `main`，上传目录 `site/dist`。

- 自研 USB CAN 板：本仓库 `evidence/` 的 2026-10-30 实测。CAN0/CAN1 FD 5M 有限台架通过；CAN2 未接线。
- 5IO 板：`site/data/5io-snapshot.json` 引用另一个仓库的固定提交与原始证据。FD 5M 30 分钟严格验收失败，完整保留；12,386,944 帧总数包含 60,000 帧 / 30 秒基线。
- 原 5IO 教学 Wiki 保留：<https://ymbot-5io-wiki.pages.dev/>。两块板的软件栈、证据与结论分开维护。

## 构建和检查

只用 Python 标准库生成 HTML。脚本验证 USB 帧数、完整性、CAN2 状态及 5IO 分阶段合计；结果文件不匹配时构建失败。

```sh
python3 site/build.py
python3 site/check.py
node --check site/assets/app.js
python3 -m http.server 8000 --directory site/dist
```

网站不加载设备控制接口、不发 CAN 帧。硬件 CLI 与网站构建独立运行。下载只复制明确列出的公开 JSON 和已公开 PDF，不递归复制私有工作目录。

## 更新记录

新增测试时保留原始证据、日期、板卡身份、软件版本、接线 / 负载 / 时长及未测范围。失败阶段不能被短测通过覆盖。修改页面引用及生成逻辑后重新构建、检查和浏览器核验。

5IO 记录来自另一个项目；更新其快照时核对固定提交、原始 JSON SHA-256 与统计口径。不要把本板的通过状态传播到另一块板。

## 发布

使用现有 Cloudflare 账户的 Pages Write 令牌，在本机环境配置 `CLOUDFLARE_API_TOKEN` 和 `CLOUDFLARE_ACCOUNT_ID`，不要写进仓库或构建产物。Pages 项目使用 Direct Upload；首次由维护者在目标账户创建同名项目。

```sh
python3 site/build.py
python3 site/check.py
npx --yes wrangler@4.152.0 pages deploy site/dist \
  --project-name ymbot-hardware-test --branch main
```

发布后核对 `/build-info.json` 的源码提交，以及首页、两个板卡详情、测试口径、原始 JSON 与 PDF 的状态和内容哈希。站点暂不依赖 GitHub 自动部署，GitHub 提交本身不会改变设备状态。
