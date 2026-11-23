# Runnable examples

The Python and C++ examples use synthetic joint state to demonstrate language features and execution. The ROS 2 example now follows the supplied W1 interface documentation: it reads joint feedback, queries PVT status, and explains planning, teaching, and welding calls.

| Example                       | Input and output                                        | Focus                                                               | Environment                                                                                |
| ----------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| [Python](./python-example.md) | Read JSON, validate it, and emit structured output      | Type hints versus runtime checks, immutable data, exceptions, CLI   | Python 3.10+, standard library                                                             |
| [C++](./cpp-example.md)       | Construct typed state and validate it through a library | RAII, ownership, explicit errors, separate library and caller       | C++17, CMake                                                                               |
| [W1 ROS 2](./ros2-example.md) | Read `/joint_states` and query PVT status               | Joint-name matching, QoS, asynchronous services, timeouts, shutdown | ROS 2 Humble, rclpy, sensor_msgs, std_srvs; online integration also needs the W1 workspace |

## Suggested order

Run Python and C++ first to check your language toolchains, then build the read-only ROS 2 client. With a W1 workspace installed, connect to an isolated W1 mock to read feedback and PVT status. A standard Humble installation can run the repository tests for client communication and error handling. Those endpoint fixtures do not implement a W1 controller.

Python and C++ are independent implementations, with no language binding. The ROS 2 example uses the Python client library; the ROS message type defines the contract between nodes written in different languages.

## Code display and maintenance

Each page imports real source files from the repository examples/ directory. Both translations show the same implementation with syntax highlighting and copy controls. Comments and output retain the source language.

Rebuild after changing source files to update the displayed code. Maintain parameter descriptions, commands, and behavioral explanations in both languages separately. This website serves static documentation; run examples on your development machine or in CI.

## Connecting real W1 hardware

For `speed_W1_v1.2`, see the [W1 ROS 2 example](./ros2-example.md) and [W1 whole-body control reference](../api/w1-control.md). Maintain installation and delivery versions in [SDK integration](./integration.md). Check the installed configuration, running model, ROS domain, and endpoint QoS before connecting.
