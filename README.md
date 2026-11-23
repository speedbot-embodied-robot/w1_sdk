# W1 文档中心

当前站点包含 W1 的双语产品资料、可运行的 Python/C++/ROS 2 示例，以及待补充的安装、版本和支持模板。产品资料列出参考参数与待确认条件；ROS 2 使用提供的 W1 接口文档。标记为「待填写」或「待确认」的项目仍需对应负责人补充。

## 本地运行

需要 Node.js 22 和 npm 10。首次安装依赖后启动预览：

```sh
npm ci
npm run docs:dev
```

本机浏览器打开终端显示的 Local 地址；同一局域网内的其他设备打开终端显示的 Network 地址（例如 `http://192.168.1.20:5173`）。服务器绑定所有网卡；如果 Network 地址不可达，请确认设备处于同一网络、使用的端口与终端输出一致，并允许该 TCP 端口通过本机防火墙。按 Ctrl+C 停止服务。

如果在 NFS 或容器挂载目录启动时遇到 `ENOSPC: System limit for number of file watchers reached`，使用轮询模式：

```sh
CHOKIDAR_USEPOLLING=true npm run docs:dev
```

轮询模式同样监听局域网网卡；打开终端显示的 Network 地址。

## 构建与检查

```sh
npm run docs:build
npm run docs:verify
npm run docs:preview
```

静态文件输出在 `docs/.vitepress/dist/`。根路径发布使用默认设置；发布到 `/repository-name/` 时，构建前设置 `DOCS_BASE=/repository-name/`。部署步骤见[发布指南](./DEPLOYMENT.md)。

## 内容模板

页面按中英文成对维护，路由位于 `docs/zh/` 和 `docs/en/`。内容负责人从[产品概览](./docs/zh/product/overview.md)、[SDK 集成](./docs/zh/sdk/integration.md)开始填写。完整输入清单见[资料收集模板](./templates/PRODUCT_CONTENT_INTAKE.md)。

欢迎多人通过 GitHub 分支和 Pull Request 共同维护。新增页面、可运行示例、双语同步、评审和合并步骤见[贡献指南](./CONTRIBUTING.md)；新示例可从[示例页面模板](./templates/EXAMPLE_PAGE_TEMPLATE.md)开始。

[产品概览](./docs/zh/product/overview.md)、[型号与规格](./docs/zh/product/specifications.md)、[部件与接口](./docs/zh/product/interfaces.md)已补入公开资料，新增[能力与应用](./docs/zh/product/capabilities.md)介绍移动、感知、焊接、分层控制概念及带日期的应用阶段。集成与缺项记录见 [产品资料集成](./engineering/W1_PRODUCT_CONTENT_INTEGRATION.md)。

## 可运行代码示例

[Python](./docs/zh/sdk/python-example.md) 示例通过 ROS 2 订阅 W1 的 `/joint_states`，将真实关节反馈录制为 JSONL，供故障排查和离线分析。[W1 ROS 2](./docs/zh/sdk/ros2-example.md) 还介绍按关节名读取状态、查询 PVT 状态服务，以及规划、示教和焊接接口；关节顺序与命令格式见 [W1 整机控制](./docs/zh/api/w1-control.md)。[C++](./docs/zh/sdk/cpp-example.md) 独立展示数据校验与库接入。中英文代码块从 `examples/` 导入同一份源码，保留 IDE 风格文件标签、行号和复制功能。

W1 接入需要另行安装的 W1 ROS 2 工作区与相应节点。本仓库不包含 `ethercat_motor_drive`、`speedbot_msgs`、控制 YAML、运动轨迹或标定文件；自动化测试使用隔离的端点替身，无需 W1 真机。

```sh
python3 scripts/test_examples.py
```

测试命令需要 Python 3.10+、CMake 3.20+ 和 C++17 编译器，检查源码引用校验器、C++、独立 CMake 接入。录制器和状态查询需要 ROS 2 Humble、已构建的本仓库示例包，以及发布 W1 `/joint_states` 的机器人工作区；具体命令和隔离端点测试见 ROS 2 教程。

新增示例页时，中英文引用相同文件和代码区域。`docs:build` 会先检查源码导入，再构建网站。README 等普通 Markdown 阅读环境不展开 VitePress 的代码导入语法；完整展示请通过文档站查看，源文件在 `examples/` 中可直接阅读。

推送到 main 后，发布工作流会先完成 C++、源码引用与 ROS 2 测试；全部通过才发布。Pull Request 也会执行示例测试。ROS 2 CI 使用 Humble 容器，验证 localhost 隔离端点下的状态订阅、服务调用、JSONL 录制及错误退出；这些测试不连接 W1 控制器或真机。

## 站点结构

- `docs/.vitepress/config.mts`：语言路由、导航、搜索和托管路径。
- `docs/.vitepress/theme/`：主题样式。`layout.css` 控制正文及两侧目录宽度，`editor.css` 控制源码块，`style.css` 控制配色和首页；`index.ts` 负责加载这些样式。
- `docs/{zh,en}/`：成对的用户文档模板。
- `scripts/verify_site.py`：构建后检查路由、链接和双语页面结构。
- `scripts/verify_snippets.py`：检查共享源码文件、区域和双语引用一致性。
- `examples/`：Python、C++ 与 ROS 2 实现、输入及测试。
- `.github/workflows/docs.yml`：推送到 `main` 后构建并发布 GitHub Pages。

当前目录是独立的文档站，不会自动同步 SDK 仓库中的代码。若文章引用 SDK 源码或可运行示例，需要在内容流程中明确对应 SDK 仓库和版本。
