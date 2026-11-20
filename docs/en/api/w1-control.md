# W1 whole-body control interfaces

This reference applies to `speed_W1_v1.2`: 28 controlled joints, two seven-axis arms, and ROS 2 Humble. It combines the W1 communication guide with the whole-body interface guide, using the current W1 arm PVT interpolation contract. See the [ROS 2 example](../sdk/ros2-example.md) for startup, a read-only node, and Planner, Teach and welding service calls.

The 28 joints on this page refer to that interface configuration. Its relationship to the product reference value of 27 degrees of freedom remains unconfirmed; see [Models and specifications](../product/specifications.md).

## Model and configuration

| Item                   | W1 configuration                                                          |
| ---------------------- | ------------------------------------------------------------------------- |
| Driver package         | `ethercat_motor_drive`                                                    |
| Launch file            | `motor_drive-speed_W1_v1_2.launch.py`                                     |
| Model parameter        | `robot_model` on `/mit_controller`: `speed_W1_v1.2`                       |
| Configuration          | `config/controllers-speed_W1_v1_2.yaml` under the package share directory |
| Joint count            | 28 total; 14 legs/waist; 14 arms                                          |
| Controller update rate | 500 Hz                                                                    |
| Default PVT input      | 100 Hz; interpolation applies only to arm position and velocity           |

The W1 workspace supplies configuration, drivers and trajectory resources. They are not included in this documentation repository. After sourcing that workspace's `install/setup.bash`, inspect the installed package and active parameters:

```bash
ros2 pkg prefix --share ethercat_motor_drive
ros2 param get /mit_controller robot_model
ros2 param get /mit_controller joints
ros2 control list_controllers -c /controller_manager
```

Interpolation enablement and nominal period are read during controller initialization. A 50 Hz source requires a matching 0.02 s period configuration and a controller reload; it cannot simply use the default 100 Hz configuration. Other models' 25/26-joint arrays do not apply to this 28-joint W1.

## Command topics and blocks

All five endpoints use `std_msgs/msg/Float64MultiArray`, subscription depth 10 and default reliable delivery. Positions are absolute joint angles. `+` means concatenating complete blocks, not interleaving fields per joint.

| Topic                                   | `data`                                               | Default W1 restrictions                                                                                                          |
| --------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `/rl_motion_control_command_pvt`        | 84 values: q + qd + τff                              | Whole-body streaming input; every frame needs a token after session reset                                                        |
| `/rl_motion_control_command`            | 28 whole-body q values; also accepts 12 leg q values | The 28-value form covers selected arm joints and is rejected; the 12-value form excludes waist and arms                          |
| `/rl_motion_control_command_with_kp_kd` | 84 values: q + kp + kd                               | Covers both arms; requires arm PVT interpolation to be disabled                                                                  |
| `/lower_body_joint_position_command`    | 14 values: legs + waist q                            | Separate leg/waist control; held until the first valid PVT frame of a new session                                                |
| `/arm_joint_position_command_165`       | 14 values: left arm 7 + right arm 7, q               | `_165` is a historical suffix; Teach/Planner position execution through this input requires arm PVT interpolation to be disabled |

| Block         | PVT                 | P+KP+KD       |
| ------------- | ------------------- | ------------- |
| `data[0:28]`  | q, rad              | q, rad        |
| `data[28:56]` | qd, rad/s           | kp, N·m/rad   |
| `data[56:84]` | τff, joint-side N·m | kd, N·m·s/rad |

Each block uses the 28-joint order below and must contain finite values. There is no combined 5N-value P/V/T/KP/KD input. P and P+KP+KD clear V/T for the joints they control; P/PVT use YAML KP/KD values; group position commands preserve other joints' targets. These data semantics do not bypass the default arm interpolation restrictions.

The caller handles action scaling, initial offsets, unit conversion, joint reordering and model limits. The driver handles motor direction, gear ratios and parallel-ankle conversion. Multiple topics may write the same joints, so use one active command source per replay.

## 28-joint order and Home

Indices are zero-based. All three PVT or gain blocks reuse this order. Extract `/joint_states` feedback by name; its array order need not match command order.

| Index | Joint name                   | Home (rad) |
| ----- | ---------------------------- | ---------- |
| 0     | `left_hip_pitch_joint`       | 0          |
| 1     | `left_hip_roll_joint`        | 0          |
| 2     | `left_hip_yaw_joint`         | 0          |
| 3     | `left_knee_joint`            | 0          |
| 4     | `left_ankle_pitch_joint`     | 0          |
| 5     | `left_ankle_roll_joint`      | 0          |
| 6     | `right_hip_pitch_joint`      | 0          |
| 7     | `right_hip_roll_joint`       | 0          |
| 8     | `right_hip_yaw_joint`        | 0          |
| 9     | `right_knee_joint`           | 0          |
| 10    | `right_ankle_pitch_joint`    | 0          |
| 11    | `right_ankle_roll_joint`     | 0          |
| 12    | `waist_yaw_joint`            | 0          |
| 13    | `waist_pitch_joint`          | 0          |
| 14    | `left_shoulder_pitch_joint`  | 0          |
| 15    | `left_shoulder_roll_joint`   | -1.36      |
| 16    | `left_shoulder_yaw_joint`    | 0          |
| 17    | `left_elbow_joint`           | 0          |
| 18    | `left_wrist_roll_joint`      | 0          |
| 19    | `left_wrist_yaw_joint`       | 0          |
| 20    | `left_wrist_pitch_joint`     | 0          |
| 21    | `right_shoulder_pitch_joint` | 0          |
| 22    | `right_shoulder_roll_joint`  | -1.36      |
| 23    | `right_shoulder_yaw_joint`   | 0          |
| 24    | `right_elbow_joint`          | 0          |
| 25    | `right_wrist_roll_joint`     | 0          |
| 26    | `right_wrist_yaw_joint`      | 0          |
| 27    | `right_wrist_pitch_joint`    | 0          |

Home comes from `init_state.default_joint_angle` and matches RViz Home for the same launch. With `hold_current_state_on_activate: true`, activation holds measured positions; it **does not move automatically to Home**. Transition smoothly from current feedback to the desired policy initial pose. Check the installed YAML and live `joints` parameter at the deployment site.

## PVT session token and first frame

After reset, a PVT message needs **exactly one** `layout.dim` entry. Its `label` must exactly match the token returned by reset; the W1 replayer also sets `size=84, stride=84`. Frames with old or missing tokens are ignored. Do not use the generic array-message assumption that layout may be omitted.

All three services are under `/mit_controller/` and use `std_srvs/srv/Trigger`. Requests are empty; responses contain `bool success` and `string message`.

| Service                        | Purpose                                          | Response handling                                                                                                                                                                                |
| ------------------------------ | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `get_pvt_interpolation_status` | Query state                                      | `waiting` awaits the first frame; `buffering/running/holding` are stream states; `fault_braking/fault` include a reason; `disabled/inactive/resetting` require waiting or checking configuration |
| `reset_pvt_interpolation`      | Request a new session in a resettable state      | On success, `message` is the token; poll until `success=true, message=waiting` before sending the first frame                                                                                    |
| `stop_pvt_interpolation`       | Request braking on selected interpolation joints | `success=true` only acknowledges the request; continue querying until `stopped` or `fault`                                                                                                       |

A session proceeds as follows:

1. Check controller readiness and stable feedback, call reset, and retain the returned token.
2. Wait for `waiting`, then start from the held position with zero first-frame velocity and feedforward. The default first-frame position tolerance on selected joints is 0.001 rad.
3. Publish 84 values at the default 100 Hz, carrying the same token on every frame.
4. Call stop and query the final state. This service affects only interpolation joints; whole-robot emergency stop uses the device's own mechanism.

The W1 package's `docs/examples/trajtest_w1_horizontal400.sh` implements feedback checks, transitions, token handling and stopping. See the [ROS 2 example](../sdk/ros2-example.md#pvt-commands-and-replay) for prerequisites and offline checks.

## Hardware mapping and feedback

Current W1 leg drivers map τff feedforward. Waist TI CSP and arm HSA CSP **do not send that feedforward cyclically**. A field binding in a generic control structure does not establish cyclic support in every driver. `tau_ff=0` does not mean measured motor torque is zero, and mock operation does not validate physical motor behavior.

Select controlled joints by name in `/joint_states`; ignore extra passive joints or frames containing only passive joints. The physical meaning of `effort` depends on driver mapping, so not every reported value represents measured torque. Check joint ownership, temperatures, error codes and bus health through dynamic joint state and diagnostic topics; see [state interfaces](../sdk/ros2-example.md#state-interfaces).

Readiness includes an active controller and driver handover. The W1 startup gate logs `MIT first commands accepted by all configured drive plugins` after all configured axes are taken over. Check bus OK status and per-axis ownership separately.

## Sources and scope

Sources are this repository's `tmp/W1_ROS2通讯接口示例.md` and `tmp/整机控制接口README.md`. The W1-specific guide takes precedence over generic or historical descriptions: this page uses current 100 Hz arm interpolation, session tokens and hardware feedforward mapping, rather than older 50/500 Hz replay conditions without interpolation.

The W1 installation should include YAML, replay scripts and trajectories under `docs/examples/`, and replay dependencies. Rebuild that workspace after configuration or data changes to update installed copies. Driver sources, trajectory data and calibration files not supplied with these documents are not provided here. Exact software revisions and firmware versions remain to be recorded with a release.
