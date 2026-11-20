# W1 整机控制接口

适用于 `speed_W1_v1.2`：28 个受控轴、七轴双臂、ROS 2 Humble。本文结合 W1 专用通讯文档与整机接口文档，采用 W1 当前双臂 PVT 插补约定。启动、只读节点及 Planner、Teach、焊接服务的调用见 [ROS 2 接口示例](../sdk/ros2-example.md)。

本页的 28 轴指上述接口配置。产品参考参数中的 27 自由度与该配置的对应关系尚待确认，见[型号与规格](../product/specifications.md)。

## 机型与配置

| 项目          | W1 配置                                                 |
| ------------- | ------------------------------------------------------- |
| 驱动包        | `ethercat_motor_drive`                                  |
| 启动入口      | `motor_drive-speed_W1_v1_2.launch.py`                   |
| 模型参数      | `/mit_controller` 的 `robot_model` 为 `speed_W1_v1.2`   |
| 配置文件      | 包 share 目录下 `config/controllers-speed_W1_v1_2.yaml` |
| 轴数          | 全身 28；腿腰 14；双臂 14                               |
| 控制器更新率  | 500 Hz                                                  |
| 默认 PVT 输入 | 100 Hz；仅双臂的位置和速度进行插补                      |

配置、驱动和轨迹资源由 W1 工作区提供，不包含在文档仓库中。加载该工作区的 `install/setup.bash` 后，可查询安装路径与运行参数：

```bash
ros2 pkg prefix --share ethercat_motor_drive
ros2 param get /mit_controller robot_model
ros2 param get /mit_controller joints
ros2 control list_controllers -c /controller_manager
```

插补启停和名义周期在控制器初始化时读取。若源频率是 50 Hz，需要匹配 0.02 s 周期配置并重新加载控制器，不能直接沿用默认 100 Hz 配置。其他机型的 25/26 轴数据不可直接用于本页的 28 轴 W1。

## 命令话题与数据块

以下入口均使用 `std_msgs/msg/Float64MultiArray`，订阅深度 10，默认可靠传输。位置为绝对关节角。`+` 表示整块拼接，不是按每个关节交错排列。

| 话题                                    | `data`                        | 默认 W1 配置下的限制                                                       |
| --------------------------------------- | ----------------------------- | -------------------------------------------------------------------------- |
| `/rl_motion_control_command_pvt`        | 84 项：q + qd + τff           | 全身流式入口；重置会话后每帧必须携带令牌                                   |
| `/rl_motion_control_command`            | 28 项全身 q；兼容 12 项腿部 q | 28 项覆盖已选中的臂轴，会被拒绝；12 项不包含腰和臂                         |
| `/rl_motion_control_command_with_kp_kd` | 84 项：q + kp + kd            | 覆盖双臂，需关闭双臂 PVT 插补                                              |
| `/lower_body_joint_position_command`    | 14 项：双腿 + 腰 q            | 可单独控制腿腰；新会话首个有效 PVT 帧前存在保持门控                        |
| `/arm_joint_position_command_165`       | 14 项：左臂 7 + 右臂 7，q     | `_165` 是历史后缀；Teach/Planner 通过此入口执行位置流时需关闭双臂 PVT 插补 |

| 块            | PVT             | P+KP+KD       |
| ------------- | --------------- | ------------- |
| `data[0:28]`  | q，rad          | q，rad        |
| `data[28:56]` | qd，rad/s       | kp，N·m/rad   |
| `data[56:84]` | τff，关节侧 N·m | kd，N·m·s/rad |

每一块均采用下一节的 28 轴顺序，值必须有限；没有合并 P/V/T/KP/KD 的 5N 项入口。P 与 P+KP+KD 清除其控制关节的 V/T；P/PVT 使用 YAML 中的 KP/KD；分组位置指令保留其他关节的目标。上述数据语义不绕过默认双臂插补的入口限制。

调用方负责 action 缩放、初始偏置、单位转换、关节重排和模型限幅；电机方向、减速比和并联踝换算由驱动处理。多个话题可写同一关节，一次回放只使用一个有效命令源。

## 28 轴顺序与 Home

下标从 0 开始。PVT 和增益格式的三个数据块复用此顺序；`/joint_states` 反馈仍应按名称提取，不能假定反馈数组位置与命令顺序一致。

| 下标 | 关节名                       | Home（rad） |
| ---- | ---------------------------- | ----------- |
| 0    | `left_hip_pitch_joint`       | 0           |
| 1    | `left_hip_roll_joint`        | 0           |
| 2    | `left_hip_yaw_joint`         | 0           |
| 3    | `left_knee_joint`            | 0           |
| 4    | `left_ankle_pitch_joint`     | 0           |
| 5    | `left_ankle_roll_joint`      | 0           |
| 6    | `right_hip_pitch_joint`      | 0           |
| 7    | `right_hip_roll_joint`       | 0           |
| 8    | `right_hip_yaw_joint`        | 0           |
| 9    | `right_knee_joint`           | 0           |
| 10   | `right_ankle_pitch_joint`    | 0           |
| 11   | `right_ankle_roll_joint`     | 0           |
| 12   | `waist_yaw_joint`            | 0           |
| 13   | `waist_pitch_joint`          | 0           |
| 14   | `left_shoulder_pitch_joint`  | 0           |
| 15   | `left_shoulder_roll_joint`   | -1.36       |
| 16   | `left_shoulder_yaw_joint`    | 0           |
| 17   | `left_elbow_joint`           | 0           |
| 18   | `left_wrist_roll_joint`      | 0           |
| 19   | `left_wrist_yaw_joint`       | 0           |
| 20   | `left_wrist_pitch_joint`     | 0           |
| 21   | `right_shoulder_pitch_joint` | 0           |
| 22   | `right_shoulder_roll_joint`  | -1.36       |
| 23   | `right_shoulder_yaw_joint`   | 0           |
| 24   | `right_elbow_joint`          | 0           |
| 25   | `right_wrist_roll_joint`     | 0           |
| 26   | `right_wrist_yaw_joint`      | 0           |
| 27   | `right_wrist_pitch_joint`    | 0           |

Home 来自 `init_state.default_joint_angle`，与同一 launch 的 RViz Home 一致。当前配置 `hold_current_state_on_activate: true`，激活时保持实测位置，**不会自动回到 Home**。接入策略应从当前反馈平滑过渡到目标初姿态；以现场已安装 YAML 和运行中 `joints` 参数为准。

## PVT 会话令牌与首帧

重置后的 PVT 消息需要 `layout.dim` **恰好一项**：`label` 逐字使用 reset 成功响应的令牌；W1 回放器同时设置 `size=84, stride=84`。旧令牌或缺少令牌的帧会被忽略。不能沿用通用数组消息中“layout 可留空”的做法。

三个服务均位于 `/mit_controller/` 下，类型为 `std_srvs/srv/Trigger`。请求为空，响应含 `bool success`、`string message`。

| 服务                           | 用途                   | 响应处理                                                                                                                                   |
| ------------------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `get_pvt_interpolation_status` | 查询状态               | `waiting` 等待首帧；`buffering/running/holding` 为流处理状态；`fault_braking/fault` 含原因；`disabled/inactive/resetting` 需等待或检查配置 |
| `reset_pvt_interpolation`      | 在可重置状态申请新会话 | 成功后 `message` 是令牌；继续查询到 `success=true, message=waiting` 才能发首帧                                                             |
| `stop_pvt_interpolation`       | 请求选中的插补轴制动   | `success=true` 仅表示请求已接受；继续查询到 `stopped` 或 `fault`                                                                           |

一次会话的流程为：

1. 确认控制器就绪、反馈稳定，调用 reset 并保存返回的令牌。
2. 查询到 `waiting`，从保持位置开始；首帧速度与前馈均置零。选中关节的首帧位置容差默认 0.001 rad。
3. 按默认 100 Hz 发布 84 项数据，每帧携带同一令牌。
4. 停止时调用 stop，并查询最终状态。此服务只作用于插补轴，整机急停使用设备自身路径。

该流程的反馈验收、过渡、令牌和停止处理已由 W1 包内 `docs/examples/trajtest_w1_horizontal400.sh` 实现。其使用条件和离线检查见 [ROS 2 示例](../sdk/ros2-example.md#pvt-命令与回放)。

## 真机字段映射与反馈

当前 W1 真机腿部具有 τff 前馈映射；腰部 TI CSP 和手臂 HSA CSP **不周期下发该前馈**。不要把通用控制结构中的字段绑定等同于每个驱动的周期下发能力。`tau_ff=0` 也不代表电机实际输出力矩为零，mock 不能验证真实电机效果。

读取 `/joint_states` 时，按名称选择受控轴，忽略附加被动关节或仅含被动关节的帧。`effort` 的物理含义依赖驱动映射，不能把所有反馈直接当作真实力矩。硬件接管、温度、错误码和总线状态分别从动态关节状态及诊断话题检查，见 [状态接口](../sdk/ros2-example.md#状态接口)。

就绪条件包括活动控制器和驱动交接。W1 启动 gate 在配置轴全部接管后记录 `MIT first commands accepted by all configured drive plugins`。总线 OK 与逐轴接管需要分别确认。

## 资料来源与适用范围

资料来自本仓库 `tmp/W1_ROS2通讯接口示例.md` 与 `tmp/整机控制接口README.md`。W1 专文优先于整机文档中的通用或历史配置描述：本文使用当前 100 Hz 双臂插补、会话令牌和真机前馈映射，不沿用旧的 50/500 Hz 无插补回放条件。

安装包应同时交付 YAML、`docs/examples/` 回放入口与轨迹，以及对应回放依赖。更改配置或数据后需重新构建 W1 工作区以更新 install 副本。本文不提供未随资料交付的驱动源码、轨迹数据或标定文件；精确软件提交和固件版本仍需随发布记录补充。
