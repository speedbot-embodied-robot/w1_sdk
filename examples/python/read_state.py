"""Parse synthetic joint snapshots; this example does not connect to a robot."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import sys
from typing import Any


@dataclass(frozen=True, slots=True)
class JointState:
    """One simulated revolute joint, using radians and radians per second."""

    name: str
    position_rad: float
    velocity_rad_s: float


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON number: {value}")


def _finite_number(value: Any, field: str) -> float:
    # bool subclasses int in Python, so isinstance(value, (int, float)) is not enough.
    if type(value) not in (int, float):
        raise ValueError(f"{field} must be a JSON number, not a bool or string")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"{field} is outside float range") from error
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def load_states(path: Path) -> tuple[JointState, ...]:
    """Load validated state; propagate OSError, UnicodeError or ValueError."""
    with path.open("r", encoding="utf-8") as stream:
        document = json.load(
            stream, object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
    if not isinstance(document, dict) or set(document) != {"joints"}:
        raise ValueError("root must be an object with exactly the field 'joints'")
    rows = document["joints"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("joints must be a non-empty array")
    states: list[JointState] = []
    names: set[str] = set()
    required = {"name", "position_rad", "velocity_rad_s"}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError(f"joints[{index}] must contain exactly {sorted(required)}")
        name = row["name"]
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise ValueError(
                f"joints[{index}].name must be non-blank without edge spaces"
            )
        if name in names:
            raise ValueError(f"duplicate joint name: {name}")
        names.add(name)
        states.append(
            JointState(
                name,
                _finite_number(row["position_rad"], f"{name}.position_rad"),
                _finite_number(row["velocity_rad_s"], f"{name}.velocity_rad_s"),
            )
        )
    return tuple(states)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("joint_state.json"),
        help="UTF-8 JSON file; defaults to the sample beside this script",
    )
    args = parser.parse_args(argv)
    try:
        states = load_states(args.input)
    except (OSError, UnicodeError) as error:
        print(f"file error: {error}", file=sys.stderr)
        return 3
    except ValueError as error:
        print(f"invalid state: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"joints": [asdict(state) for state in states]}, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
