# 接入信息

本页记录本机已验证的 W1 ROS 2 只读示例环境。示例对应 `speed_W1_v1.2`（28 个受控轴、两侧各七轴），接口说明见 [W1 ROS 2 接口示例](./ros2-example.md) 和 [W1 整机控制参考](../api/w1-control.md)。本仓库不包含 W1 控制器、驱动、固件、控制 YAML 或 `speedbot_msgs`。

| 字段         | 已确认信息                                                                                |
| ------------ | ----------------------------------------------------------------------------------------- |
| 适用设备     | W1；`speed_W1_v1.2`，28 个受控轴、两侧各七轴                                              |
| 本机验证环境 | Ubuntu 22.04.5 LTS、x86_64、ROS 2 Humble、Python 3.10.12、GCC 11.4.0、CMake 3.22.1        |
| 示例依赖     | `rclpy` 3.3.21、`sensor_msgs` 4.9.1、`std_srvs` 4.9.1、`colcon-core` 0.20.1               |
| 验证记录     | 2026-11-23；文档构建和 ROS 2 示例包验证通过，未连接 W1 真机，不能据此确认固件或硬件兼容性 |

## 获取与安装

本仓库提供 `w1_docs_ros2` 公开示例包，源码位于 `examples/ros2/src/w1_docs_ros2/`。W1 工作区、控制器、驱动和固件需要从设备交付环境获取。

在本机安装的 ROS 2 Humble 环境中构建示例包：

```bash
source /opt/ros/humble/setup.bash
colcon --log-base examples/ros2/log build \
  --base-paths examples/ros2/src \
  --build-base examples/ros2/build \
  --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
```

验证安装结果：

```bash
ros2 pkg prefix w1_docs_ros2
```

## 运行示例

`state_reader` 订阅 `/joint_states`，按名称读取 `right_elbow_joint`，再查询 `/mit_controller/get_pvt_interpolation_status`。它只读状态，不发送运动、复位或停止命令：

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

运行示例需要已经启动并发布相应话题和服务的 W1 工作区；本仓库不启动控制器，也不提供真机或 W1 mock。成功时，`state_reader` 输出一条包含关节位置和 PVT 响应的 JSON；录制器生成一条元数据记录和多条 `sensor_msgs/msg/JointState` JSONL 记录。

| 退出码 | 含义                                         |
| ------ | -------------------------------------------- |
| 0      | 状态读取和 PVT 查询成功，或录制完成          |
| 2      | 参数、消息格式或输出文件校验失败             |
| 3      | 反馈、服务发现、服务响应或录制期间无数据超时 |
| 4      | 服务返回失败，或录制文件无法写入             |
| 130    | Ctrl+C 或 ROS context 关闭                   |

继续查看 [W1 ROS 2 接口示例](./ros2-example.md) 和 [W1 整机控制参考](../api/w1-control.md)。
