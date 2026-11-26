# Capabilities and applications

This page describes W1 mobility, perception and welding workflows. See [Models and specifications](./specifications.md) for reference parameters and the [ROS 2 example](../sdk/ros2-example.md) for software prerequisites.

## Mobility and perception

| Capability                           | Description                                                                                                                                            |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Bipedal mobility                     | Crossing obstacles, adapting to confined ship compartments, autonomous navigation, obstacle avoidance and stairs                                       |
| Environment and workpiece perception | Lidar, ToF cameras and a 3D line-scan camera for perceiving the surroundings and workpiece; counts are in [Components and interfaces](./interfaces.md) |
| Weld-seam processing                 | Finding and identifying seams, planning trajectories and performing welding                                                                            |

See the [interface example](../sdk/ros2-example.md) for ROS 2 state and application services. Physical connections and mounting information belong in [Components and interfaces](./interfaces.md).

## Working postures and welding positions

Working postures include standing, a wide squat stance and half-kneeling. Welding positions include flat, vertical and overhead.

## Control architecture

| Layer | Role                                |
| ----- | ----------------------------------- |
| S2    | Task planning                       |
| S1    | Action planning / action scheduling |
| S0    | Motion control                      |

## Application stage and dated records

| Recorded on | Status or plan at that time                                                                         |
| ----------- | --------------------------------------------------------------------------------------------------- |
| 2026-11-06  | A plan to enter shipyards for training and validation in real working conditions at the end of 2026 |
