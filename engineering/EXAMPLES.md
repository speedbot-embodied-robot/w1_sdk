# Python、C++ 与 ROS 2 可运行示例

日期：2026-11-20。目标是在文档站展示可实际执行的源码，并解释语言和 ROS 2 接口的特性。

后续更新：ROS 2 已改为 W1 实际状态与 PVT 查询接口，当前方案及验证见 [W1 ROS 2 集成记录](./W1_ROS2_INTEGRATION.md)。以下初版合成数据与数量统计是历史记录，不代表更新后的 ROS 2 接口范围。

## 范围与职责

- Python：标准库 JSON 解析、带类型提示的数据结构、运行时校验、异常边界及 CLI。
- C++17：公共类型、库 target、RAII、显式结果类型、独立调用程序及 CTest。
- ROS 2 Humble：sensor_msgs/msg/JointState、QoS、发布订阅、执行器、参数与退出处理。
- 模拟数据只供本地学习和测试，不声明 W1 真实消息、关节映射、物理限制或硬件验证结果。
- 中英文说明引用 examples/ 中同一份源码，源码不复制到文档目录。

## 协作

- python_example：Python 实现、测试和双语说明。
- cpp_example：C++ 实现、测试和双语说明。
- ros2_example：ROS 2 包、实际通信测试和双语说明。
- 主代理：导航、源码引用检查、CI、构建和最终集成。

## 验收

1. Python 成功数据、非法字段、错误数值和 CLI 失败路径。
2. C++ Debug/Release 下校验不依赖 assert；独立链接库运行。
3. ROS 2 在 localhost 和独立 domain 上验证收发、无数据超时和消息结构校验；测试不依赖真机。
4. 源码引用文件和区域存在、内容非空、两种语言映射相同。
5. 中英文页面由菜单可达，根路径与 /w1_sdk/ 子路径构建和链接检查通过。
6. 保留用户对 docs/zh/index.md 的未提交修改。本次不推送。

## 验证结果

2026-11-20，本机 Ubuntu 22.04、Python 3.10.12、GCC 11.4、CMake 3.22.1、ROS 2 Humble / rmw_fastrtps_cpp：

| 范围     | 结果                                                                                                                         |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Python   | 4 个 unittest 方法及其子用例通过；包含 JSON 模式、bool、NaN/Inf、溢出、编码与 CLI 错误通道                                   |
| C++      | Release 构建、3 个 CTest 通过（库含 12 项校验）；独立 consumer 工程通过                                                      |
| ROS 2    | colcon build 成功；显式 pytest 收集并通过 2 项契约测试；4 项安装后 CLI 测试通过，涵盖实际 DDS 收发、非法消息、超时、无效参数 |
| ROS CLI  | best_effort/volatile 的 ros2 topic echo --once 实际收到 JointState                                                           |
| 源码引用 | 24 处导入及双语映射通过；9 项校验器回归测试通过，包括丢失文件、区域为空、混用区域标记、无空格导入与语言间漂移                |
| 文档     | 根路径默认中文与 /w1_sdk/ 默认英文均构建并校验通过；每次 32 个 HTML 页面                                                     |
| 展示     | 六个双语示例页面的生成 HTML 均有实际源码、高亮 token 和复制按钮；Chrome 桌面检查 Python 页面与新侧栏                         |
| 格式     | Python Ruff 检查通过；新增/修改文档、配置单独运行 Prettier，排除用户正在编辑的首页                                           |
| 忽略规则 | CMake、colcon、Python 缓存、egg-info 与 log 不进入提交候选                                                                   |

新增 CI 包含 Python/C++ 测试和 ROS 2 Humble 容器测试，并成为 Pages 发布的前置条件。尚未推送，因此新增 GitHub jobs 尚未在云端运行；不能将本地通过写成云端通过。Windows、macOS、其他 ROS 版本与真机未验证。

ROS 2 容器使用 ros:humble-ros-base 标签，系统依赖由 apt 安装；发行版固定，镜像与系统补丁未固定到内容摘要。此示例不承诺字节级可复现的 ROS 运行环境。

首次 colcon test 默认 unittest 未收集到 pytest 测试；已改为 --python-testing pytest 后实测通过。独立 review 发现导入校验器漏检无空格导入、混用 region 标记，均已修复并加入回归测试。

## IDE 风格代码块

2026-11-20：源码导入使用原生 code-group 文件标签与行号，配色使用 Shiki 内置 light-plus / dark-plus。样式集中在 docs/.vitepress/theme/editor.css；源码与示例行为不变。

cpp_example 子代理只读复核了 VitePress 的复制按钮 DOM 依赖、标签切换与行号布局。保留原生控件顺序、active 状态和 pre 横向滚动，没有添加会干扰复制的标题节点。

构建通过，24 处共享导入与 32 页站内链接通过。Chrome 实际检查 ROS 2 的多文件标签切换，并截获 clipboard.writeText 参数确认内容等于当前代码文本，不含文件标签和行号。检查浅色、深色桌面和 390px 手机视口，复制按钮处于标题栏，页面无横向溢出，长行在代码区域内滚动。系统剪贴板权限没有作为测试前提。改动尚未推送。

## W1 反馈录制器更新

日期：2026-11-23。移除低价值的本地 JSON Python mock（examples/python/read_state.py 及输入、测试），改为通过 ROS 2 Humble 只读订阅 W1 /joint_states 并录制 JSONL。原有 state_reader 保留，用于按名称单次读取关节并查询 PVT 状态；C++ 校验示例仍使用合成数据。

录制器保存实际解析后的 topic、消息原数组、publisher 提供的 header.stamp 和 frame_id。回调验证后将记录放入有界队列，单独写线程按序输出；使用 monotonic 时钟控制时长和无数据超时，输出文件独占创建，已有文件不会覆盖。它只记录到达本节点的反馈，不验证时间戳新鲜度，不保证 DDS 无丢帧，也不发送控制命令。

验证：Humble colcon build 通过，7 项 ROS 消息契约测试和 18 项隔离 CLI 测试通过；覆盖 remap 元数据、多帧与空数组、超时、迟到帧、paused sim clock、拒绝覆盖及 SIGINT 收尾。C++ 3 项 CTest、独立 consumer、9 项源码引用校验也通过。根路径和 /w1_sdk/ 文档构建、36 页链接验证均通过。隔离端点不代表 W1 真机验证；队列溢出和写盘故障没有专门注入测试。
