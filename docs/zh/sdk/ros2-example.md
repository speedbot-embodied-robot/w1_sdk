# ROS 2：W1 通讯接口与示例

本页面向 `speed_W1_v1.2`（28 轴、七轴双臂），环境为 ROS 2 Humble。示例使用 W1 实际的 `/joint_states` 和 PVT 状态服务：先在 W1 mock 中读取反馈，再调用 `execute: false` 的右臂规划服务。所有名称均采用默认命名空间，完整关节顺序与控制约束见 [W1 整机控制接口](../api/w1-control.md)。

## 环境与依赖

开发环境使用 Ubuntu 22.04、Python 3.10 和 ROS 2 Humble。只读示例包 `w1_docs_ros2` 随本仓库提供，依赖 `rclpy`、`sensor_msgs`、`std_srvs`，通过 `ament_python` / `colcon` 构建。使用与 Humble 安装一致的系统 Python；需要另外安装 colcon 和 pytest 来构建、测试。

W1 驱动与 mock 由已构建的 W1 工作区提供：`ethercat_motor_drive` 包、W1 launch 和 YAML 不在本仓库内。Planner、TeachPanel 和焊接示例还需要该工作区的 `speedbot_msgs` 及相应服务提供方。只读节点本身不依赖 `speedbot_msgs`。没有 W1 工作区时可以运行本页末尾的隔离通信测试，但无法启动 W1 mock。

## 启动与发现

两个终端都加载 Humble 和 **W1 工作区** 的安装环境；将下面路径替换为本机实际位置。域 83 是示例所选的本机测试域，应选用空闲域。跨电脑接入时，两端使用实际控制器所在域、设置 `ROS_LOCALHOST_ONLY=0`，并确保网络支持 DDS 发现。

```bash
source /opt/ros/humble/setup.bash
source /path/to/w1_ws/install/setup.bash
export ROS_DOMAIN_ID=83
export ROS_LOCALHOST_ONLY=1
```

终端 1 启动 W1 mock、RViz 和 Planner。只检查底层状态时可省略 `moveit:=true`；视觉节点另行启动。

```bash
ros2 launch ethercat_motor_drive motor_drive-speed_W1_v1_2.launch.py bSim:=true moveit:=true
```

终端 2 检查机型、活动控制器、反馈、PVT 订阅者和规划服务：

```bash
ros2 param get /mit_controller robot_model
ros2 control list_controllers -c /controller_manager
ros2 topic echo /joint_states --once --qos-reliability best_effort
ros2 topic info /rl_motion_control_command_pvt -v
ros2 service type /plan_move
ros2 service call /mit_controller/get_pvt_interpolation_status std_srvs/srv/Trigger '{}'
```

预期模型为 `speed_W1_v1.2`、`mit_controller` 为 `active`，规划服务类型为 `speedbot_msgs/srv/PlanMove`。默认插补配置就绪、首帧发送前，PVT 查询返回 `success=true, message=waiting`。真机接入还需核对驱动交接和反馈新鲜度；W1 启动 gate 在配置轴全部接管后记录 `MIT first commands accepted by all configured drive plugins`。

## 状态接口

下表方向以外部应用为视角，均为订阅接收。

| 话题                                                  | 消息类型                              | 字段与单位                                                                                                                                        | 可用条件                                                           |
| ----------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `/joint_states`                                       | `sensor_msgs/msg/JointState`          | 按 `name[i]` 关联 `position[i]`（rad）、`velocity[i]`（rad/s）、`effort[i]`（N·m，含义取决于驱动映射）；`header.stamp` 为消息时间                 | mock、真机；按名提取受控轴，忽略被动脚趾等附加关节或仅含被动轴的帧 |
| `/imu/data`                                           | `sensor_msgs/msg/Imu`                 | `frame_id=base_link`；四元数 x/y/z/w、角速度 rad/s、加速度 m/s²；W1 broadcaster 已做安装旋转换算                                                  | 真机 FSS broadcaster；默认 mock 不提供这路硬件数据                 |
| `/motor_temperature_broadcaster/dynamic_joint_states` | `control_msgs/msg/DynamicJointState`  | 按 `joint_names` 找轴，再按对应 `interface_names` 读取 `values`，含 `initialized`、`controller_owned`、`status_word`、`error_code` 和配置的温度项 | W1 真机，当前配置 10 Hz                                            |
| `/diagnostics`                                        | `diagnostic_msgs/msg/DiagnosticArray` | `status[].name/level/message/values`；先查 EtherCAT 聚合项及总线项，再按轴定位                                                                    | 已启用硬件状态监控；总线 OK 与逐轴接管需分别检查                   |

关节和 IMU 读端可用传感器 QoS。实际发布频率、QoS 和硬件数据是否存在，应在运行系统中检查：

```bash
ros2 topic info /joint_states -v
ros2 topic hz /joint_states
ros2 topic echo /imu/data --once --qos-reliability best_effort
```

### JointState 与 QoS

标准 `JointState` 的 `position`、`velocity`、`effort` 可以为空，非空时须与 `name` 等长。该读端进一步要求名称非空、不重复、至少一组状态数组非空，以及数据为有限数值；从合法消息按名提取 `right_elbow_joint` 的位置，忽略没有目标轴或没有位置数据的帧。数组顺序不需要与 28 轴命令顺序一致。未知力矩应保持空数组，不以零冒充真实测量。

订阅端使用 Humble 的 `qos_profile_sensor_data`：`BEST_EFFORT`、`VOLATILE`、`KEEP_LAST`、depth 5。它可接收兼容的 best-effort 或 reliable 发布者；要求 reliable 的订阅器无法与 best-effort 发布者匹配。服务客户端使用 ROS 默认服务 QoS。Remap 只改变端点名，不转换消息类型或单位。

标准定义可查阅 ROS 官方的 [JointState 消息](https://github.com/ros2/common_interfaces/blob/humble/sensor_msgs/msg/JointState.msg)和 [Humble QoS profiles](https://github.com/ros2/rmw/blob/humble/rmw/include/rmw/qos_profiles.h)。

`header.stamp` 是采集时间；本例用单调时钟限制等待，并未检查采集时间是否过旧。仿真 `/clock` 暂停不会让等待无限持续。该节点用于接口读取，不提供运动前的反馈新鲜度验收或实时控制保证。

## 只读节点：关节反馈与 PVT 状态

从**本仓库根目录**构建，保留终端 2 已加载的 W1 环境和域设置：

```bash
colcon --log-base examples/ros2/log build \
  --base-paths examples/ros2/src \
  --build-base examples/ros2/build \
  --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
ros2 run w1_docs_ros2 state_reader
```

节点先读取右肘角度，再异步调用 `/mit_controller/get_pvt_interpolation_status`（`std_srvs/srv/Trigger`），输出一条 JSON。字段包括 `joint_name`、`position_rad`、`stamp`、`frame_id` 和 `pvt: {success, message}`；数值来自本次反馈与响应。收到其他有效 PVT 状态时也原样输出，不能把固定的 `waiting` 当作每次运行的结果。

服务返回 `success=false` 时仍输出响应 JSON，再以退出码 4 结束；未取得响应的超时不会输出该 JSON。通过 `ros2 run` 运行时，非零退出可能在 stdout 追加 `[ros2run]: Process exited with failure N`，自动化解析需识别 JSON 行。退出 0 只表示读到位置并查询成功，不表示机器人已具备运动条件。

| 参数                      | 默认值              | 含义                             |
| ------------------------- | ------------------- | -------------------------------- |
| `joint_name`              | `right_elbow_joint` | 需要读取的关节名                 |
| `timeout_seconds`         | `5.0`               | 等待有效目标关节位置的最长时间   |
| `service_timeout_seconds` | `5.0`               | 服务发现、服务响应各自的最长时间 |

默认三个阶段最多分别等待 5 秒，合计等待预算为 15 秒。ROS 浮点参数使用 `5.0`，避免写成整数类型。参数在启动时读取。

```bash
ros2 run w1_docs_ros2 state_reader --ros-args \
  -p joint_name:=right_elbow_joint \
  -p timeout_seconds:=5.0 -p service_timeout_seconds:=5.0
```

有命名空间的部署可映射两个**绝对端点**。下例 `/robot` 是部署命名空间示意：

```bash
ros2 run w1_docs_ros2 state_reader --ros-args \
  -r /joint_states:=/robot/joint_states \
  -r /mit_controller/get_pvt_interpolation_status:=/robot/mit_controller/get_pvt_interpolation_status
```

| 退出码 | 含义                                                     |
| ------ | -------------------------------------------------------- |
| 0      | 成功读取关节位置，状态服务返回 `success=true`            |
| 2      | 消息校验失败，或参数类型/范围不合法                      |
| 3      | 等待反馈、服务发现或服务响应超时                         |
| 4      | 服务调用失败或返回 `success=false`；需检查响应状态及原因 |
| 130    | Ctrl+C 或上下文关闭                                      |

### 完整源码

此节点只订阅状态并查询服务，不调用 reset/stop、不发布运动命令。回调和异步服务由 `SingleThreadedExecutor` 驱动；服务等待位于回调之外，避免在同一执行器回调中阻塞等待自身的响应。结束时释放执行器、节点与 context。

::: code-group
<<< ../../../examples/ros2/src/w1_docs_ros2/w1_docs_ros2/state_reader.py{python:line-numbers}
:::

源码是构建和网页展示的同一份文件。包清单和安装入口如下：

::: code-group
<<< ../../../examples/ros2/src/w1_docs_ros2/package.xml{xml:line-numbers} [package.xml]
<<< ../../../examples/ros2/src/w1_docs_ros2/setup.py{python:line-numbers} [setup.py]
<<< ../../../examples/ros2/src/w1_docs_ros2/setup.cfg{ini:line-numbers} [setup.cfg]
:::

## PVT 命令与回放

W1 默认控制器为 500 Hz，双臂 P/V 插补期望 100 Hz 输入。`/rl_motion_control_command_pvt` 使用 `std_msgs/msg/Float64MultiArray`，84 项按 **28 个 q + 28 个 qd + 28 个 τff** 拼接，单位分别为 rad、rad/s、N·m。重置会话后，`layout.dim` 恰好一项，`label` 逐字使用 reset 返回的令牌；回放器同时设置 `size=84, stride=84`。

开始流程为 reset → 查询到 `success=true, waiting` → 从保持位置发首帧（速度、前馈均为零）→ 持续发布同一令牌。选中关节首帧位置容差默认 0.001 rad。50 Hz 源需匹配 0.02 s 配置并重载控制器。停止请求返回成功仅表示接受，需继续查到 `stopped` 或 `fault`，且只作用于插补轴。

完整的五个命令入口、关节顺序、三个会话服务和硬件映射见 [W1 整机控制接口](../api/w1-control.md)。默认双臂插补会限制全身 P、P+KP+KD 及双臂位置入口，不能直接套用未启用插补时的发送例程。

W1 安装包中的 horizontal400 回放器包含反馈检查、首姿态过渡、令牌和停止处理。先执行离线检查：

```bash
controller_share=$(ros2 pkg prefix --share ethercat_motor_drive)
bash "$controller_share/docs/examples/trajtest_w1_horizontal400.sh" --check-only
```

资料给出的离线摘要为 `6800 frames, 28 controlled joints, 100 Hz`。下面命令会实际发送约 68 秒轨迹，另含过渡与保持；只在前述已启动的 W1 mock、同一隔离域内进行本例的发布测试：

```bash
bash "$controller_share/docs/examples/trajtest_w1_horizontal400.sh"
```

默认回放力矩前馈为零；仍需检查在线 PVT 状态和反馈。脚本、轨迹及其依赖由 `ethercat_motor_drive` 安装包提供，本仓库不含这些文件。

## 双臂规划与示教

| 接口                                | 方式与类型                                                                               | 参数、单位与返回                                                                                                               |
| ----------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `/plan_move`                        | Planner 服务，`speedbot_msgs/srv/PlanMove`                                               | 每次选择一侧臂，7 个目标角，**rad**；起点取当前反馈，`execute=false` 只规划                                                    |
| `/plan_move/stop`                   | Planner 服务，`std_srvs/srv/Trigger`                                                     | 空请求，停止 Planner 发布执行轨迹                                                                                              |
| `/arm_move`                         | TeachPanel 话题，`std_msgs/msg/Float64MultiArray`                                        | 单臂 7 个**度数**，`layout.dim[].label` 为 `left_arm`/`right_arm`；双臂 MOVE_J 为 14 个度数，左臂在前；入队后无 topic 完成响应 |
| `/left_arm_move`、`/right_arm_move` | Planner **服务**为 `speedbot_msgs/srv/ArmMoveJointState`；Teach 同名**话题**是旧兼容入口 | Planner 服务按反馈和目标规划并请求执行；新接入只规划用 `/plan_move`，排入示教队列用 `/arm_move`                                |

### 仅规划右臂

| 方向 | 字段                                       | 含义                                                                     |
| ---- | ------------------------------------------ | ------------------------------------------------------------------------ |
| 请求 | `id`、`arm_name`、`planner_id`             | 字符串标记、臂组 `left_arm/right_arm`、规划器标识                        |
| 请求 | `goal_joint_state.data`、`execute`         | 按所选 MoveIt 臂组顺序排列的 7 个 rad；是否进入执行路径                  |
| 响应 | `success`、`message`                       | 结合本次 `execute` 解释；目标、当前状态或场景均可能导致规划失败          |
| 响应 | `trajectory`、`scene_version`、`replanned` | `JointTrajectory` 含 `joint_names`、`points`；另返回场景版本及是否重规划 |

前面的 `moveit:=true` 启动服务。以下调用只规划；成功时检查轨迹关节名和点，失败时检查 `message`：

```bash
ros2 service call /plan_move speedbot_msgs/srv/PlanMove \
  "{id: w1_demo, arm_name: right_arm, planner_id: RRTConnectkConfigDefault, goal_joint_state: {data: [0.0, -1.36, 0.0, 0.1, 0.0, 0.0, 0.0]}, execute: false}"
```

### 向 Teach 提交右臂 MOVE_J

此调用会提交运动任务。用于已加载七轴 TeachPanel、并以**关闭双臂 PVT 插补**配置重新启动的 mock；前面的默认配置只满足上述只规划例程。Teach 的目标使用度，Planner 和底层控制使用 rad。

```bash
ros2 topic pub --once /arm_move std_msgs/msg/Float64MultiArray \
  "{layout: {dim: [{label: right_arm, size: 7, stride: 7}]}, data: [0.0, -78.0, 0.0, 5.0, 0.0, 0.0, 0.0]}"
```

## 焊接应用服务

外部应用调用 Capture；视觉节点采集并识别焊缝后，调用 W1 TeachPanel 的 Build 服务完成预检、保存及可选入队。

| 接口                                      | 类型与提供方                                                         | 调用条件                                                                         |
| ----------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `/weld_vision/capture_and_generate`       | `speedbot_msgs/srv/CaptureWeldProgram`，W1 视觉节点                  | 相机、W1 实测手眼标定、拍照期间静止、新鲜反馈及 `waist_yaw ← right_wrist_yaw` TF |
| `/teach_mode_panel/build_weld_program_w1` | `speedbot_msgs/srv/BuildWeldProgramW1`，启用焊接模块的 W1 TeachPanel | 有效 TCP；拍照姿态为右臂 7 项 rad；输入几何在 `waist_yaw` 系，点与偏移单位 m     |

| Capture 字段              | 类型/单位    | 含义                                                                                       |
| ------------------------- | ------------ | ------------------------------------------------------------------------------------------ |
| 请求 `auto_execute`       | bool         | false：生成并保存；true：保存后入执行队列                                                  |
| 响应 `success`、`message` | bool、string | 采集、识别、生成结果；自动执行时成功截至入队，不表示焊接已完成                             |
| 响应 `program_path`       | string       | 成功时是服务端文件系统的程序绝对路径；失败为空                                             |
| 响应 `weld_length`        | float64，mm  | 最终规划采用的焊缝长度；失败为 0。Build 的 `executed_lengths` 单位是 m，表示规划选用的长度 |

将标定路径换为该 W1 的实测文件，启动视觉节点后，在另一个已加载相同环境的终端调用 Capture。`auto_execute: false` 会拍照并写入程序文件，保留待检查；纯 mock 只能用于端点发现，完整生成依赖相机、标定和面板。

```bash
ros2 run weld_seam_vision weld_seam_vision_w1_node --ros-args \
  -p calibration_info:=/path/to/measured_w1_calibration.yml
# 另一个终端
ros2 service type /teach_mode_panel/build_weld_program_w1
ros2 service call /weld_vision/capture_and_generate speedbot_msgs/srv/CaptureWeldProgram \
  '{auto_execute: false}'
```

## 验证与排查

仅验证本仓库只读客户端时，无需 W1 驱动包。加载 Humble、构建并 source 本页的 `w1_docs_ros2` 安装后，从仓库根目录执行：

```bash
colcon --log-base examples/ros2/log test \
  --build-base examples/ros2/build --install-base examples/ros2/install \
  --packages-select w1_docs_ros2 --python-testing pytest
colcon test-result --test-result-base examples/ros2/build --verbose
ROS_LOCALHOST_ONLY=1 ROS_DOMAIN_ID=169 python3 examples/ros2/test_cli.py
```

169 应为本机空闲测试域。CLI 测试只在独立的 remap 端点运行状态发布者和 Trigger 服务替身，覆盖客户端的读取、过滤、校验、超时及服务失败处理。它不启动 W1 控制器，也不代表 W1 硬件、规划器或焊接服务验收。

| 现象                                                                                | 检查项                                                                                                      |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 找不到 `ethercat_motor_drive` 或 `speedbot_msgs`                                    | 是否已取得并加载相应 W1 工作区；文档仓库只构建读端                                                          |
| 看不到话题或服务                                                                    | install、域、localhost、RMW 和 DDS 网络发现；分别用 `ros2 topic list -t`、`ros2 service list -t` 检查提供方 |
| 反馈超时                                                                            | `JointState` 类型、QoS、目标轴名称、位置数组；只有被动关节的帧会继续等待                                    |
| PVT 服务发现/响应超时                                                               | 控制器是否启动、服务名称和 remap、服务端执行是否阻塞；检查本次超时所处阶段                                  |
| 发现 PVT 订阅者仍在等待                                                             | 控制器就绪、令牌、84 项顺序、首帧位置；若已故障先读取原因并等待制动完成                                     |
| 规划成功但执行时手臂无响应                                                          | 区分只规划、入队、执行；检查双臂 PVT 占用及位置入口条件，核对度与 rad                                       |
| Humble 的 `ros2 interface show speedbot_msgs/srv/PlanMove` 报 `InvalidResourceName` | 资料记录当前包安装布局可触发 CLI 展开错误；用下面 Python 字段检查和在线服务类型核对                         |

```bash
python3 -c 'from speedbot_msgs.srv import PlanMove; print(PlanMove.Request.get_fields_and_field_types())'
ros2 service type /plan_move
```

## 资料与验证范围

接口资料为本仓库 `tmp/W1_ROS2通讯接口示例.md`、`tmp/整机控制接口README.md`，W1 专文约定优先。原文 2026-11-20 的验证记录为：W1 无界面 mock 读到右肘 0.0000 rad、PVT `waiting`；只规划请求成功并产生 183 个轨迹点；100 Hz 回放通过离线检查，Teach/Capture 校验了消息字段。**这是来源记录，不是本次文档集成重新运行的结果**，轨迹点数也不是固定值。来源未进行实机运动、相机采集和焊接执行验证。

本仓库测试覆盖示例客户端与文档构建；完整 W1 联调需在已交付的对应工作区中进行。后续可在 [SDK 集成](./integration.md)补充精确软件版本、固件组合和设备部署记录。
