# Python: read and validate joint state

This runnable example reads two **synthetic revolute joint** states from a local JSON file, validates them, and writes the result to standard output. It demonstrates Python code rendering, input boundaries, and CLI behavior. It does not connect to a robot or define actual W1 joint names, SDK interfaces, or motion limits.

## Environment and execution

Requires Python **3.10 or later** and only the standard library; no pip installation is needed. Verified on Linux with Python 3.10.12. Run these commands from the repository root:

```bash
python3 examples/python/read_state.py
python3 examples/python/read_state.py examples/python/joint_state.json
```

On success, the exit code is `0` and stdout contains one JSON line with two joints. The position of `demo_joint_1` is `0.25 rad` and its velocity is `0.1 rad/s`. Stderr is empty.

Without a file argument, the script reads `joint_state.json` beside itself. You can therefore invoke the script by absolute path from another working directory. An explicitly supplied relative input path is resolved against the current working directory.

## Input and contract

Input is UTF-8 JSON. This block imports `examples/python/joint_state.json`; both language pages share the same input file:

::: code-group
<<< ../../../examples/python/joint_state.json{json:line-numbers}
:::

| Field               | Type and unit      | Constraints                                                                    |
| ------------------- | ------------------ | ------------------------------------------------------------------------------ |
| Root field `joints` | Array              | Required and non-empty; no other root fields are accepted                      |
| Each item's `name`  | String             | Required, non-blank, no leading or trailing whitespace; unique within the file |
| `position_rad`      | JSON number, rad   | Required and finite; converted to Python `float`                               |
| `velocity_rad_s`    | JSON number, rad/s | Required and finite; converted to Python `float`                               |

Each joint accepts exactly the three fields above. Duplicate JSON fields, booleans, numeric strings, `null`, `NaN`, `Infinity`, and floating-point overflow are rejected. Zero and negative values are allowed. The example checks neither physical limits nor timestamps or freshness. Add these according to the actual device contract; valid formatting alone does not establish that a value can safely control hardware.

## Complete Python source

The source is maintained only in `examples/python/read_state.py`. Editing it updates the code blocks in both language pages.

::: code-group
<<< ../../../examples/python/read_state.py{python:line-numbers}
:::

## Python features and interfaces

`JointState` is a dataclass with `frozen=True, slots=True`: declared fields make the model readable and instances reject ordinary field assignment. `load_states()` returns an immutable tuple, suitable for passing a parsed snapshot to other code.

Type annotations do not validate runtime data, so the loader checks each input. In particular, Python's `bool` subclasses `int`; using `type(value)` explicitly rejects booleans. JSON may contain integers or exponents outside the floating-point range, so conversion overflow and non-finite values are handled too.

| Interface                              | Input                      | Return or exceptions                                                                                                                     |
| -------------------------------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `load_states(path: Path)`              | File path                  | `tuple[JointState, ...]`; invalid data raises `ValueError`, reading failures raise `OSError`, and decoding failures raise `UnicodeError` |
| `main(argv: list[str] \| None = None)` | Optional CLI argument list | Returns a CLI exit code; argparse's help and argument-error paths may raise `SystemExit`                                                 |

The `with` statement closes the file automatically. Parsing is synchronous and reads the entire document into memory, which suits small snapshots. The `if __name__ == "__main__"` guard prevents CLI execution on import. Library callers handle exceptions; the CLI translates them into stderr and exit codes. `asdict()` and `json.dumps(..., allow_nan=False)` produce explicit JSON rather than the dataclass's debugging representation.

The `JointState` constructor itself does not validate external data; use `load_states()` to obtain validated snapshots. This is an independent Python implementation with no C++ extension binding and no ROS 2 runtime dependency.

## Failure behavior and tests

| Exit code | stdout / stderr    | Scenario                                                 |
| --------- | ------------------ | -------------------------------------------------------- |
| `0`       | JSON / empty       | Read and validation succeeded                            |
| `2`       | Empty / diagnostic | Invalid JSON or fields; CLI argument errors also use `2` |
| `3`       | Empty / diagnostic | Missing, unreadable, inaccessible, or invalid UTF-8 file |

`--help` prints help and returns `0` without reading data. Use a nonexistent file to inspect the error channel:

```bash
python3 examples/python/read_state.py missing-state.json
echo $?
```

When the file does not exist, the expected exit code is `3`. The behavioral tests cover immutability, missing and unknown fields, empty input, duplicate fields and names, booleans, non-finite values, overflow, malformed JSON, incorrect encoding, and invoking the CLI from another directory:

```bash
python3 -m unittest discover -s examples/python -p 'test_*.py' -v
```

Next: [C++ example](./cpp-example.md) · [ROS 2 interface example](./ros2-example.md) · [SDK integration template](./integration.md)
