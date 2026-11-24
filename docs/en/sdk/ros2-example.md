# ROS 2: W1 communication interfaces and examples

This page applies to `speed_W1_v1.2` (28 joints and two seven-axis arms) with ROS 2 Humble. It uses the actual W1 `/joint_states` topic and PVT status service: read feedback in the W1 mock first, then request a right-arm plan with `execute: false`. All names use the default namespace. See [W1 whole-body control](../api/w1-control.md) for full joint ordering and control constraints.

## Environment and dependencies

Use Ubuntu 22.04, Python 3.10 and ROS 2 Humble. This repository provides the read-only `w1_docs_ros2` package, depending on `rclpy`, `sensor_msgs` and `std_srvs`, built with `ament_python` / `colcon`. Use the system Python matching your Humble installation. Building and testing additionally require colcon and pytest.

A separately built W1 workspace provides the driver and mock. This repository does not contain `ethercat_motor_drive`, its W1 launch file or YAML. Planner, TeachPanel and welding examples also require that workspace's `speedbot_msgs` and the corresponding service providers. The read-only node itself does not depend on `speedbot_msgs`. Without the W1 workspace, you can run the isolated communication tests at the end of this page, but cannot start the W1 mock.

## Startup and discovery

In both terminals, source Humble and the **W1 workspace** installation, replacing the path below with your actual location. Domain 83 is the example's local test domain; choose an unused one. For cross-machine integration, use the controller's domain on both machines, set `ROS_LOCALHOST_ONLY=0`, and ensure the network supports DDS discovery.

```bash
source /opt/ros/humble/setup.bash
source /path/to/w1_ws/install/setup.bash
export ROS_DOMAIN_ID=83
export ROS_LOCALHOST_ONLY=1
```

Terminal 1 starts the W1 mock, RViz and Planner. Omit `moveit:=true` if only checking low-level state. Start the vision node separately.

```bash
ros2 launch ethercat_motor_drive motor_drive-speed_W1_v1_2.launch.py bSim:=true moveit:=true
```

In terminal 2, inspect the model, active controller, feedback, PVT subscriber and planning service:

```bash
ros2 param get /mit_controller robot_model
ros2 control list_controllers -c /controller_manager
ros2 topic echo /joint_states --once --qos-reliability best_effort
ros2 topic info /rl_motion_control_command_pvt -v
ros2 service type /plan_move
ros2 service call /mit_controller/get_pvt_interpolation_status std_srvs/srv/Trigger '{}'
```

The expected model is `speed_W1_v1.2`, with `mit_controller` active and planning service type `speedbot_msgs/srv/PlanMove`. With default interpolation ready and before the first frame, the PVT query returns `success=true, message=waiting`. Hardware integration also requires driver handover and fresh feedback. The W1 startup gate logs `MIT first commands accepted by all configured drive plugins` after all configured axes are taken over.

## State interfaces

The direction below is from the external application's perspective: subscribe to receive.

| Topic                                                 | Message type                          | Fields and units                                                                                                                                                        | Availability                                                                                               |
| ----------------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `/joint_states`                                       | `sensor_msgs/msg/JointState`          | Match `name[i]` to `position[i]` (rad), `velocity[i]` (rad/s), and `effort[i]` (N·m, interpretation depends on driver mapping); `header.stamp` is the message timestamp | Mock and hardware; select controlled joints by name and ignore extra passive joints or passive-only frames |
| `/imu/data`                                           | `sensor_msgs/msg/Imu`                 | `header.frame_id` is `base_link` in the W1 v1.2 configuration; `orientation` quaternion x/y/z/w, `angular_velocity` (rad/s), `linear_acceleration` (m/s²)               | W1 hardware FSS IMU broadcaster; default mock does not provide this hardware stream                        |
| `/motor_temperature_broadcaster/dynamic_joint_states` | `control_msgs/msg/DynamicJointState`  | Read by joint and interface name; common interfaces include `status_word`, `error_code`, `motor_temperature` (°C), `drive_temperature` (°C), and `bus_voltage` (V)      | W1 hardware state broadcaster, configured at 10 Hz; fields vary by drive support                           |
| `/diagnostics`                                        | `diagnostic_msgs/msg/DiagnosticArray` | Standard `status[]` summary: `name`, `level`, `message`, `hardware_id`, and key-value `values[]`                                                                        | W1 hardware with hardware status monitoring started; default mock does not provide hardware diagnostics    |

Joint and IMU readers can use sensor-data QoS. Inspect actual publication rate, QoS and hardware stream availability on the running system:

```bash
ros2 topic info /joint_states -v
ros2 topic hz /joint_states
ros2 topic echo /imu/data --once --qos-reliability best_effort
```

### Read-only IMU and motor diagnostics

In a terminal with the W1 workspace sourced, inspect the topics and message types before reading one sample:

```bash
ros2 topic list -t
ros2 topic type /imu/data
ros2 topic info /imu/data -v
ros2 topic echo /imu/data --once --qos-reliability best_effort
ros2 topic echo /motor_temperature_broadcaster/dynamic_joint_states --once
ros2 topic echo /diagnostics --once
```

In `DynamicJointState`, `joint_names[i]` maps to `interface_values[i]`. Inside that entry, `interface_names[j]` maps to `values[j]`. Look up names rather than assuming a fixed array order. `status_word` and `error_code` are raw drive status values; their meanings depend on the drive model and its public definitions. Not every drive exposes every temperature or voltage interface.

Use `/diagnostics` for aggregate status. To identify an individual joint, combine it with that joint's entry in `dynamic_joint_states`. The IMU covariance fields are present, but the current publisher does not provide calibrated covariance; consumers should not treat zero-filled values as calibrated uncertainty.

### JointState and QoS

Standard `JointState` permits empty `position`, `velocity` and `effort` arrays; each populated array must match `name` length. This reader additionally requires nonempty, unique names, at least one populated state array, and finite values. It extracts `right_elbow_joint` by name from valid messages, ignoring frames without that joint or without position data. Feedback order need not match the 28-joint command order. Keep unknown effort absent rather than representing it as a measured zero.

The subscription uses Humble's `qos_profile_sensor_data`: `BEST_EFFORT`, `VOLATILE`, `KEEP_LAST`, depth 5. It accepts compatible best-effort or reliable publishers; a subscriber requiring reliable delivery cannot match a best-effort publisher. The client uses default ROS service QoS. Remapping changes endpoint names, not message types or units.

See the official ROS [JointState definition](https://github.com/ros2/common_interfaces/blob/humble/sensor_msgs/msg/JointState.msg) and [Humble QoS profiles](https://github.com/ros2/rmw/blob/humble/rmw/include/rmw/qos_profiles.h) for the standard contracts.

`header.stamp` represents the state-recording time by message semantics and comes from the publisher; it may be zero. This example limits waiting with a monotonic clock, but does not reject stale timestamps. A paused simulation `/clock` cannot leave it waiting indefinitely. The node demonstrates interface reads; it does not establish feedback freshness for motion or provide real-time control guarantees.

### Record continuous joint feedback

To save multiple `/joint_states` frames for offline analysis, use the [Python JSONL recording example](./python-example.md). The recorder preserves each message's name order, state arrays, `header.stamp`, and `frame_id`, and adds local monotonic elapsed time. Empty state arrays remain `[]`. It only subscribes and writes a file; it publishes no control command. Its purpose differs from `state_reader`: that node reads one named joint and queries PVT status, while the recorder saves complete feedback frames without querying PVT.

## Read-only node: joint feedback and PVT status

Build from **this repository's root**, retaining terminal 2's W1 environment and domain settings:

```bash
colcon --log-base examples/ros2/log build \
  --base-paths examples/ros2/src \
  --build-base examples/ros2/build \
  --install-base examples/ros2/install \
  --packages-select w1_docs_ros2
source examples/ros2/install/local_setup.bash
ros2 run w1_docs_ros2 state_reader
```

The node reads the right elbow position, asynchronously calls `/mit_controller/get_pvt_interpolation_status` (`std_srvs/srv/Trigger`), and prints one JSON object. Fields include `joint_name`, `position_rad`, `stamp`, `frame_id` and `pvt: {success, message}`. Values come from this run's feedback and response. Other valid PVT states are preserved; do not assume `waiting` is the result of every run.

A response with `success=false` still produces response JSON before exiting with code 4. A timeout without a response produces no such JSON. When using `ros2 run`, a nonzero exit may append `[ros2run]: Process exited with failure N` to stdout; automated consumers should identify JSON lines. Exit 0 means the read and query succeeded, not that the robot is ready to move.

| Parameter                 | Default             | Meaning                                                   |
| ------------------------- | ------------------- | --------------------------------------------------------- |
| `joint_name`              | `right_elbow_joint` | Joint to read                                             |
| `timeout_seconds`         | `5.0`               | Maximum wait for a valid target joint position            |
| `service_timeout_seconds` | `5.0`               | Separate maximum waits for service discovery and response |

By default each of the three stages can wait up to 5 seconds, for a total waiting budget of 15 seconds. Write floating-point ROS parameters as `5.0`, not an integer. Parameters are read at startup.

```bash
ros2 run w1_docs_ros2 state_reader --ros-args \
  -p joint_name:=right_elbow_joint \
  -p timeout_seconds:=5.0 -p service_timeout_seconds:=5.0
```

For a namespaced deployment, remap both **absolute endpoints**. `/robot` below is an example deployment namespace:

```bash
ros2 run w1_docs_ros2 state_reader --ros-args \
  -r /joint_states:=/robot/joint_states \
  -r /mit_controller/get_pvt_interpolation_status:=/robot/mit_controller/get_pvt_interpolation_status
```

| Exit code | Meaning                                                                        |
| --------- | ------------------------------------------------------------------------------ |
| 0         | Joint position read successfully and status service returned `success=true`    |
| 2         | Invalid message or parameter type/range                                        |
| 3         | Feedback, service discovery or service response timed out                      |
| 4         | Service call failed or returned `success=false`; inspect its status and reason |
| 130       | Ctrl+C or context shutdown                                                     |

### Complete source

The node only subscribes to state and queries a service. It does not call reset/stop or publish motion commands. A `SingleThreadedExecutor` drives callbacks and the asynchronous service. Waiting occurs outside callbacks, avoiding a callback blocking its own executor from handling the response. Completion releases the executor, node and context.

::: code-group
<<< ../../../examples/ros2/src/w1_docs_ros2/w1_docs_ros2/state_reader.py{python:line-numbers}
:::

The same source file is built and displayed on this page. Package manifest and installation entry points:

::: code-group
<<< ../../../examples/ros2/src/w1_docs_ros2/package.xml{xml:line-numbers} [package.xml]
<<< ../../../examples/ros2/src/w1_docs_ros2/setup.py{python:line-numbers} [setup.py]
<<< ../../../examples/ros2/src/w1_docs_ros2/setup.cfg{ini:line-numbers} [setup.cfg]
:::

## PVT commands and replay

The default W1 controller runs at 500 Hz, with arm P/V interpolation expecting 100 Hz input. `/rl_motion_control_command_pvt` uses `std_msgs/msg/Float64MultiArray` with 84 values: **28 q + 28 qd + 28 τff**, in rad, rad/s and N·m. After session reset, `layout.dim` must contain exactly one entry whose `label` matches the returned reset token exactly. The replayer also sets `size=84, stride=84`.

Start with reset → query until `success=true, waiting` → send the first frame from the held position with zero velocity and feedforward → continue publishing with the same token. Default first-frame position tolerance on selected joints is 0.001 rad. A 50 Hz source needs a matching 0.02 s configuration and controller reload. Stop success only acknowledges the request; query until `stopped` or `fault`. Stopping affects only interpolation joints.

See [W1 whole-body control](../api/w1-control.md) for all five command inputs, joint order, three session services and hardware mapping. Default arm interpolation restricts whole-body P, P+KP+KD and arm position inputs; examples for configurations without interpolation cannot be applied directly.

The W1 installation's horizontal400 replayer handles feedback checks, initial-pose transition, session tokens and stopping. Start with the offline check:

```bash
controller_share=$(ros2 pkg prefix --share ethercat_motor_drive)
bash "$controller_share/docs/examples/trajtest_w1_horizontal400.sh" --check-only
```

The source document reports an offline summary of `6800 frames, 28 controlled joints, 100 Hz`. The next command actually publishes about 68 seconds of trajectory plus transitions and holds. For this example, run it only against the W1 mock started above in the same isolated domain:

```bash
bash "$controller_share/docs/examples/trajtest_w1_horizontal400.sh"
```

Default replay feedforward is zero; inspect online PVT status and feedback as well. The script, trajectory and dependencies come from the `ethercat_motor_drive` installation and are not included in this repository.

## Arm planning and teaching

| Interface                           | Transport and type                                                                                                     | Parameters, units and results                                                                                                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/plan_move`                        | Planner service, `speedbot_msgs/srv/PlanMove`                                                                          | One arm per request, 7 target angles in **rad**; starts from current feedback; `execute=false` only plans                                                                      |
| `/plan_move/stop`                   | Planner service, `std_srvs/srv/Trigger`                                                                                | Empty request; stops Planner trajectory publication                                                                                                                            |
| `/arm_move`                         | TeachPanel topic, `std_msgs/msg/Float64MultiArray`                                                                     | One arm: 7 **degree** values, `layout.dim[].label` is `left_arm`/`right_arm`; dual-arm MOVE_J: 14 degree values, left first; no completion response on the topic after queuing |
| `/left_arm_move`, `/right_arm_move` | Planner **services** use `speedbot_msgs/srv/ArmMoveJointState`; Teach **topics** with the same names are legacy inputs | Planner services plan from feedback and request execution; for new integrations use `/plan_move` for planning only and `/arm_move` to queue a teaching task                    |

### Plan the right arm without execution

| Direction | Fields                                     | Meaning                                                                                           |
| --------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Request   | `id`, `arm_name`, `planner_id`             | String identifier, `left_arm/right_arm` group, planner identifier                                 |
| Request   | `goal_joint_state.data`, `execute`         | 7 rad values in the selected MoveIt arm group's order; whether to enter execution                 |
| Response  | `success`, `message`                       | Interpret with the request's `execute`; target, current state or scene may cause planning failure |
| Response  | `trajectory`, `scene_version`, `replanned` | `JointTrajectory` with `joint_names` and `points`, plus scene version and replanning flag         |

The earlier `moveit:=true` launch starts this service. The following call only plans. Check joint names and trajectory points on success, or `message` on failure:

```bash
ros2 service call /plan_move speedbot_msgs/srv/PlanMove \
  "{id: w1_demo, arm_name: right_arm, planner_id: RRTConnectkConfigDefault, goal_joint_state: {data: [0.0, -1.36, 0.0, 0.1, 0.0, 0.0, 0.0]}, execute: false}"
```

### Queue a right-arm MOVE_J in Teach

This call submits a motion task. Use a mock with the seven-axis TeachPanel loaded and restarted with **arm PVT interpolation disabled**. The earlier default configuration supports the planning-only example above. Teach targets use degrees; Planner and low-level control use rad.

```bash
ros2 topic pub --once /arm_move std_msgs/msg/Float64MultiArray \
  "{layout: {dim: [{label: right_arm, size: 7, stride: 7}]}, data: [0.0, -78.0, 0.0, 5.0, 0.0, 0.0, 0.0]}"
```

## Welding application services

The external application calls Capture. After capturing and recognizing a seam, the vision node calls the W1 TeachPanel Build service for preflight, saving and optional queuing.

| Interface                                 | Type and provider                                                          | Prerequisites                                                                                                                  |
| ----------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `/weld_vision/capture_and_generate`       | `speedbot_msgs/srv/CaptureWeldProgram`, W1 vision node                     | Camera, measured W1 hand-eye calibration, stationary robot during capture, fresh feedback and `waist_yaw ← right_wrist_yaw` TF |
| `/teach_mode_panel/build_weld_program_w1` | `speedbot_msgs/srv/BuildWeldProgramW1`, W1 TeachPanel with welding enabled | Valid TCP; capture pose is 7 right-arm rad values; input geometry is in `waist_yaw`, with points and offsets in m              |

| Capture field                 | Type/unit    | Meaning                                                                                                                              |
| ----------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Request `auto_execute`        | bool         | false: generate and save; true: save and queue for execution                                                                         |
| Response `success`, `message` | bool, string | Capture, recognition and generation result; automatic execution success covers queuing, not completed welding                        |
| Response `program_path`       | string       | Absolute program path on the server filesystem on success; empty on failure                                                          |
| Response `weld_length`        | float64, mm  | Seam length selected for the final plan; 0 on failure. Build's `executed_lengths` uses m and describes lengths selected for planning |

Replace the calibration path with this W1's measured file. Start the vision node, then call Capture from another terminal with the same environment. `auto_execute: false` captures an image and writes a program file for inspection. A pure mock can check endpoint discovery; complete generation requires the camera, calibration and panel.

```bash
ros2 run weld_seam_vision weld_seam_vision_w1_node --ros-args \
  -p calibration_info:=/path/to/measured_w1_calibration.yml
# In another terminal
ros2 service type /teach_mode_panel/build_weld_program_w1
ros2 service call /weld_vision/capture_and_generate speedbot_msgs/srv/CaptureWeldProgram \
  '{auto_execute: false}'
```

## Verification and troubleshooting

The isolated communication tests on this page use separate ROS endpoints to check `state_reader` and the joint feedback recorder. They do not start the W1 mock or simulate a controller or hardware. See the [Python recording example](./python-example.md) for recorder parameters, JSONL format and file behavior.

Testing this repository's read-only client does not require W1 drivers. With Humble sourced, build and source `w1_docs_ros2` as above, then run from the repository root:

```bash
colcon --log-base examples/ros2/log test \
  --build-base examples/ros2/build --install-base examples/ros2/install \
  --packages-select w1_docs_ros2 --python-testing pytest
colcon test-result --test-result-base examples/ros2/build --verbose
ROS_LOCALHOST_ONLY=1 ROS_DOMAIN_ID=169 python3 examples/ros2/test_cli.py
```

169 should be an unused local test domain. CLI tests use remapped, separate endpoints with a state publisher and a Trigger service substitute. They cover client reads, filtering, validation, timeouts and service failure handling. They do not start the W1 controller or establish acceptance of hardware, planning or welding services.

| Symptom                                                                               | Check                                                                                                                                             |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Missing `ethercat_motor_drive` or `speedbot_msgs`                                     | Obtain and source the corresponding W1 workspace; this documentation repository builds only the reader                                            |
| Topics or services are not visible                                                    | Installation overlay, domain, localhost, RMW and DDS discovery; inspect providers separately with `ros2 topic list -t` and `ros2 service list -t` |
| Feedback timeout                                                                      | `JointState` type, QoS, target name and position array; passive-only frames leave the reader waiting                                              |
| PVT service discovery/response timeout                                                | Controller startup, service name and remap, blocked server execution; identify the timed-out stage                                                |
| PVT subscriber is visible but still waiting                                           | Controller readiness, token, 84-value ordering and first-frame position; if faulted, inspect the reason and wait for braking to finish            |
| Planning succeeds but arms do not respond to execution                                | Distinguish planning, queuing and execution; check arm PVT ownership, position-input conditions and degrees versus rad                            |
| Humble `ros2 interface show speedbot_msgs/srv/PlanMove` reports `InvalidResourceName` | The source records a CLI expansion issue with the current installation layout; inspect Python fields and the online service type below            |

```bash
python3 -c 'from speedbot_msgs.srv import PlanMove; print(PlanMove.Request.get_fields_and_field_types())'
ros2 service type /plan_move
```

## Sources and verification scope

The W1-specific contract takes precedence. Their 2026-11-20 verification record reports right-elbow feedback of 0.0000 rad and PVT `waiting` in a headless W1 mock, a successful planning-only request with 183 trajectory points, an offline 100 Hz replay check, and Teach/Capture message-field checks. **These are source records, not results rerun during this documentation integration.** The trajectory point count is not fixed. The source did not validate physical motion, camera capture or welding execution.

This repository's tests cover the client and documentation build. Full W1 integration requires the corresponding delivered workspace. Record exact software versions, firmware combinations and deployment validation in [SDK integration](./integration.md).
