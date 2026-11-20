# C++: typed state and CMake integration

This **C++17 standard-library** example validates and prints the state of two synthetic revolute joints. It demonstrates a typed public interface, RAII, error enums, and CMake target integration. It makes no network connection, calls no real W1 SDK, and sends no motion commands. Names and values are test data; passing validation does not establish compliance with hardware limits.

## Build and run

Run from the repository root. You need CMake 3.20 or newer and a C++17 compiler; Python, ROS 2, and Node.js are not dependencies of this example.

```bash
cmake -S examples/cpp -B examples/cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build examples/cpp/build --parallel
ctest --test-dir examples/cpp/build --output-on-failure
./examples/cpp/build/joint_state_demo
```

Success returns exit code `0` and writes the following to stdout:

```text
demo_joint_1: position=0.250 rad, velocity=0.100 rad/s
demo_joint_2: position=-0.500 rad, velocity=0.000 rad/s
```

Inject a nonfinite position to exercise the error path:

```bash
./examples/cpp/build/joint_state_demo --invalid
echo $?
```

Stderr contains `Invalid state: position must be finite (joint index 1)` and the exit code is `1`. Unknown arguments return `2`; a standard exception during operations such as constructing the state returns `3`. `--help` prints usage and returns `0`. These commands use a Linux single-configuration generator. Verification used Ubuntu 22.04, GCC 11.4, and CMake 3.22.1; other systems have not been tested.

## Public interface and data contract

| Symbol                          | Type or signature                              | Contract                                                                                                                                              |
| ------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `w1_docs::JointState`           | Value type owning three `std::vector` objects  | `names` must be nonempty; names must be nonempty and unique; positions use rad and velocities use rad/s                                               |
| `positions_rad`                 | `std::vector<double>`                          | Must match the number of names; all values must be finite                                                                                             |
| `velocities_rad_s`              | `std::vector<double>`                          | May be entirely empty to represent unavailable velocity; otherwise the length must match and values must be finite. Empty does not mean zero velocity |
| `w1_docs::validate_state`       | `ValidationResult(const JointState&) noexcept` | Does not modify, copy, or allocate for the input. Returns the first error as an enum                                                                  |
| `ValidationResult::joint_index` | `std::size_t`                                  | Zero-based index for element errors; `kNoJoint` for whole-state errors or success                                                                     |
| `w1_docs::describe`             | `std::string_view(ValidationCode) noexcept`    | Returns a read-only view of a static string with program lifetime                                                                                     |

This example requires positions. ROS 2 `JointState` permits some arrays to be empty, so an adapter must choose an application-specific mapping rather than treating these checks as the entire ROS message definition. See the [ROS 2 example](./ros2-example.md).

The header below is imported directly from `examples/cpp/include/w1_docs/joint_state.hpp`. Both language pages use this same file.

::: code-group
<<< ../../../examples/cpp/include/w1_docs/joint_state.hpp{cpp:line-numbers}
:::

## Runnable caller

`JointState` owns its arrays, and standard containers release storage when they leave scope. The validator borrows the data via `const&` only for the call. It retains no raw pointers and requires no manual resource release.

::: code-group
<<< ../../../examples/cpp/main.cpp{cpp:line-numbers}
:::

`noexcept` is reserved for the validator and diagnostics, which do not allocate. Constructing `std::vector` or `std::string` can still throw, so the executable handles standard exceptions. There is no background thread. Multiple threads may read the same immutable state; callers must synchronize any concurrent writer.

::: details Validation implementation
::: code-group
<<< ../../../examples/cpp/src/joint_state.cpp{cpp:line-numbers}
:::
:::

The duplicate-name check uses a nested loop with O(n²) worst-case complexity and no additional allocation. This is appropriate for this small educational example; it makes no real-time performance guarantee. The interface accepts constructed C++ objects and does not parse JSON or receive DDS messages.

## Consume the library from another project

The library and executable are separate build targets. The public target `w1_docs::state` propagates its include directory and C++17 requirement. This version supports `add_subdirectory`; it does not provide an `install`, `export`, or `find_package` package.

::: code-group
<<< ../../../examples/cpp/CMakeLists.txt{cmake:line-numbers}
:::

An independent consumer project uses the public header and library target, reusing the same caller source:

::: code-group
<<< ../../../examples/cpp/consumer/CMakeLists.txt{cmake:line-numbers}
:::

```bash
cmake -S examples/cpp/consumer -B examples/cpp/build/consumer -DCMAKE_BUILD_TYPE=Release
cmake --build examples/cpp/build/consumer --parallel
./examples/cpp/build/consumer/state_consumer
```

For your own project, point `add_subdirectory` at the checked-out `examples/cpp` directory and replace `../main.cpp` with your caller. Link the library target rather than adding `src/joint_state.cpp` to the executable again. When consumed as a subdirectory, examples and tests default to disabled to avoid altering the parent project's test configuration.

## Test coverage and next steps

CTest exercises normal execution and the CLI failure path. Twelve library cases cover valid data, empty state, missing or extra positions, omitted optional velocities, a velocity length mismatch, empty and duplicate names, NaN, positive and negative infinity, and finite input outside the demonstration values. Tests use explicit checks and return a nonzero status on failure, including Release builds.

When connecting a real SDK, implement field mapping, timestamps, and unit conversions in the acquisition layer, then add product limits and device-error handling. This is an independent C++ implementation without a Python binding; compare the [Python example](./python-example.md) and record real SDK requirements in [SDK integration](./integration.md).
