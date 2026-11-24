# Integration details

This page records the locally verified W1 ROS 2 read-only example environment. The examples correspond to `speed_W1_v1.2` (28 controlled joints, seven joints on each arm). See the [W1 ROS 2 interface example](./ros2-example.md) and [W1 whole-body control reference](../api/w1-control.md) for the interface contract. This repository does not contain the W1 controller, driver, firmware, control YAML, or `speedbot_msgs`.

| Field                | Confirmed information                                                                                       |
| -------------------- | ----------------------------------------------------------------------------------------------------------- |
| Applicable device    | W1; `speed_W1_v1.2`, with 28 controlled joints and seven joints on each arm                                 |
| Local verification   | Ubuntu 22.04.5 LTS, x86_64, ROS 2 Humble, Python 3.10.12, GCC 11.4.0, and CMake 3.22.1                      |
| Example dependencies | `rclpy` 3.3.21, `sensor_msgs` 4.9.1, `std_srvs` 4.9.1, and `colcon-core` 0.20.1                             |
| Verification record  | 2026-11-23; documentation and ROS 2 example package checks passed; no W1 hardware was connected or verified |

## Get and install

This repository provides the public `w1_docs_ros2` example package under `examples/ros2/src/w1_docs_ros2/`. The W1 workspace, controller, driver, and firmware must come from the delivered device environment.

Build the example package in the locally installed ROS 2 Humble environment:

```bash
source /opt/ros/humble/setup.bash
colcon --log-base examples/ros2/log build \
  --base-paths examples/ros2/src \
  --build-base examples/ros2/build \
  --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
```

Verify the installation:

```bash
ros2 pkg prefix w1_docs_ros2
```

## Run the examples

`state_reader` subscribes to `/joint_states`, reads `right_elbow_joint` by name, and then queries `/mit_controller/get_pvt_interpolation_status`. It only reads state and sends no motion, reset, or stop command:

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

The examples require a W1 workspace that is already publishing the required topic and service. This repository does not start a controller and does not provide a W1 mock or real hardware. On success, `state_reader` prints one JSON object containing the joint position and PVT response; the recorder writes one metadata record and multiple `sensor_msgs/msg/JointState` JSONL records.

| Exit code | Meaning                                                         |
| --------- | --------------------------------------------------------------- |
| 0         | State read and PVT query succeeded, or recording completed      |
| 2         | Parameter, message, or output-file validation failed            |
| 3         | Feedback, service discovery, service response, or data timeout  |
| 4         | Service reported failure, or the recording file could not write |
| 130       | Ctrl+C or ROS context shutdown                                  |

Continue with the [W1 ROS 2 interface example](./ros2-example.md) and [W1 whole-body control reference](../api/w1-control.md).
