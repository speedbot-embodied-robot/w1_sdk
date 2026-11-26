# W1 ROS 2 joint-state examples

The `w1_docs_ros2` package reads a named joint from `/joint_states`
(`sensor_msgs/msg/JointState`) and records received feedback as JSONL. These
examples only read robot state and do not send motion commands.

The documented W1 interface is the current official `speed_W1_v1.2`
configuration with 26 controlled joints and six axes on each arm. From the
repository root, with ROS 2 Humble installed:

```bash
source /opt/ros/humble/setup.bash
colcon --log-base examples/ros2/log build --base-paths examples/ros2/src \
  --build-base examples/ros2/build --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
ros2 run w1_docs_ros2 state_reader
```

Run the reader in the same ROS domain as an already-started W1 controller or
another `/joint_states` publisher. The package does not install the W1
controller, its launch files, or configuration. See the [Chinese guide](../../docs/zh/sdk/ros2-example.md)
and [English guide](../../docs/en/sdk/ros2-example.md) for the state and control interfaces.

The `state_reader` parameters are `joint_name` (default `right_elbow_joint`)
and `timeout_seconds` (default `5.0`). It selects the joint by name, reports
its position and message timestamp, and exits after one valid sample. Invalid
array lengths, duplicate names and non-finite values produce an error. Exit
codes are 0 for success, 2 for invalid parameters or messages, 3 for timeout,
and 130 for interruption.

To record continuous feedback, select an output path that does not already
exist and run:

```bash
ros2 run w1_docs_ros2 record_joint_states --ros-args \
  -p output_path:=joint_states.jsonl \
  -p duration_seconds:=10.0 \
  -p timeout_seconds:=5.0
```

The recorder preserves the received `JointState` names, arrays, timestamp, and
frame ID. It sends no motion command.

To test the client and recorder against local isolated publishers, build and
source the overlay first, then run:

```bash
ROS_LOCALHOST_ONLY=1 ROS_DOMAIN_ID=169 python3 examples/ros2/test_cli.py
```

Choose an unused local domain if 169 is occupied. Tests use synthetic state
messages and do not connect to W1 or emulate its controller or hardware.
