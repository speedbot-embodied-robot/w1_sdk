# SDK 集成

本页介绍仓库内公开 ROS 2 示例的构建方式。当前正式接口配置为 `speed_W1_v1.2`，包含 26 个受控关节，左右臂各 6 轴。

## 环境

| 项目            | 本机环境                                     |
| --------------- | -------------------------------------------- |
| 操作系统与架构  | Ubuntu 22.04.5 LTS、x86_64                   |
| ROS 2 与 Python | ROS 2 Humble、Python 3.10.12                 |
| 编译工具        | GCC 11.4.0、CMake 3.22.1、colcon-core 0.20.1 |
| ROS 包          | rclpy 3.3.21、sensor_msgs 4.9.1              |

## 构建示例包

从仓库根目录加载 ROS 2 Humble 后构建：

```bash
source /opt/ros/humble/setup.bash
colcon --log-base examples/ros2/log build \
  --base-paths examples/ros2/src \
  --build-base examples/ros2/build \
  --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
ros2 pkg prefix w1_docs_ros2
```

## 运行示例

`state_reader` 订阅 `/joint_states`，按名称读取 `right_elbow_joint`，只读取状态：

```bash
ros2 run w1_docs_ros2 state_reader
```

需要连续保存关节反馈时，运行 JSONL 录制器。输出文件必须不存在：

```bash
ros2 run w1_docs_ros2 record_joint_states --ros-args \
  -p output_path:=joint_states.jsonl \
  -p duration_seconds:=10.0 \
  -p timeout_seconds:=5.0
```

示例要求 W1 工作区已发布 `/joint_states`。本仓库不启动控制器，也不提供机器人硬件。成功时，`state_reader` 输出一条包含关节位置和时间戳的 JSON；录制器生成一条元数据记录和多条 `sensor_msgs/msg/JointState` JSONL 记录。

| 退出码 | 含义                         |
| ------ | ---------------------------- |
| 0      | 状态读取或录制完成           |
| 2      | 参数、消息或输出文件校验失败 |
| 3      | 反馈或录制超时               |
| 4      | 录制文件无法写入             |
| 130    | Ctrl+C 或 ROS context 关闭   |

ROS 2 状态话题的字段、真机 IMU/电机诊断读取以及 26 轴控制接口见 [W1 ROS 2 接口示例](./ros2-example.md) 和 [W1 整机控制](../api/w1-control.md)。连接机器人时，两端需使用兼容的 ROS 域与网络发现配置。

## 隔离测试

仓库的隔离 ROS 测试使用本机独立发布端验证关节状态读取与录制器文件输出，不连接 W1 控制器。构建环境后，从仓库根目录执行：

```bash
ROS_LOCALHOST_ONLY=1 ROS_DOMAIN_ID=169 python3 examples/ros2/test_cli.py
```

169 是本机测试域；若已被占用，请换成空闲域。测试使用合成状态消息，不模拟 W1 控制器或硬件。真实接入前，确认 ROS 域和网络发现设置。
