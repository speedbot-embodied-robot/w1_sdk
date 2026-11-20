# W1 ROS 2 feedback and PVT status example

The `w1_docs_ros2` package reads a named joint from `/joint_states`
(`sensor_msgs/msg/JointState`), then queries
`/mit_controller/get_pvt_interpolation_status` (`std_srvs/srv/Trigger`).
The defaults match the supplied `speed_W1_v1.2` interface documentation.
It sends no motion, reset or stop command and does not require `speedbot_msgs`.

From the repository root, with ROS 2 Humble installed:

```bash
source /opt/ros/humble/setup.bash
colcon --log-base examples/ros2/log build --base-paths examples/ros2/src \
  --build-base examples/ros2/build --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
ros2 run w1_docs_ros2 state_reader
```

Run the reader in the same ROS domain as an already started W1 controller or
W1 mock. The package does not install that controller, its launch files,
configuration or custom planning/welding services. The full
[Chinese guide](../../docs/zh/sdk/ros2-example.md) and
[English guide](../../docs/en/sdk/ros2-example.md) explain W1 startup and discovery.

Parameters: `joint_name` defaults to `right_elbow_joint`, `timeout_seconds` to
`5.0` for feedback, and `service_timeout_seconds` to `5.0` for discovery and then
another `5.0` for the response. Deadlines use the monotonic clock, including
when ROS simulated time is paused. Valid unrelated or position-less messages
are ignored without renewing the deadline. Invalid array lengths, duplicate
names and non-finite values cause an error. The reader prints one JSON record
with `joint_name`, `position_rad`, `stamp`, `frame_id`, and
`pvt: {success, message}`. It preserves the returned PVT state, including states
other than `waiting`. A completed request with `success=false` prints its response
and exits with code 4; it does not mean transport failed. On a nonzero exit,
`ros2 run` may append its own process-exit notice after the node output.

Exit codes: 0 success; 2 invalid parameters/message; 3 feedback, discovery or
response timeout; 4 service call failure or `success=false`; 130 interruption.
The feedback timestamp is reported, not checked against a motion-control
freshness threshold. This single snapshot is not a controller readiness gate.

Remap both absolute endpoint names when using a robot namespace:

```bash
ros2 run w1_docs_ros2 state_reader --ros-args \
  -r /joint_states:=/robot_1/joint_states \
  -r /mit_controller/get_pvt_interpolation_status:=/robot_1/mit_controller/get_pvt_interpolation_status \
  -p joint_name:=right_elbow_joint -p timeout_seconds:=5.0 \
  -p service_timeout_seconds:=5.0
```

To test only the client, from the repository root after sourcing its overlay:

```bash
colcon --log-base examples/ros2/log test --build-base examples/ros2/build \
  --install-base examples/ros2/install --packages-select w1_docs_ros2 \
  --python-testing pytest
colcon test-result --test-result-base examples/ros2/build --verbose
ROS_LOCALHOST_ONLY=1 ROS_DOMAIN_ID=169 python3 examples/ros2/test_cli.py
```

Choose an unused local domain if 169 is occupied. The CLI tests create synthetic
feedback and Trigger responses under unique `/w1_docs_test_...` endpoints and
remap the reader to them. These tests do not run W1 mock, contact a controller,
or verify hardware behavior. The former standalone `fixture_publisher` teaching
entry point has been removed; test fixtures live only in `test_cli.py`.
