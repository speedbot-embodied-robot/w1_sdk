# W1 整机控制接口

本文适用于当前正式 ROS 2 控制配置 `speed_W1_v1.2`，环境为 ROS 2 Humble。该配置包含 26 个受控关节，左右臂各 6 轴。关节顺序、消息字段与上层接口以当前公开接口资料为准。

## 配置核对

加载对应 ROS 2 环境后，可查看控制器状态和运行时关节顺序：

```bash
ros2 control list_controllers -c /controller_manager
ros2 param get /mit_controller joints
```

预期活动控制器包括 `joint_state_broadcaster` 和 `mit_controller`。运行时 `joints` 列表应与下表一致。

## 控制话题

五个底层控制入口均使用 `std_msgs/msg/Float64MultiArray`，订阅深度为 10，默认可靠传输。位置值为绝对关节角。控制器更新率为 500 Hz。

| 话题                                    | 消息数据                            | 用途                                    |
| --------------------------------------- | ----------------------------------- | --------------------------------------- |
| `/rl_motion_control_command_pvt`        | 78 项：26 个 q、26 个 qd、26 个 τff | 全身位置、速度与关节侧力矩前馈          |
| `/rl_motion_control_command`            | 26 项全身 q，或 12 项双腿 q         | 12 项格式只更新双腿，腰与双臂保留原目标 |
| `/rl_motion_control_command_with_kp_kd` | 78 项：26 个 q、26 个 kp、26 个 kd  | 全身位置与逐关节增益                    |
| `/lower_body_joint_position_command`    | 14 项：双腿与腰部 q                 | 更新双腿和腰部位置                      |
| `/arm_joint_position_command_165`       | 12 项：左臂 6 项、右臂 6 项         | 更新双臂位置，话题后缀为历史名称        |

`q` 单位为 rad，`qd` 为 rad/s，`τff` 为 N·m，`kp` 为 N·m/rad，`kd` 为 N·m·s/rad。三个数据块按顺序拼接，不按关节交错排列。普通位置消息使用默认空 `layout`。只有 `/rl_motion_control_command_with_kp_kd` 从消息读取 `kp` 和 `kd`，其他位置与 PVT 入口使用配置中的增益。接受位置帧后，该帧覆盖关节的速度和前馈目标会置零。

## 26 轴命令顺序

下标从 0 开始。PVT 和带增益消息的三个数据块共用此顺序。`/joint_states` 的反馈顺序可能不同，读取反馈时应按关节名匹配。

| 下标 | 关节名                       |
| ---: | ---------------------------- |
|    0 | `left_hip_pitch_joint`       |
|    1 | `left_hip_roll_joint`        |
|    2 | `left_hip_yaw_joint`         |
|    3 | `left_knee_joint`            |
|    4 | `left_ankle_pitch_joint`     |
|    5 | `left_ankle_roll_joint`      |
|    6 | `right_hip_pitch_joint`      |
|    7 | `right_hip_roll_joint`       |
|    8 | `right_hip_yaw_joint`        |
|    9 | `right_knee_joint`           |
|   10 | `right_ankle_pitch_joint`    |
|   11 | `right_ankle_roll_joint`     |
|   12 | `waist_yaw_joint`            |
|   13 | `waist_pitch_joint`          |
|   14 | `left_shoulder_pitch_joint`  |
|   15 | `left_shoulder_roll_joint`   |
|   16 | `left_shoulder_yaw_joint`    |
|   17 | `left_elbow_joint`           |
|   18 | `left_wrist_yaw_joint`       |
|   19 | `left_wrist_pitch_joint`     |
|   20 | `right_shoulder_pitch_joint` |
|   21 | `right_shoulder_roll_joint`  |
|   22 | `right_shoulder_yaw_joint`   |
|   23 | `right_elbow_joint`          |
|   24 | `right_wrist_yaw_joint`      |
|   25 | `right_wrist_pitch_joint`    |

左右按机器人自身方向定义。正方向按对应关节坐标系的 URDF 轴定义和右手定则确定。被动脚趾关节可能出现在状态反馈中，但不属于这 26 项控制数组。

### PVT 数据布局

| 下标范围      | 字段             | 单位  |
| ------------- | ---------------- | ----- |
| `data[0:26]`  | 全身位置 q       | rad   |
| `data[26:52]` | 全身速度 qd      | rad/s |
| `data[52:78]` | 全身力矩前馈 τff | N·m   |

真机上腿部支持力矩前馈。腰部和双臂采用位置控制，对应的前馈项填 0。右膝命令下标为 9，因此该轴在位置、速度和前馈块中的位置分别为 `data[9]`、`data[35]`、`data[61]`。

### 位置数组范围

`/rl_motion_control_command` 可发送 26 项全身位置，或 12 项双腿位置。12 项数组只含左右腿，不含腰和双臂。

`/lower_body_joint_position_command` 顺序为 0–13，即双腿和腰部。`/arm_joint_position_command_165` 顺序为左臂下标 14–19，随后右臂下标 20–25。

发送前应核对数组长度、有限数值、关节顺序和目标范围。不要假定状态反馈数组与控制数组同序。多个控制话题可能覆盖相同关节，单次控制任务应使用一个有效命令入口。

## 双臂示教接口

W1 示教面板通过 `/arm_move` 接收关节目标，单位为度。单臂目标为 6 项，双臂目标为 12 项并按左臂在前排列。示教面板通过 `/arm_joint_position_command_165` 输出 12 项弧度位置目标。

| 话题                                | 类型                             | 数据格式                                                                                      |
| ----------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------- |
| `/arm_move`                         | `std_msgs/msg/Float64MultiArray` | 单臂 6 项，`layout.dim[].label` 为 `left_arm` 或 `right_arm`；双臂 12 项，标签可用 `dual_arm` |
| `/left_arm_move`、`/right_arm_move` | `std_msgs/msg/Float64MultiArray` | 旧版单臂话题，每侧 6 项                                                                       |

示教话题示例会向已加载示教面板的系统提交右臂目标：

```bash
ros2 topic info /arm_move -v
ros2 topic pub --once /arm_move std_msgs/msg/Float64MultiArray \
  "{layout: {dim: [{label: right_arm, size: 6, stride: 6}]}, data: [0.0, -7.0, 0.0, 5.0, 0.0, 0.0]}"
```

发布该话题会提交运动目标。使用前应确认连接的是预期的仿真或机器人系统，且目标符合当前设备配置。

## 服务可用性

默认部署提供双臂示教。双臂规划服务 `/plan_move` 和焊接程序生成服务 `/weld_vision/capture_and_generate` 默认未启用。连接到具体系统后，可用以下命令查看实际服务及类型：

```bash
ros2 service list -t
```

相关状态话题、消息字段、QoS 和示例命令见 [W1 ROS 2 接口示例](../sdk/ros2-example.md)。
