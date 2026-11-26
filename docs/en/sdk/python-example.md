# Python: record W1 joint feedback

This example subscribes to W1's `/joint_states` topic with ROS 2 Humble and saves received feedback to a local JSON Lines file. The recording can support offline inspection and analysis. The node only subscribes to state; it publishes no control command and does not start the robot.

## Environment

Requires Ubuntu 22.04, Python 3.10 and ROS 2 Humble. The recorder uses `rclpy` and `sensor_msgs` and is built with this repository's `w1_docs_ros2` package. When connecting to W1, also source its built workspace. See the [W1 ROS 2 interface guide](./ros2-example.md) for setup, ROS domain and discovery requirements.

Run from the repository root. Source ROS 2 Humble first. When connecting to W1, also source the workspace that matches its controller and use the controller's ROS domain. For communication across computers, allow discovery beyond localhost on both machines, for example with `ROS_LOCALHOST_ONLY=0`.

```bash
source /opt/ros/humble/setup.bash
# When connecting to W1, source its controller workspace first
# source /path/to/w1_ws/install/setup.bash

colcon --log-base examples/ros2/log build \
  --base-paths examples/ros2/src \
  --build-base examples/ros2/build \
  --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
```

## Record

Choose an output path that does not already exist, then run:

```bash
ros2 run w1_docs_ros2 record_joint_states --ros-args \
  -p output_path:=/tmp/w1-joint-states.jsonl \
  -p duration_seconds:=10.0 \
  -p timeout_seconds:=5.0
```

The node subscribes to `/joint_states` by default and records for 10 seconds. It exits on timeout if no valid message arrives within 5 seconds after startup or between valid messages. The default `output_path` is `joint_states.jsonl` in the current working directory. The file is created exclusively; an existing file is never overwritten. Choose another path or filename to retry.

## JSONL contents

The first line contains format metadata. Each following line represents one received `sensor_msgs/msg/JointState`:

| Field                            | Meaning                                                                                                   |
| -------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `record_type`, `schema_version`  | Row type and local file-format version; `metadata` for the header row and `joint_state` for feedback rows |
| `topic`, `message_type`          | Effective subscribed topic and ROS message type in the metadata row; the default topic is `/joint_states` |
| `elapsed_seconds`                | Monotonic time elapsed since recording started until this frame was received                              |
| `stamp.sec`, `stamp.nanosec`     | ROS acquisition-time field from the message publisher; it may be zero and is not replaced by receive time |
| `frame_id`                       | Coordinate-frame label from the original message                                                          |
| `name`                           | Joint-name array                                                                                          |
| `position`, `velocity`, `effort` | State arrays preserved from the ROS message; unavailable arrays remain empty (`[]`)                       |

Each array uses the corresponding index in `name`. The recorder requires nonempty, unique names; each of `position`, `velocity`, and `effort` may be empty or must match the name-array length, and numeric values must be finite. Missing state arrays remain `[]`; values are not filled with zero or changed to `null`. A message with all three state arrays empty is still preserved. Match values by joint name; do not assume feedback order equals the 26-joint command order. Metadata documents units for revolute and prismatic joints. The message does not carry joint type, so interpret values using the actual robot model. The publisher supplies `header.stamp`; it may be zero. This tool does not validate timestamp freshness or detect loss upstream or in DDS; it records only messages that reach this node.

The subscription uses ROS 2 Humble's `qos_profile_sensor_data` (`BEST_EFFORT`, `VOLATILE`, `KEEP_LAST`, depth 5) and must be QoS-compatible with the publisher. This profile does not guarantee lossless delivery, so the output should not be treated as a complete, lossless controller log.

Recorder source:

::: code-group
<<< ../../../examples/ros2/src/w1_docs_ros2/w1_docs_ros2/record_joint_states.py{python:line-numbers}
:::

## Parameters and exit codes

| Parameter          | Default              | Purpose                                                                                            |
| ------------------ | -------------------- | -------------------------------------------------------------------------------------------------- |
| `output_path`      | `joint_states.jsonl` | Output path; relative paths use the current working directory, and the file must not already exist |
| `duration_seconds` | `10.0`               | Maximum duration measured from the start of recording                                              |
| `timeout_seconds`  | `5.0`                | Maximum wait for the first frame or between valid frames                                           |

| Exit code | Meaning                                                                                  |
| --------- | ---------------------------------------------------------------------------------------- |
| `0`       | Duration elapsed and data was recorded                                                   |
| `2`       | Invalid parameter/message, or the output file already exists                             |
| `3`       | Timeout before the first frame, between frames, or no data during the recording period   |
| `4`       | Recording-queue or file I/O error, including failure to create, write, or flush the file |
| `130`     | Ctrl+C; received records are flushed to the file when possible                           |

This tool stores ROS state. It does not check controller readiness, verify feedback freshness, or establish that the robot can move safely. For joint and IMU state, motor diagnostics, and control-array formats, see the [W1 ROS 2 examples](./ros2-example.md).

## Isolated tests

The repository's isolated ROS tests use a local publisher to check the read-only state client and recorder file output. `state_reader` reads one named joint and does not depend on a control service. They do not connect to a W1 controller. Recorder coverage includes multi-frame JSONL, remapped-topic metadata, array preservation, no-data timeouts, first messages before and after the idle deadline, refusal to overwrite, invalid frames and flushing on interruption. After building the package, run from the repository root:

```bash
ROS_LOCALHOST_ONLY=1 ROS_DOMAIN_ID=169 python3 examples/ros2/test_cli.py
```

169 is a local test domain; choose an unused value if it is occupied. The test substitute checks client and file-recording behavior only; it does not simulate a W1 controller or its hardware. Before running the recorder against a real or separately launched test publisher, verify the ROS domain and discovery settings.
