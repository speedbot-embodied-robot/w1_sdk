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

This site's [ROS 2 interface example](../sdk/ros2-example.md) and [whole-body control reference](../api/w1-control.md) specifically cover `speed_W1_v1.2`, with 28 controlled axes and two seven-axis arms.

The product reference degree-of-freedom count and the number of software-controlled axes differ; see [Models and specifications](./specifications.md). When integrating software, follow the installed configuration and interface documentation for the specific model.

## Where developers can start

| Task                                              | Required configuration                                                                      | Result to inspect                                                                                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Read joint feedback and PVT status                | ROS 2 Humble, this site's `w1_docs_ros2` reader and running endpoints from the W1 workspace | Read the right elbow position by name and inspect the PVT service's `success/message`; see the [ROS 2 example](../sdk/ros2-example.md) |
| Request planning for one arm                      | W1 Planner, `speedbot_msgs` and the corresponding planning scene                            | Call `/plan_move` with `execute=false` and inspect the result, trajectory and scene version; see the planning example on the same page |
| Understand welding-program generation             | W1 vision node, TeachPanel, camera, measured calibration and a valid TCP                    | Review Capture/Build prerequisites, program paths and length fields in the welding-service section on the same page                    |
| Check language toolchains and calling conventions | Python 3.10+, or C++17 and CMake                                                            | Run the independent [examples](../sdk/examples.md) for data validation and calling patterns                                            |

The repository's client tests cover reads and error handling against isolated endpoints. Running the W1 controller, planner, camera and welding workflow requires the corresponding workspace and equipment; client tests do not replace whole-robot acceptance. Installation and delivery-version information is maintained in [SDK integration](../sdk/integration.md).
