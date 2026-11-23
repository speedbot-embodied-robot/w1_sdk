# Python：录制 W1 关节反馈

这个示例使用 ROS 2 Humble 订阅 W1 的 `/joint_states`，将收到的反馈按 JSON Lines 格式保存到本地文件。它适合保存一段状态数据供离线排查或分析；只订阅状态，不发布控制命令，也不启动机器人。

## 环境

需要 Ubuntu 22.04、Python 3.10 和 ROS 2 Humble。录制包使用 `rclpy`、`sensor_msgs`，随仓库的 `w1_docs_ros2` 一起构建；连接 W1 时还需加载已构建的 W1 工作区。安装环境、ROS 域和网络发现准备方式见 [W1 ROS 2 接口示例](./ros2-example.md)。

从仓库根目录执行。先加载 ROS 2 Humble；连接 W1 时，再加载与控制器匹配的工作区并沿用控制器实际使用的 ROS 域。跨电脑通信需让两端都允许网络发现，例如设置 `ROS_LOCALHOST_ONLY=0`。

```bash
source /opt/ros/humble/setup.bash
# 连接 W1 时，先加载控制器工作区
# source /path/to/w1_ws/install/setup.bash

colcon --log-base examples/ros2/log build \
  --base-paths examples/ros2/src \
  --build-base examples/ros2/build \
  --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
```

## 录制

选择一个尚不存在的输出文件，然后运行：

```bash
ros2 run w1_docs_ros2 record_joint_states --ros-args \
  -p output_path:=/tmp/w1-joint-states.jsonl \
  -p duration_seconds:=10.0 \
  -p timeout_seconds:=5.0
```

节点默认订阅 `/joint_states`，录制 10 秒；如果启动后 5 秒没有收到有效消息，或有效消息间隔超过 5 秒，就以超时退出。`output_path` 默认是当前目录下的 `joint_states.jsonl`。文件以独占方式新建，已存在时拒绝覆盖；更换路径或文件名后重试。

## JSONL 内容

文件第一行是格式元数据，后续每行对应一条收到的 `sensor_msgs/msg/JointState`：

| 字段                             | 含义                                                                      |
| -------------------------------- | ------------------------------------------------------------------------- |
| `record_type`、`schema_version`  | 行类型和本地文件格式版本；元数据行为 `metadata`，反馈行为 `joint_state`   |
| `topic`、`message_type`          | 实际订阅的话题名与 ROS 消息类型，位于元数据行；默认话题为 `/joint_states` |
| `elapsed_seconds`                | 从录制开始计时到收到该帧的单调时钟经过时间                                |
| `stamp.sec`、`stamp.nanosec`     | 消息携带的 ROS 采集时间字段，由发布者填写，可能为零；不替换为本机接收时刻 |
| `frame_id`                       | 原消息的坐标系标记                                                        |
| `name`                           | 关节名称数组                                                              |
| `position`、`velocity`、`effort` | 按 ROS 消息原样保存的状态数组；没有该项数据时保留为空数组 `[]`            |

数组按各自相同索引与 `name` 对应。录制器要求 `name` 非空且名称唯一；`position`、`velocity`、`effort` 各自可以为空，非空时长度必须与 `name` 一致，数值须为有限值。没有某类状态时保留 `[]`，不补零或转成 `null`；三组状态数组都为空时也会按原消息保存。应按关节名匹配，不要假设反馈排列等于控制命令中的 28 轴顺序。元数据注明转动关节与移动关节各字段单位；消息本身不含关节类型，解释数据时需结合实际机器人模型。`header.stamp` 由发布者填写，可能为零；本工具不验证时间新鲜度，也无法判断上游或 DDS 是否丢帧，只会保存本节点实际收到的消息。

订阅使用 ROS 2 Humble 的 `qos_profile_sensor_data`（`BEST_EFFORT`、`VOLATILE`、`KEEP_LAST`，depth 5），需与发布端 QoS 兼容。该配置不保证无丢帧，录制文件不应被视为完整、无损的控制器日志。

录制器源码：

::: code-group
<<< ../../../examples/ros2/src/w1_docs_ros2/w1_docs_ros2/record_joint_states.py{python:line-numbers}
:::

## 参数与退出码

| 参数               | 默认值               | 用途                                                     |
| ------------------ | -------------------- | -------------------------------------------------------- |
| `output_path`      | `joint_states.jsonl` | 输出路径；相对路径以当前工作目录为基准，文件必须尚不存在 |
| `duration_seconds` | `10.0`               | 从录制开始计时计算的最长时长                             |
| `timeout_seconds`  | `5.0`                | 等待首帧或两条有效帧之间的最长间隔                       |

| 退出码 | 含义                                                  |
| ------ | ----------------------------------------------------- |
| `0`    | 到达录制时长且已记录数据                              |
| `2`    | 参数错误、消息无效，或输出文件已存在                  |
| `3`    | 收到首帧前超时、连续数据超时，或录制时长内无数据      |
| `4`    | 录制队列或文件 I/O 错误，包括无法创建、写入或冲刷文件 |
| `130`  | Ctrl+C；已收到的记录会尝试冲刷到文件                  |

此工具只负责留存 ROS 状态，不检查控制器是否 ready、不验证反馈是否足够新鲜，也不代表设备可以安全运动。要单次读取指定关节并同时查询 PVT 状态，请用 [ROS 2 只读节点](./ros2-example.md#只读节点-关节反馈与-pvt-状态)。

## 隔离测试

仓库的隔离 ROS 测试使用本机独立发布端验证只读状态客户端与录制器文件输出；`state_reader` 测试另使用 Trigger 服务替身。不连接 W1 控制器。录制器覆盖多帧 JSONL、remap 后的话题元数据、数组保留、无数据超时、超时前后首帧、拒绝覆盖、无效帧和中断冲刷。构建环境后，从仓库根目录执行：

```bash
ROS_LOCALHOST_ONLY=1 ROS_DOMAIN_ID=169 python3 examples/ros2/test_cli.py
```

169 是本机测试域；若已被占用，请换成空闲域。测试替身只验证客户端与文件录制行为，不模拟 W1 控制器或其硬件。录制器接入真实或另行运行的测试发布端前，确认 ROS 域和网络发现设置正确。
