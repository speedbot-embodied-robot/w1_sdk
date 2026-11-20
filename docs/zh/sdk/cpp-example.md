# C++：类型化状态与 CMake 集成

这个示例用 **C++17 标准库**检查并输出两个模拟旋转关节的状态。它展示有类型的公共接口、RAII、错误枚举和 CMake target 接入方式。没有网络连接、真实 W1 SDK 调用或运动控制；示例中的关节名称和数值都是测试数据，校验通过也不表示数值符合任何硬件限位。

## 构建和运行

在仓库根目录执行。需要 CMake 3.20 以上及支持 C++17 的编译器；不依赖 Python、ROS 2 或 Node.js。

```bash
cmake -S examples/cpp -B examples/cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build examples/cpp/build --parallel
ctest --test-dir examples/cpp/build --output-on-failure
./examples/cpp/build/joint_state_demo
```

成功时退出码为 `0`，标准输出为：

```text
demo_joint_1: position=0.250 rad, velocity=0.100 rad/s
demo_joint_2: position=-0.500 rad, velocity=0.000 rad/s
```

主动输入一个非有限数值，验证失败路径：

```bash
./examples/cpp/build/joint_state_demo --invalid
echo $?
```

标准错误输出 `Invalid state: position must be finite (joint index 1)`，退出码为 `1`。未知命令行参数返回 `2`，构造数据等步骤发生标准异常时返回 `3`。`--help` 显示用法并返回 `0`。上述命令使用 Linux 单配置生成器；本例已在 Ubuntu 22.04、GCC 11.4、CMake 3.22.1 上验证，其他系统未实测。

## 公共接口与数据约定

| 符号                            | 类型或签名                                     | 约定                                                                   |
| ------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------- |
| `w1_docs::JointState`           | 拥有三个 `std::vector` 的值类型                | `names` 非空、名称非空且唯一；每个位置单位为 rad；速度单位为 rad/s     |
| `positions_rad`                 | `std::vector<double>`                          | 必须与名称数组等长，所有数值有限                                       |
| `velocities_rad_s`              | `std::vector<double>`                          | 可以整体为空，表示未提供速度；否则必须等长且全部有限。空值不等于零速度 |
| `w1_docs::validate_state`       | `ValidationResult(const JointState&) noexcept` | 不修改或复制输入、不分配内存。返回首个错误；通过错误枚举判断结果       |
| `ValidationResult::joint_index` | `std::size_t`                                  | 元素错误为从 0 开始的索引；整体错误或成功为 `kNoJoint`                 |
| `w1_docs::describe`             | `std::string_view(ValidationCode) noexcept`    | 返回静态字符串的只读视图，生命周期覆盖整个程序                         |

位置数组在本例中是必填项。ROS 2 的 `JointState` 允许部分数组为空，所以对接时必须根据业务需求决定如何转换，不能把本例校验规则当成 ROS 消息的全部定义。见 [ROS 2 示例](./ros2-example.md)。

下面的头文件直接导入 `examples/cpp/include/w1_docs/joint_state.hpp`；中文和英文引用同一个文件。

::: code-group
<<< ../../../examples/cpp/include/w1_docs/joint_state.hpp{cpp:line-numbers}
:::

## 可运行调用代码

`JointState` 自己拥有数组；离开作用域时，标准容器自动释放内存。校验函数的 `const&` 只在调用期间借用这些数据。代码不保存裸指针，也不需要调用者手动释放资源。

::: code-group
<<< ../../../examples/cpp/main.cpp{cpp:line-numbers}
:::

`noexcept` 仅用于不分配内存的校验和诊断函数。创建 `std::vector`、`std::string` 仍可能抛出异常，示例入口因此保留异常处理。这里没有后台线程；多个线程可以同时读取同一个不可变状态，若有线程写入，调用者必须自行同步。

::: details 展开校验实现
::: code-group
<<< ../../../examples/cpp/src/joint_state.cpp{cpp:line-numbers}
:::
:::

重名检查使用简单的两层循环，最坏为 O(n²)，优点是无需额外分配；它适用于此小规模教学示例，未承诺实时控制性能。此接口处理的是已构造的 C++ 对象，不负责 JSON 解析或 DDS 接收。

## 作为库接入自己的项目

库与可执行程序分开构建。公开 target 是 `w1_docs::state`，它传播头文件搜索路径和 C++17 要求。此版本支持 `add_subdirectory`，尚未提供 `install`、`export` 或 `find_package` 安装包。

::: code-group
<<< ../../../examples/cpp/CMakeLists.txt{cmake:line-numbers}
:::

仓库还提供独立消费工程，使用公共头文件和库 target，复用同一份调用代码：

::: code-group
<<< ../../../examples/cpp/consumer/CMakeLists.txt{cmake:line-numbers}
:::

```bash
cmake -S examples/cpp/consumer -B examples/cpp/build/consumer -DCMAKE_BUILD_TYPE=Release
cmake --build examples/cpp/build/consumer --parallel
./examples/cpp/build/consumer/state_consumer
```

将此 CMake 文件用于自己的项目时，把 `add_subdirectory` 的源路径指向检出的 `examples/cpp`，并把 `../main.cpp` 换成自己的调用文件。不要再将 `src/joint_state.cpp` 加进可执行程序，链接库 target 即可。作为子目录使用时，示例和测试默认关闭，避免改动消费工程的测试配置。

## 测试覆盖与后续接入

CTest 检查正常运行和 CLI 失败路径。库测试包含 12 个用例：有效数据、空状态、缺失或过多的位置、可选速度为空、速度长度错误、空名称、重复名称、NaN、正负无穷和超出示例数值的有限输入。测试通过实际条件返回非零状态，Release 构建也会执行检查。

对接真实 SDK 时，在数据获取层填入真实字段映射、时间戳和硬件单位换算，再添加产品限位及设备故障处理。与 [Python 示例](./python-example.md)相比，本例是独立 C++ 实现，没有 Python 绑定层；真正的 SDK 接入要求仍填写在 [SDK 集成](./integration.md)。
