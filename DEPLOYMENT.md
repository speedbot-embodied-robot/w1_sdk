# 文档站构建与部署

本站生成静态文件，不需要在服务器运行 Node.js 或 VitePress。构建输入是 `docs/`，产物目录为 `docs/.vitepress/dist/`。每次部署前先构建并验证同一份产物。

## 本地构建

使用 `.nvmrc` 中指定的 Node.js 版本。在仓库根目录运行：

```bash
npm ci
DOCS_PLATFORM=local DOCS_BASE=/ DOCS_DEFAULT_LANG=zh npm run docs:build
DOCS_PLATFORM=local DOCS_BASE=/ DOCS_DEFAULT_LANG=zh python3 scripts/verify_site.py
```

本地默认发布到域名根路径 `/`，根入口默认进入中文。`DOCS_BASE` 必须以 `/` 开始和结束；部署到域名根目录时用 `/`，部署在子路径时例如用 `/w1-docs/`。构建和验证时传入相同的 `DOCS_PLATFORM`、`DOCS_BASE`、`DOCS_DEFAULT_LANG`。产物会根据这些值生成资源和语言链接。

运行 `npm run docs:preview -- --host 0.0.0.0` 可以预览构建产物。预览完毕后按 Ctrl+C 停止。

## GitHub Pages

`.github/workflows/docs.yml` 在 `main` 分支收到 push 时自动执行 `npm ci`、构建、站点校验，并将 `docs/.vitepress/dist/` 发布到 GitHub Pages。也可以在仓库的 **Actions → Build and deploy documentation → Run workflow** 手动触发；该工作流只对 `main` 发布。

目标仓库是 [speedbot-embodied-robot/w1_sdk](https://github.com/speedbot-embodied-robot/w1_sdk)。首次发布前，在仓库的 [Settings → Pages](https://github.com/speedbot-embodied-robot/w1_sdk/settings/pages) 将 **Build and deployment → Source** 设为 **GitHub Actions**。截至 2026-11-20 本次检查，Pages 尚未启用；未配置时工作流会在读取 Pages 配置这一步失败，完成设置后可在 Actions 中重新运行。

工作流从 GitHub Pages 配置读取 base path。此项目站点默认使用 `/w1_sdk/`；未配置自定义域名时，发布成功后的预期地址为 `https://speedbot-embodied-robot.github.io/w1_sdk/`。用户站点或配置了自定义域名的站点通常使用 `/`。站点标题在 `docs/.vitepress/config.mts` 中维护，自定义域名在仓库 Pages 设置中配置。以成功工作流的 deployment 地址为准。

GitHub Pages 构建默认语言为英文。可以在 **Settings → Secrets and variables → Actions → Variables** 添加 `DOCS_DEFAULT_LANG`，值设为 `en` 或 `zh`。改动变量后需重新运行工作流。两个语言目录始终都可访问，默认语言只影响站点根入口。

## 国内服务器与 Nginx

此方式把静态文件放到已有 Linux Web 服务器上，由 Nginx 提供服务。它不要求服务器安装 Node.js，也不会自动连接或修改生产服务器。

1. 在本机生成部署到域名根目录的文件：

   ```bash
   npm ci
   DOCS_PLATFORM=domestic DOCS_BASE=/ DOCS_DEFAULT_LANG=zh npm run docs:build
   DOCS_PLATFORM=domestic DOCS_BASE=/ DOCS_DEFAULT_LANG=zh python3 scripts/verify_site.py
   ```

2. 将 `deploy/nginx.conf.example` 复制到服务器的 Nginx 配置目录，并把示例域名 `docs.example.com`、证书路径和站点路径替换为实际值。配置假设 TLS 证书已由服务器管理员准备好；HTTP 仅用于 ACME 校验并将普通请求重定向到 HTTPS。

3. 在服务器上为站点创建专用目录，然后把 `docs/.vitepress/dist/` **目录中的内容**同步到 Nginx 配置的 `root` 目录。不要把 `dist` 目录本身嵌套为 `current/dist`：Nginx 的 `index.html` 应直接位于 `/srv/www/w1-docs/current/index.html`。

   ```bash
   ssh deploy@docs.example.com 'sudo install -d -o www-data -g www-data /srv/www/w1-docs/current'
   rsync -av docs/.vitepress/dist/ deploy@docs.example.com:/tmp/w1-docs-dist/
   ssh deploy@docs.example.com 'sudo rsync -av /tmp/w1-docs-dist/ /srv/www/w1-docs/current/ && rm -rf /tmp/w1-docs-dist'
   ```

   请将 `deploy`、域名和路径换成自己的值，并确认 Nginx worker 用户可读取部署目录。上述同步目标是专用文档目录；请勿把它改成服务器上其他站点或系统目录。

4. 在服务器执行 `sudo nginx -t`，通过后再执行 `sudo systemctl reload nginx`。检查 `https://docs.example.com/`、`/zh/` 和 `/en/`，并确认页面刷新、语言切换、搜索和静态资源正常。

`deploy/nginx.conf.example` 将站点构建于域名根目录。如果将站点放在同一域名的子目录，例如 `https://example.com/w1-docs/`，构建时设置 `DOCS_BASE=/w1-docs/`，并将 dist 的内容放在 Nginx 文档根目录的 `w1-docs/` 下；否则资源和页面链接会指向错误路径。

若希望推送分支后自动发布到国内服务器，需要另行配置受控的 CI 任务、部署凭据和主机密钥校验。当前仓库只自动部署到 GitHub Pages；国内服务器步骤是人工构建与同步，不会因 GitHub 分支 push 自动执行。
