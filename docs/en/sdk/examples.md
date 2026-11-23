# Runnable examples

The Python example subscribes to W1's `/joint_states` topic with ROS 2 Humble and records feedback as JSONL. The C++ example uses synthetic state to demonstrate language and library interfaces. The ROS 2 guide also covers a single-joint read, PVT status queries, and planning, teaching, and welding interfaces.

| Example                       | Input and output                                            | Focus                                                                          | Environment                                                                  |
| ----------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| [Python](./python-example.md) | Subscribe to `/joint_states` and record feedback as JSONL   | ROS 2 subscriptions, message-array semantics, acquisition time, file recording | Python 3.10, ROS 2 Humble, rclpy, sensor_msgs, std_srvs; W1 workspace for W1 |
| [C++](./cpp-example.md)       | Construct synthetic state and validate it through a library | RAII, ownership, explicit errors, separate library and caller                  | C++17, CMake                                                                 |
| [W1 ROS 2](./ros2-example.md) | Read one joint and query PVT status                         | Joint-name matching, QoS, asynchronous services, timeouts, shutdown            | ROS 2 Humble, rclpy, sensor_msgs, std_srvs; W1 workspace for integration     |

## Suggested order

Build the ROS 2 package as described on the Python page, then run the recorder against an active W1 `/joint_states` publisher. Without a W1 environment, you can run the C++ example and the isolated-endpoint tests described in the ROS 2 guide. Those tests exercise client communication with test endpoints; they do not run a W1 controller or simulate hardware.

Python and C++ are independent implementations, with no language binding. The ROS 2 example uses the Python client library; the ROS message type defines the contract between nodes written in different languages.

## Code display and maintenance

Each page imports real source files from the repository examples/ directory. Both translations show the same implementation with syntax highlighting and copy controls. Comments and output retain the source language.

Rebuild after changing source files to update the displayed code. Maintain parameter descriptions, commands, and behavioral explanations in both languages separately. This website serves static documentation; run examples on your development machine or in CI.

## Connecting W1

For `speed_W1_v1.2`, see the [W1 ROS 2 example](./ros2-example.md) and [W1 whole-body control reference](../api/w1-control.md). Maintain installation and delivery versions in [SDK integration](./integration.md). Check the installed configuration, running model, ROS domain, and endpoint QoS before connecting.
