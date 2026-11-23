# Components and interfaces

This page describes the W1 sensing configuration and links the documented software interfaces. Annotated component drawings, mounting locations and wiring specifications remain to be supplied.

## Sensing components

Lidar, ToF cameras and a 3D line-scan camera form the environment and workpiece sensing configuration. Each component's specific role and relationship to welding services remain to be documented. The quantities below are reference values to confirm against the delivered configuration.

| Component           | Reference quantity | Model and performance                                          | Location and connection information                                                      |
| ------------------- | ------------------ | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Lidar               | 1                  | Model, measurement range, and resolution pending               | Mounting location, interface specifications, and cables pending                          |
| ToF cameras         | 3                  | Each camera's model, measurement range, and resolution pending | Individual identifiers, mounting locations, interface specifications, and cables pending |
| 3D line-scan camera | 1                  | Model, measurement range, and resolution pending               | Mounting location, interface specifications, and cables pending                          |

This configuration has not been mapped to a specific hardware revision. Sensor categories do not establish USB, Ethernet, or other physical interfaces, supply requirements, or SDK availability. Confirm quantities and models against the delivered configuration. For capability context, see [Capabilities and applications](./capabilities.md).

## Documented software interfaces

The following interfaces apply to the documented `speed_W1_v1.2` ROS 2 configuration. Software endpoints do not replace physical port identifiers or wiring diagrams, and their relationship to individual sensing components must be checked separately.

| Purpose                             | Documented endpoint                                     | Conditions and further details                                                                                                                                                                                                                                |
| ----------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Joint feedback                      | `/joint_states`                                         | Read by joint name; message details and the read-only client are in the [ROS 2 example](../sdk/ros2-example.md#state-interfaces)                                                                                                                              |
| IMU and hardware status             | `/imu/data`, dynamic joint state, and diagnostic topics | Provided by the relevant hardware broadcaster or monitoring node; the default mock does not produce hardware IMU data. See the [ROS 2 example](../sdk/ros2-example.md#state-interfaces)                                                                       |
| Weld capture and program generation | `/weld_vision/capture_and_generate`                     | Requires a camera, measured W1 hand–eye calibration, valid feedback, and TeachPanel. The material does not bind this service to a specific camera in the table above. See [Welding application services](../sdk/ros2-example.md#welding-application-services) |
| Whole-body and arm control          | PVT and grouped joint commands                          | Joint ordering, units, sessions, and configuration restrictions are in [W1 whole-body control](../api/w1-control.md)                                                                                                                                          |

## Component and physical-interface information still needed

| Material                               | Required content                                                                                                                      |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Annotated robot and component diagrams | Model/hardware revision, orientation, callout numbers, official component names, images cleared for publication, and alternative text |
| Nameplate and revision identification  | Nameplate location, model/revision lookup method, and mapping to the software model                                                   |
| External connectors                    | Interface names, locations/markings, connector models, pin assignments, electrical and communication specifications                   |
| Accessories and cables                 | Compatible devices, cables, supply requirements, configurations, and connection sequence                                              |
| Conditions of use                      | Connection prerequisites, environmental requirements, and configuration limits from the applicable product manual                     |

The available software integration path is in the [W1 ROS 2 example](../sdk/ros2-example.md). Physical connection steps remain pending until the required hardware documentation is available.
