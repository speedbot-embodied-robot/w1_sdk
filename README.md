# W1 文档中心

当前站点包含 W1 产品、快速开始、SDK、API、版本与支持页面的中英文模板。标记为「待填写」的项目是内容输入项；尚未由产品、研发或测试确认的信息不能当作 W1 事实发布。

## 本地运行

需要 Node.js 22 和 npm 10。首次安装依赖后启动预览：

```sh
npm ci
npm run docs:dev
```

浏览器打开终端显示的本机地址，按 Ctrl+C 停止。

如果在 NFS 或容器挂载目录启动时遇到 `ENOSPC: System limit for number of file watchers reached`，使用轮询模式：

```sh
CHOKIDAR_USEPOLLING=true npm run docs:dev
```

## 构建与检查

```sh
npm run docs:build
npm run docs:verify
npm run docs:preview
```

静态文件输出在 `docs/.vitepress/dist/`。根路径发布使用默认设置；发布到 `/repository-name/` 时，构建前设置 `DOCS_BASE=/repository-name/`。部署步骤见[发布指南](./DEPLOYMENT.md)。

## 内容模板

页面按中英文成对维护，路由位于 `docs/zh/` 和 `docs/en/`。内容负责人从[产品概览](./docs/zh/product/overview.md)、[首次接入](./docs/zh/guide/quick-start.md)、[SDK 集成](./docs/zh/sdk/integration.md)及[API 参考](./docs/zh/api/reference.md)开始填写。完整输入清单见[资料收集模板](./templates/PRODUCT_CONTENT_INTAKE.md)。

## 站点结构

- `docs/.vitepress/config.mts`：语言路由、导航、搜索和托管路径。
- `docs/.vitepress/theme/`：主题样式。
- `docs/{zh,en}/`：成对的用户文档模板。
- `scripts/verify_site.py`：构建后检查路由、链接和双语页面结构。
- `.github/workflows/docs.yml`：推送到 `main` 后构建并发布 GitHub Pages。

当前目录是独立的文档站，不会自动同步 SDK 仓库中的代码。若文章引用 SDK 源码或可运行示例，需要在内容流程中明确对应 SDK 仓库和版本。
