# SDK integration

This page explains how to build the public ROS 2 example package in this repository. The current official interface is `speed_W1_v1.2`, with 26 controlled joints and six axes on each arm.

## Environment

| Item                              | Local environment                            |
| --------------------------------- | -------------------------------------------- |
| Operating system and architecture | Ubuntu 22.04.5 LTS, x86_64                   |
| ROS 2 and Python                  | ROS 2 Humble, Python 3.10.12                 |
| Build tools                       | GCC 11.4.0, CMake 3.22.1, colcon-core 0.20.1 |
| ROS packages                      | rclpy 3.3.21, sensor_msgs 4.9.1              |

## Build the example package

From the repository root, source ROS 2 Humble and build the package:

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

## Run the examples

`state_reader` subscribes to `/joint_states` and reads `right_elbow_joint` by name. It only reads state:

```bash
ros2 run w1_docs_ros2 state_reader
```

To save continuous joint feedback, run the JSONL recorder. The output file must not already exist:

```bash
ros2 run w1_docs_ros2 record_joint_states --ros-args \
  -p output_path:=joint_states.jsonl \
  -p duration_seconds:=10.0 \
  -p timeout_seconds:=5.0
```

The W1 workspace must already be publishing `/joint_states`. This repository does not start a controller or provide robot hardware. On success, `state_reader` prints a JSON object with the joint position and timestamp. The recorder writes one metadata record followed by `sensor_msgs/msg/JointState` records in JSONL format.

| Exit code | Meaning                                              |
| --------- | ---------------------------------------------------- |
| 0         | State read or recording completed                    |
| 2         | Parameter, message, or output-file validation failed |
| 3         | Feedback or recording timeout                        |
| 4         | Recording file could not be written                  |
| 130       | Ctrl+C or ROS context shutdown                       |

See the [W1 ROS 2 interface examples](./ros2-example.md) and [whole-body control interface](../api/w1-control.md) for state topics, real-robot IMU and motor diagnostics, and the 26-axis control interface. When connecting to a robot, use compatible ROS domains and network discovery settings on both machines.

## Isolated tests

The isolated ROS tests use a local publisher to verify joint-state reading and recorder output without connecting to a W1 controller. After building the package, run from the repository root:

```bash
ROS_LOCALHOST_ONLY=1 ROS_DOMAIN_ID=169 python3 examples/ros2/test_cli.py
```

169 is a local test domain. If it is already in use, choose an available domain. The test uses synthetic state messages and does not simulate a W1 controller or hardware. Before connecting to a real system, verify the ROS domain and network discovery settings.
