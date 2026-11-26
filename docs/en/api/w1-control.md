# W1 Whole-Body Control Interface

This page applies to the current official ROS 2 control configuration, `speed_W1_v1.2`, with ROS 2 Humble. The configuration has 26 controlled joints, with six axes on each arm. Joint order, message fields, and upper-level interfaces follow the current public interface documentation.

## Verify the configuration

After sourcing the corresponding ROS 2 environment, inspect controller status and the runtime joint order:

```bash
ros2 control list_controllers -c /controller_manager
ros2 param get /mit_controller joints
```

The active controllers should include `joint_state_broadcaster` and `mit_controller`. The runtime `joints` list should match the 26-axis order below.

## Command topics

All five low-level command inputs use `std_msgs/msg/Float64MultiArray`, with a subscription depth of 10 and reliable delivery by default. Position values are absolute joint angles. The controller update rate is 500 Hz.

| Topic                                   | Message data                                 | Purpose                                                                               |
| --------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------- |
| `/rl_motion_control_command_pvt`        | 78 values: 26 q, 26 qd, 26 τff               | Whole-body position, velocity, and joint-side torque feedforward                      |
| `/rl_motion_control_command`            | 26 whole-body q values, or 12 leg q values   | The 12-value form updates only the legs. Waist and arms retain their existing targets |
| `/rl_motion_control_command_with_kp_kd` | 78 values: 26 q, 26 kp, 26 kd                | Whole-body position and per-joint gains                                               |
| `/lower_body_joint_position_command`    | 14 values: legs and waist q                  | Updates leg and waist positions                                                       |
| `/arm_joint_position_command_165`       | 12 values: 6 left-arm and 6 right-arm values | Updates both arm positions. The topic suffix is a historical name                     |

`q` is in rad, `qd` in rad/s, `τff` in N·m, `kp` in N·m/rad, and `kd` in N·m·s/rad. The three blocks are concatenated in sequence, not interleaved per joint. Ordinary position messages use the default empty `layout`. Only `/rl_motion_control_command_with_kp_kd` takes `kp` and `kd` from the message. Other position and PVT inputs use the configured gains. After a position frame is accepted, velocity and feedforward targets for the joints covered by that frame are set to zero.

## 26-axis command order

Indices are zero-based. The three blocks in PVT and gain messages use the same order. The order of feedback in `/joint_states` may differ, so match feedback by joint name.

| Index | Joint name                   |
| ----: | ---------------------------- |
|     0 | `left_hip_pitch_joint`       |
|     1 | `left_hip_roll_joint`        |
|     2 | `left_hip_yaw_joint`         |
|     3 | `left_knee_joint`            |
|     4 | `left_ankle_pitch_joint`     |
|     5 | `left_ankle_roll_joint`      |
|     6 | `right_hip_pitch_joint`      |
|     7 | `right_hip_roll_joint`       |
|     8 | `right_hip_yaw_joint`        |
|     9 | `right_knee_joint`           |
|    10 | `right_ankle_pitch_joint`    |
|    11 | `right_ankle_roll_joint`     |
|    12 | `waist_yaw_joint`            |
|    13 | `waist_pitch_joint`          |
|    14 | `left_shoulder_pitch_joint`  |
|    15 | `left_shoulder_roll_joint`   |
|    16 | `left_shoulder_yaw_joint`    |
|    17 | `left_elbow_joint`           |
|    18 | `left_wrist_yaw_joint`       |
|    19 | `left_wrist_pitch_joint`     |
|    20 | `right_shoulder_pitch_joint` |
|    21 | `right_shoulder_roll_joint`  |
|    22 | `right_shoulder_yaw_joint`   |
|    23 | `right_elbow_joint`          |
|    24 | `right_wrist_yaw_joint`      |
|    25 | `right_wrist_pitch_joint`    |

Left and right refer to the robot's own sides. Positive directions follow the corresponding joint axis in the URDF and the right-hand rule. Passive toe joints may appear in state feedback, but they are not part of these 26 control-array entries.

### PVT data layout

| Index range   | Field                             | Unit  |
| ------------- | --------------------------------- | ----- |
| `data[0:26]`  | Whole-body position q             | rad   |
| `data[26:52]` | Whole-body velocity qd            | rad/s |
| `data[52:78]` | Whole-body torque feedforward τff | N·m   |

On the real robot, the legs support torque feedforward. The waist and arms use position control, so their feedforward entries should be zero. The right knee has command index 9, so its position, velocity, and feedforward entries are `data[9]`, `data[35]`, and `data[61]`, respectively.

### Position-array coverage

`/rl_motion_control_command` accepts 26 whole-body position values or 12 leg position values. The 12-value array contains only the left and right legs, without the waist or arms.

`/lower_body_joint_position_command` uses indices 0–13 for both legs and the waist. `/arm_joint_position_command_165` contains the left arm at indices 14–19, followed by the right arm at indices 20–25.

Before publishing, check array length, finite values, joint order, and target ranges. Do not assume feedback arrays use the command order. Multiple command topics may write to the same joints, so use one active command input for a control task.

## Bilateral arm teaching interface

The W1 teaching panel receives joint targets on `/arm_move` in degrees. A single-arm target has six values. A dual-arm target has 12 values, with the left arm first. The teaching panel publishes 12 arm position targets in radians through `/arm_joint_position_command_165`.

| Topic                               | Type                             | Data format                                                                                                                                                       |
| ----------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/arm_move`                         | `std_msgs/msg/Float64MultiArray` | Six values for one arm, with `layout.dim[].label` set to `left_arm` or `right_arm`. Twelve values for both arms, with the left arm first and the `dual_arm` label |
| `/left_arm_move`, `/right_arm_move` | `std_msgs/msg/Float64MultiArray` | Legacy single-arm topics, six values per side                                                                                                                     |

The following example submits a right-arm target to a system with the teaching panel loaded:

```bash
ros2 topic info /arm_move -v
ros2 topic pub --once /arm_move std_msgs/msg/Float64MultiArray \
  "{layout: {dim: [{label: right_arm, size: 6, stride: 6}]}, data: [0.0, -7.0, 0.0, 5.0, 0.0, 0.0]}"
```

Publishing to this topic submits a motion target. Confirm that the connection is to the intended simulated or robot system and that the target matches the device configuration.

## Service availability

The default deployment provides bilateral arm teaching. The dual-arm planning service `/plan_move` and weld-program generation service `/weld_vision/capture_and_generate` are disabled by default. To inspect the services and types available on a connected system, run:

```bash
ros2 service list -t
```

For state topics, message fields, QoS, and examples, see [W1 ROS 2 Interface Examples](../sdk/ros2-example.md).
