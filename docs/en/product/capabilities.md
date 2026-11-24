# Capabilities and applications

This page describes W1 mobility, perception and welding workflows. Performance, operating conditions and delivered versions still require confirmation. See [Models and specifications](./specifications.md) for reference parameters and the [ROS 2 example](../sdk/ros2-example.md) for software prerequisites.

## Mobility and perception

| Capability                           | Description                                                                                                                                            |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Bipedal mobility                     | Crossing obstacles, adapting to confined ship compartments, autonomous navigation, obstacle avoidance and stairs                                       |
| Environment and workpiece perception | Lidar, ToF cameras and a 3D line-scan camera for perceiving the surroundings and workpiece; counts are in [Components and interfaces](./interfaces.md) |
| Weld-seam processing                 | Finding and identifying seams, planning trajectories and performing welding                                                                            |

Perception equipment does not itself define public data topics or SDK features. See the [interface example](../sdk/ros2-example.md) for ROS 2 state and application services supported by the supplied interface material. Physical connections and mounting information belong in [Components and interfaces](./interfaces.md).

## Working postures and welding positions

Working postures include standing, a wide squat stance and half-kneeling. Welding positions include flat, vertical and overhead.

The descriptions do not provide posture-specific workspaces, stability conditions, welding processes or continuous operating times. Add performance records by posture and operating condition when available. The current material cannot establish welding accuracy, repeatability or quality pass rates.

## Control architecture

| Layer | Role                                | Documentation limit                                                  |
| ----- | ----------------------------------- | -------------------------------------------------------------------- |
| S2    | Task planning                       | Module boundaries and interface definitions remain to be supplied    |
| S1    | Action planning / action scheduling | The precise role and software module contract remain to be confirmed |
| S0    | Motion control                      | Module boundaries and interface definitions remain to be supplied    |

This table describes the architecture concept. Process boundaries, messages, execution rates, hardware allocation and the relationship of S2/S1/S0 to Planner, TeachPanel and PVT interfaces remain to be documented.

## Application stage and dated records

| Recorded on | Status or plan at that time                                                                         |
| ----------- | --------------------------------------------------------------------------------------------------- |
| 2026-11-06  | A plan to enter shipyards for training and validation in real working conditions at the end of 2026 |
| 2026-11-08  | At the R&D prototype stage, without commercialization or order deliveries                           |

These are historical status records and plans. SDK and firmware releases are maintained separately in [Releases](../support/releases.md).
