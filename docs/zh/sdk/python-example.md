# Python：读取和校验关节状态

这个可运行示例从本地 JSON 文件读取两组**模拟旋转关节**状态，校验后将结果写到标准输出。它用于测试 Python 代码展示、数据边界和命令行调用，不连接机器人，也不代表 W1 的真实关节名称、SDK 接口或运动范围。

## 环境与运行

要求 Python **3.10 或以上**，只用标准库，无需 pip 安装。已在 Linux、Python 3.10.12 上验证。下面的命令在仓库根目录执行：

```bash
python3 examples/python/read_state.py
python3 examples/python/read_state.py examples/python/joint_state.json
```

成功时退出码是 `0`，stdout 是一行 JSON，包含两个关节；`demo_joint_1` 的位置为 `0.25 rad`、速度为 `0.1 rad/s`。stderr 为空。

不传文件参数时，脚本读取自己所在目录中的 `joint_state.json`，因此也可以在其他工作目录通过脚本的绝对路径运行。显式传入的相对文件路径则相对于当前工作目录解析。

## 输入数据与约定

文件为 UTF-8 JSON。以下内容直接引用 `examples/python/joint_state.json`，中英文页面共享这一份输入：

::: code-group
<<< ../../../examples/python/joint_state.json{json:line-numbers}
:::

| 字段              | 类型与单位       | 约束                                       |
| ----------------- | ---------------- | ------------------------------------------ |
| 根对象的 `joints` | 数组             | 必填且非空；根对象不接受其他字段           |
| 每项的 `name`     | 字符串           | 必填、非空、无首尾空白；同一文件内不得重复 |
| `position_rad`    | JSON 数字，rad   | 必填、有限值，读入后转为 Python `float`    |
| `velocity_rad_s`  | JSON 数字，rad/s | 必填、有限值，读入后转为 Python `float`    |

每个关节只接受表中的三个字段。重复 JSON 字段、布尔值、数字字符串、`null`、`NaN`、`Infinity` 和浮点溢出均被拒绝。数值零和负值可以使用。示例没有物理限位、时间戳或新鲜度检查；实际接入时必须依据设备的真实数据契约补充，不能将“格式有效”当作“可控制设备”。

## 完整 Python 源码

源码只维护在 `examples/python/read_state.py`。修改该文件会同步改变两种语言页面中的代码块。

::: code-group
<<< ../../../examples/python/read_state.py{python:line-numbers}
:::

## Python 特性与接口

`JointState` 是 `frozen=True, slots=True` 的 dataclass：声明的字段便于阅读，实例不支持普通字段赋值；`load_states()` 返回不可变 tuple，适合把一次解析后的快照传给其他代码。

类型注解不会执行运行时校验，因此加载器逐项检查输入。尤其 Python 中 `bool` 是 `int` 的子类，代码用 `type(value)` 明确拒绝布尔值。JSON 可以包含超出浮点表示范围的整数或指数，转换时的溢出和非有限值也会被处理。

| 接口                                   | 输入               | 返回或异常                                                                                               |
| -------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------- |
| `load_states(path: Path)`              | 文件路径           | `tuple[JointState, ...]`；输入不符时抛 `ValueError`，文件读取失败抛 `OSError`，解码失败抛 `UnicodeError` |
| `main(argv: list[str] \| None = None)` | 可选命令行参数列表 | 返回 CLI 退出码；`argparse` 自身的帮助或参数错误可抛 `SystemExit`                                        |

文件通过 `with` 自动关闭；解析是同步的、一次性读入内存，适合小型快照。`if __name__ == "__main__"` 让导入模块不会执行命令行。库函数的异常由调用者处理，CLI 则将错误转换为 stderr 和退出码。`asdict()` 配合 `json.dumps(..., allow_nan=False)` 输出明确的 JSON，不依赖 dataclass 的调试字符串。

`JointState` 构造器本身不验证外部数据；应通过 `load_states()` 获得经过校验的快照。该示例是独立 Python 实现，没有 C++ 扩展绑定，也没有 ROS 2 运行时依赖。

## 失败行为与测试

| 退出码 | stdout / stderr | 场景                                         |
| ------ | --------------- | -------------------------------------------- |
| `0`    | JSON / 空       | 读取和校验成功                               |
| `2`    | 空 / 诊断信息   | JSON 或字段非法；命令行参数错误也使用 `2`    |
| `3`    | 空 / 诊断信息   | 文件不存在、无权限、无法读取或不是有效 UTF-8 |

`--help` 打印帮助并返回 `0`，不读取数据。可以指定一个不存在的文件检查错误通道：

```bash
python3 examples/python/read_state.py missing-state.json
echo $?
```

当文件不存在时，预期退出码为 `3`。完整行为测试包含不可变性、缺失和多余字段、空输入、重复字段和名称、布尔值、非有限值、溢出、损坏 JSON、错误编码，以及从其他目录调用 CLI：

```bash
python3 -m unittest discover -s examples/python -p 'test_*.py' -v
```

下一步：[C++ 示例](./cpp-example.md) · [ROS 2 接口示例](./ros2-example.md) · [SDK 集成模板](./integration.md)
