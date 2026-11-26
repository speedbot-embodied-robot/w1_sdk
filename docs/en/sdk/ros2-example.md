# W1 ROS 2 Interface Examples

This page applies to the current official `speed_W1_v1.2` configuration with ROS 2 Humble. It has 26 controlled joints, with six axes on each arm. Connect from the same ROS domain as the running W1 workspace. See the [whole-body control interface](../api/w1-control.md) for command order and array lengths.

## Connect and verify

```bash
source /opt/ros/humble/setup.bash
source /path/to/w1_ws/install/setup.bash

ros2 control list_controllers -c /controller_manager
ros2 param get /mit_controller joints
ros2 topic info /joint_states -v
```

Use the same `ROS_DOMAIN_ID` as the robot. For cross-host communication, allow network discovery, for example with `ROS_LOCALHOST_ONLY=0`. Confirm that `joint_state_broadcaster` and `mit_controller` are `active` and that the runtime `joints` parameter matches the 26-axis command order. Check actual topic rates and QoS with `ros2 topic hz` and `ros2 topic info -v`.

## State topics

| Topic                                                 | Message type                          | Fields and units                                                                                                                                                                                      | Availability                                                                                              |
| ----------------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `/joint_states`                                       | `sensor_msgs/msg/JointState`          | Match `position[i]` (rad), `velocity[i]` (rad/s), and `effort[i]` (N·m) by `name[i]`; `header.stamp` is the message time                                                                              | Simulation and real robot. Extract controlled joints by name and ignore extra passive joints such as toes |
| `/imu/data`                                           | `sensor_msgs/msg/Imu`                 | `header.frame_id` is `base_link`; quaternion x/y/z/w, angular velocity (rad/s), linear acceleration (m/s²). Data is transformed to `base_link`                                                        | Real robot. The default simulation does not provide this hardware stream                                  |
| `/motor_temperature_broadcaster/dynamic_joint_states` | `control_msgs/msg/DynamicJointState`  | Find values by joint and interface names in `joint_names`, `interface_names`, and `values`. Includes initialization, controller ownership, status word, error code, and configured temperature fields | Real-robot hardware publisher, 10 Hz in the documented configuration                                      |
| `/diagnostics`                                        | `diagnostic_msgs/msg/DiagnosticArray` | Read `status[]` fields `name`, `level`, `message`, and `values` for aggregate and bus warnings                                                                                                        | Systems with hardware monitoring enabled                                                                  |
| `/fss_imu/temperature`                                | `std_msgs/msg/Float64`                | `data` is a scalar temperature; no Header is included                                                                                                                                                 | Real-robot IMU temperature stream                                                                         |

The velocity and effort arrays in `JointState` can be empty. Do not replace missing values with zero. The meaning of `effort` depends on drive mapping. For `DynamicJointState`, locate a joint and interface by name instead of assuming fixed array order. A diagnostic `level=0` alone does not mean the system is ready. A monitor may still report `starting`.

`/joint_states_for_tf` is a separate visualization stream. Read `/joint_states` for control and data collection.

```bash
# Simulation or real robot
ros2 topic echo /joint_states --once --qos-reliability best_effort
ros2 topic info /joint_states -v

# Real robot with hardware publishers and monitor nodes running
ros2 topic echo /imu/data --once --qos-reliability best_effort
ros2 topic echo /motor_temperature_broadcaster/dynamic_joint_states --once --qos-reliability best_effort
ros2 topic echo /diagnostics --once
ros2 topic echo /fss_imu/temperature --once
```

## Python: read joint and IMU state

This read-only example independently subscribes to the joint-state and IMU topics, reads the right elbow by name, and prints one valid IMU message. The topics are not synchronized. Save as `read_w1_state.py` and run after sourcing ROS:

<<< ../../../examples/ros2/snippets/read_w1_state.py{python:line-numbers}

The default simulation does not publish hardware `/imu/data`. To test parsing only, publish a test message in the same ROS domain:

```bash
ros2 topic pub -r 5 /imu/data sensor_msgs/msg/Imu \
  "{header: {frame_id: base_link}, orientation: {w: 1.0}, angular_velocity: {z: 0.125}, linear_acceleration: {z: 9.81}}"
```

This synthetic stream is only for validating message parsing.

## C++: read joint and IMU samples

This example subscribes to both topics using sensor QoS, then exits after receiving a right-elbow position and a `base_link` IMU message. Save it as `src/w1_state_reader.cpp` in an ament C++ package.

<<< ../../../examples/ros2/snippets/read_w1_state.cpp{cpp:line-numbers}

Declare dependencies on `ament_cmake`, `rclcpp`, and `sensor_msgs` in `package.xml` and `CMakeLists.txt`. Add the target and build it with the package:

```cmake
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(w1_state_reader src/w1_state_reader.cpp)
ament_target_dependencies(w1_state_reader rclcpp sensor_msgs)
install(TARGETS w1_state_reader DESTINATION lib/${PROJECT_NAME})
ament_package()
```

Then run `colcon build --packages-select <your_package>`, source `install/setup.bash`, and launch `ros2 run <your_package> w1_state_reader`. The topics are independent message streams, so the samples are not synchronized.

## Control topics and array layout

See the [whole-body control interface](../api/w1-control.md) for all five command inputs and the 26-axis order:

| Topic                                   | Type                             |   Length | Data                           |
| --------------------------------------- | -------------------------------- | -------: | ------------------------------ |
| `/rl_motion_control_command_pvt`        | `std_msgs/msg/Float64MultiArray` |       78 | q[26] + qd[26] + τff[26]       |
| `/rl_motion_control_command`            | `std_msgs/msg/Float64MultiArray` | 26 or 12 | Whole-body q, or legs only     |
| `/rl_motion_control_command_with_kp_kd` | `std_msgs/msg/Float64MultiArray` |       78 | q[26] + kp[26] + kd[26]        |
| `/lower_body_joint_position_command`    | `std_msgs/msg/Float64MultiArray` |       14 | Leg and waist q                |
| `/arm_joint_position_command_165`       | `std_msgs/msg/Float64MultiArray` |       12 | Left-arm q[6] + right-arm q[6] |

The following example only assembles a PVT message object. It does not publish a motion command:

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

Positions are absolute. Before publishing, check the target, order, units, and limits against state feedback and the robot model. Ensure the controller and actuators have completed handover.

## Single-arm and bilateral teaching

The default deployment provides bilateral teaching. `/arm_move` receives targets in degrees, with six values for one arm or 12 for both arms, left arm first. The example submits a right-arm target to a system with the teaching panel loaded:

```bash
ros2 topic info /arm_move -v
ros2 topic pub --once /arm_move std_msgs/msg/Float64MultiArray \
  "{layout: {dim: [{label: right_arm, size: 6, stride: 6}]}, data: [0.0, -7.0, 0.0, 5.0, 0.0, 0.0]}"
```

Publishing this topic submits a motion target. Legacy single-arm topics `/left_arm_move` and `/right_arm_move` take six values per side. The dual-arm planning service `/plan_move` and weld-trajectory generation service `/weld_vision/capture_and_generate` are disabled in the default deployment. Use `ros2 service list -t` to inspect service names and types on a connected system.
