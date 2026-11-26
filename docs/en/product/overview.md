# Product overview

W1 (Weldroid-W1) is a full-size bipedal humanoid welding robot from Speedbot for complex welding settings such as shipbuilding. Its product direction is to move to a workstation in a confined space, perceive the workpiece and weld seam, and perform welding.

See [Models and specifications](./specifications.md) for reference parameters and their conditions.

## Positioning and use cases

| Item                   | Description                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| Form                   | Full-size bipedal humanoid welding robot                                                                |
| Intended setting       | Shipbuilding, particularly confined and structurally complex spaces such as ship compartments           |
| Intended work          | Reach a workstation, perceive the environment and workpiece, identify seams, plan trajectories and weld |
| Documentation audience | Developers learning about W1, reading robot state or integrating planning and welding workflows         |

See [Capabilities and applications](./capabilities.md) for mobility, postures, perception configuration and application progress.

## Model and interface scope

This site's [ROS 2 interface examples](../sdk/ros2-example.md) and [whole-body control reference](../api/w1-control.md) cover the official `speed_W1_v1.2` configuration, with 26 controlled joints and six axes on each arm.

The mechanical whole-body degree-of-freedom figure and the software controlled-joint count describe different parameters; see [Models and specifications](./specifications.md). Follow the installed configuration and interface documentation for software integration.

## Where developers can start

| Task                                              | Required configuration                                      | Result to inspect                                                                                                      |
| ------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Read joint and IMU state                          | ROS 2 Humble and a running W1 workspace                     | Read joint state by name and parse IMU messages; see the [ROS 2 examples](../sdk/ros2-example.md)                      |
| Review bilateral teaching                         | A system with the W1 teaching panel loaded                  | Check single-arm and dual-arm `/arm_move` target formats; see the [ROS 2 examples](../sdk/ros2-example.md)             |
| Review command-array layout                       | ROS 2 Humble and the official `speed_W1_v1.2` configuration | Check the 26-axis order, data blocks, and command topics; see the [whole-body control interface](../api/w1-control.md) |
| Check language toolchains and calling conventions | Python 3.10+, or C++17 and CMake                            | Run the independent [examples](../sdk/examples.md) for data validation and calling patterns                            |

The joint, IMU, and control examples explain ROS 2 message reading and data layout. Availability of hardware state streams depends on the corresponding real-robot publishers and monitor nodes. See [SDK integration](../sdk/integration.md) for environment details.
