# Product overview

W1, also known as Weldroid-W1, is a full-size bipedal humanoid welding robot introduced by Speedbot for complex welding settings such as shipbuilding. Its intended workflow is to reach a workstation in a confined space, perceive the workpiece and weld seam, and perform welding.

The official product designation, hardware revisions and applicable operating conditions remain to be confirmed. See [Models and specifications](./specifications.md) for reference values and measurement conditions still needed.

## Positioning and use cases

| Item                   | Description                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| Form                   | Full-size bipedal humanoid welding robot                                                                |
| Intended setting       | Shipbuilding, particularly confined and structurally complex spaces such as ship compartments           |
| Intended work          | Reach a workstation, perceive the environment and workpiece, identify seams, plan trajectories and weld |
| Documentation audience | Developers learning about W1, reading robot state or integrating planning and welding workflows         |

See [Capabilities and applications](./capabilities.md) for mobility, postures, perception equipment and application progress. Process coverage, operating conditions and performance acceptance criteria still need to be supplied.

## Model and interface scope

The relationship between the W1 product name and individual hardware revisions remains to be confirmed. This site's [ROS 2 example](../sdk/ros2-example.md) and [whole-body control reference](../api/w1-control.md) specifically cover `speed_W1_v1.2`, with 28 controlled joints and two seven-joint arms.

The product's reference degree-of-freedom count differs from the software's controlled-joint count; see [Models and specifications](./specifications.md). Use the installed configuration and interface documentation for the model you are integrating. Support must be checked for each version.

## Where developers can start

| Task                                              | Required configuration                                                                      | Result to inspect                                                                                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Read joint feedback and PVT status                | ROS 2 Humble, this site's `w1_docs_ros2` reader and running endpoints from the W1 workspace | Read the right elbow position by name and inspect the PVT service's `success/message`; see the [ROS 2 example](../sdk/ros2-example.md) |
| Request planning for one arm                      | W1 Planner, `speedbot_msgs` and the corresponding planning scene                            | Call `/plan_move` with `execute=false` and inspect the result, trajectory and scene version; see the planning example on the same page |
| Understand welding-program generation             | W1 vision node, TeachPanel, camera, measured calibration and a valid TCP                    | Review Capture/Build prerequisites, program paths and length fields in the welding-service section on the same page                    |
| Check language toolchains and calling conventions | Python 3.10+, or C++17 and CMake                                                            | Run the independent [examples](../sdk/examples.md) for data validation and calling patterns                                            |

The repository's client tests cover reads and error handling against isolated endpoints. Running the W1 controller, planner, camera and welding workflow requires their workspace and equipment. Client tests do not establish whole-robot acceptance. Maintain installation and delivery-version information in [SDK integration](../sdk/integration.md).

## Appearance and identification material

The supplied material contains no product photos ready for publication, numbered component diagrams or nameplate locations. Add revision-specific photographs, viewing directions, identification marks and image permissions when available. See [Components and interfaces](./interfaces.md) for the known perception components and missing physical-interface information.
