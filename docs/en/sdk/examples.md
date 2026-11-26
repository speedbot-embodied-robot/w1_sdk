# Runnable examples

The repository provides a Python joint-feedback recorder and a C++17 data-validation example. The W1 ROS 2 page covers state topics, real-robot IMU and motor diagnostics, the 26-axis command layout, and the bilateral teaching interface.

| Example                       | Input and output                                               | Focus                                                                        | Environment                                                           |
| ----------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| [Python](./python-example.md) | Subscribe to `/joint_states` and record feedback as JSONL      | ROS 2 subscriptions, message-array semantics, timestamps, and file recording | Python 3.10, ROS 2 Humble, rclpy, sensor_msgs                         |
| [C++](./cpp-example.md)       | Validate synthetic state                                       | RAII, ownership, error handling, CMake target                                | C++17, CMake                                                          |
| [W1 ROS 2](./ros2-example.md) | Read joint and IMU state, inspect motor and control interfaces | Message fields, QoS, 26-axis order, teaching topic                           | ROS 2 Humble; a running device workspace is required to connect to W1 |

The Python recorder saves received joint feedback. The C++ example uses synthetic data. The ROS 2 page demonstrates subscriptions to public joint and IMU topics and describes public control-message layouts.
