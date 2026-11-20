# Models and specifications

This page lists W1 reference parameters and the ROS 2 configuration documented in this manual. Official specifications, measurement methods and operating conditions remain to be confirmed.

## Identify a model

| Identifier                     | Available information                                                | Still needed                                                                                           |
| ------------------------------ | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Product name                   | Speedbot W1, also written Weldroid-W1                                | Official model designation, naming rules, and corresponding hardware revision                          |
| Physical identification        | No nameplate or annotated component diagram in the supplied material | Nameplate location, model/revision lookup method, and differences between configurations               |
| ROS 2 configuration identifier | This manual's interface documentation uses `speed_W1_v1.2`           | Mapping from this software model to the public product model, specific hardware, and firmware versions |

For software configuration and discovery commands, see [W1 whole-body control](../api/w1-control.md).

## Reference body parameters

These reference values have not been mapped to a hardware revision and are not verified specifications for `speed_W1_v1.2`.

| Parameter                     | Reference value            | Unit | Conditions and notes                                                                                     |
| ----------------------------- | -------------------------- | ---- | -------------------------------------------------------------------------------------------------------- |
| Robot form                    | Full-size bipedal humanoid | —    | Intended for complex welding workstations such as shipbuilding                                           |
| Height                        | Approximately 1.7          | m    | Measurement posture and definition are not given                                                         |
| Whole-body degrees of freedom | 27                         | —    | Joint distribution is not given; this differs from the software configuration below                      |
| Single-arm payload            | 10                         | kg   | Posture, reach, duration, and whether this is a rated or limiting value are not given                    |
| Whole-robot payload           | 30                         | kg   | Payload definition and test conditions are not given; do not infer combined arm payload from this figure |

Official specifications and operating conditions still require confirmation by the product owner.

## 27 degrees of freedom and 28 controlled joints

| Scope                                       | Count                                           | Meaning for developers                                                                                     |
| ------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Product reference parameters                | 27 whole-body degrees of freedom                | A per-joint breakdown and hardware-version mapping remain to be confirmed                                  |
| `speed_W1_v1.2` ROS 2 control configuration | 28 controlled joints: 14 legs/waist and 14 arms | This configuration determines command ordering and array lengths; its whole-body PVT message has 84 values |

The relationship between these counts or versions is **pending confirmation**; the current material does not explain the difference. For integration, check the running `robot_model` and `joints` parameters and the installed configuration. Do not change command lengths using the reference degree-of-freedom count. The complete 28-joint order and PVT format are in [W1 whole-body control](../api/w1-control.md).

## Parameters and conditions still needed

| Category                       | Missing from the supplied material                                                                            |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| Welding accuracy and quality   | Welding accuracy, repeatability, weld-quality metrics, and test methods                                       |
| Welding process and throughput | Welding speed, supported process range, continuous-operation capability, and conditions                       |
| Mobility                       | Walking speed, maximum obstacle height, climbing capability, and test conditions                              |
| Power and endurance            | Battery specifications, runtime, charging time, and test load                                                 |
| Operating environment          | Ingress protection, operating temperature/humidity, explosion-protection rating, and applicable conditions    |
| Sensing                        | Sensor models, measurement ranges, resolution, and calibration requirements                                   |
| Motion limits                  | Hardware-specific joint position/velocity/torque limits, workspace, and posture-dependent payload constraints |

These fields remain pending; values cannot be derived from capability descriptions. For application scenarios, working postures, and perception, see [Capabilities and applications](./capabilities.md). Missing physical-location and connection information is listed in [Components and interfaces](./interfaces.md).
