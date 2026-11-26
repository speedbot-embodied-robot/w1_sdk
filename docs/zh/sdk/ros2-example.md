# W1 ROS 2 接口示例

本文适用于当前正式 `speed_W1_v1.2` 配置，使用 ROS 2 Humble。该配置有 26 个受控关节，左右臂各 6 轴。连接真实机器人时，需要使用设备当前的 ROS 域和已启动的控制工作区。完整的命令顺序与数组长度见[整机控制接口](../api/w1-control.md)。

## 连接与核对

开发端应加载 ROS 2 Humble，并与 W1 使用相同的 `ROS_DOMAIN_ID`。跨主机通信时，双方需允许网络发现，例如 `ROS_LOCALHOST_ONLY=0`。

```bash
source /opt/ros/humble/setup.bash
# 已构建的 W1 工作区
source /path/to/w1_ws/install/setup.bash

ros2 control list_controllers -c /controller_manager
ros2 param get /mit_controller joints
ros2 topic info /joint_states -v
```

确认 `joint_state_broadcaster` 和 `mit_controller` 已处于 `active` 状态。`joints` 参数应与控制接口页的 26 轴命令顺序一致。话题真实发布频率和 QoS 可分别用 `ros2 topic hz`、`ros2 topic info -v` 检查。

## 状态话题

| 话题                                                  | 消息类型                              | 字段和单位                                                                                                               | 可用条件                                               |
| ----------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| `/joint_states`                                       | `sensor_msgs/msg/JointState`          | 按 `name[i]` 匹配 `position[i]`（rad）、`velocity[i]`（rad/s）、`effort[i]`（N·m）；`header.stamp` 是消息时间            | 仿真和真机。按名称提取受控关节，忽略被动脚趾等附加关节 |
| `/imu/data`                                           | `sensor_msgs/msg/Imu`                 | `header.frame_id` 为 `base_link`；姿态四元数 x/y/z/w、角速度 rad/s、线加速度 m/s²，数据已转换到 `base_link` 坐标系       | 真机 IMU；默认仿真不提供这路硬件数据                   |
| `/motor_temperature_broadcaster/dynamic_joint_states` | `control_msgs/msg/DynamicJointState`  | 按关节名与接口名从 `joint_names`、`interface_names`、`values` 查找；包括初始化、控制器接管、状态字、错误码及已配置温度项 | 真机硬件状态发布器，当前资料中的配置频率为 10 Hz       |
| `/diagnostics`                                        | `diagnostic_msgs/msg/DiagnosticArray` | 遍历 `status[]` 的 `name`、`level`、`message` 和 `values`，读取聚合与总线告警                                            | 启用了硬件状态监控的系统                               |
| `/fss_imu/temperature`                                | `std_msgs/msg/Float64`                | `data` 为温度标量，消息不含 Header                                                                                       | 真机 IMU 温度流                                        |

`JointState` 的速度和力矩数组可能为空，不能将空值补成零。`effort` 的物理含义取决于驱动映射。`DynamicJointState` 应先按关节名定位，再按接口名读取，数组顺序不应硬编码。诊断状态的 `level=0` 也不单独代表系统已就绪，例如监控项仍可能处于 `starting` 状态。

用于 TF 可视化的 `/joint_states_for_tf` 是单独支路。控制和数据采集应读取 `/joint_states`。

读取话题样例：

```bash
# 仿真或真机
ros2 topic echo /joint_states --once --qos-reliability best_effort
ros2 topic info /joint_states -v

# 对应硬件发布器和监控节点已启动的真机
ros2 topic echo /imu/data --once --qos-reliability best_effort
ros2 topic echo /motor_temperature_broadcaster/dynamic_joint_states --once --qos-reliability best_effort
ros2 topic echo /diagnostics --once
ros2 topic echo /fss_imu/temperature --once
```

## Python：读取关节与 IMU

下面的只读示例分别订阅关节和 IMU 话题，按关节名称取出右肘数据，并输出一条有效的 IMU 消息。两个话题独立到达，示例不进行时间同步。保存为 `read_w1_state.py` 后，在已 source ROS 环境的终端运行。

<<< ../../../examples/ros2/snippets/read_w1_state.py{python:line-numbers}

默认仿真没有 `/imu/data` 硬件流。若只想在仿真中验证 IMU 解析，可在同一 ROS 域发布测试消息，然后启动读端：

```bash
ros2 topic pub -r 5 /imu/data sensor_msgs/msg/Imu \
  "{header: {frame_id: base_link}, orientation: {w: 1.0}, angular_velocity: {z: 0.125}, linear_acceleration: {z: 9.81}}"
```

这条测试发布命令用于验证消息解析，不代表真实传感器数据。

## C++：读取单帧关节与 IMU

下面示例使用传感器 QoS 分别订阅两个话题，收到右肘位置和一条 `base_link` IMU 消息后退出。将代码保存为 ament C++ 包中的 `src/w1_state_reader.cpp`：

<<< ../../../examples/ros2/snippets/read_w1_state.cpp{cpp:line-numbers}

在 `package.xml` 和 `CMakeLists.txt` 中声明 `ament_cmake`、`rclcpp` 与 `sensor_msgs` 依赖，并在 `CMakeLists.txt` 中加入构建目标：

```cmake
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(w1_state_reader src/w1_state_reader.cpp)
ament_target_dependencies(w1_state_reader rclcpp sensor_msgs)
install(TARGETS w1_state_reader DESTINATION lib/${PROJECT_NAME})
ament_package()
```

执行 `colcon build --packages-select <your_package>`，然后 source `install/setup.bash` 并运行 `ros2 run <your_package> w1_state_reader`。两个话题是独立消息流，读取结果不保证来自同一采样时刻。

## 控制话题与数组布局

底层控制命令及 26 轴关节顺序见[整机控制接口](../api/w1-control.md)。常用入口如下：

| 话题                                    | 类型                             | 数组长度 | 数据                     |
| --------------------------------------- | -------------------------------- | -------: | ------------------------ |
| `/rl_motion_control_command_pvt`        | `std_msgs/msg/Float64MultiArray` |       78 | q[26] + qd[26] + τff[26] |
| `/rl_motion_control_command`            | `std_msgs/msg/Float64MultiArray` | 26 或 12 | 全身 q，或仅双腿 q       |
| `/rl_motion_control_command_with_kp_kd` | `std_msgs/msg/Float64MultiArray` |       78 | q[26] + kp[26] + kd[26]  |
| `/lower_body_joint_position_command`    | `std_msgs/msg/Float64MultiArray` |       14 | 双腿和腰部 q             |
| `/arm_joint_position_command_165`       | `std_msgs/msg/Float64MultiArray` |       12 | 左臂 q[6] + 右臂 q[6]    |

数组位置与单位必须符合接口定义。以下示例只展示如何组装 PVT 消息对象，不会发布运动命令：

```python
from std_msgs.msg import Float64MultiArray

q = [0.0] * 26
qd = [0.0] * 26
tau_ff = [0.0] * 26

if not (len(q) == len(qd) == len(tau_ff) == 26):
    raise ValueError("PVT arrays must each contain 26 values")

msg = Float64MultiArray()
msg.data = q + qd + tau_ff
assert len(msg.data) == 78
```

命令位置为绝对值。发送前应从当前反馈和设备模型确认目标、数组顺序、单位与限位。部署系统在发布前需完成控制器和执行器接管。

## 单臂与双臂示教

W1 默认提供双臂示教。`/arm_move` 接收度为单位的关节目标，单臂为 6 项，双臂为 12 项并按左臂在前排列。话题格式与示例见下方命令：

```bash
ros2 topic info /arm_move -v
ros2 topic pub --once /arm_move std_msgs/msg/Float64MultiArray \
  "{layout: {dim: [{label: right_arm, size: 6, stride: 6}]}, data: [0.0, -7.0, 0.0, 5.0, 0.0, 0.0]}"
```

这会提交运动目标。单臂示教话题为 `/left_arm_move` 和 `/right_arm_move`，各接收 6 项。当前默认部署未启用双臂规划服务 `/plan_move` 和焊接轨迹生成服务 `/weld_vision/capture_and_generate`。实际系统中的服务和类型请用 `ros2 service list -t` 查询。
