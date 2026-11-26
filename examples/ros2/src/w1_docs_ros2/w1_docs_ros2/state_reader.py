"""Read one named joint position from W1 /joint_states."""

import json
import math
import sys
import time

import rclpy
from rclpy.context import Context
from rclpy.exceptions import (
    InvalidParameterTypeException,
    InvalidParameterValueException,
)
from rclpy.executors import ExternalShutdownException, SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState


class ReadTimeout(Exception):
    """The requested joint state was not received before the deadline."""


def validate_state(msg):
    """Validate named finite states; each optional array is empty or name-sized."""
    count = len(msg.name)
    if count == 0 or any(not name for name in msg.name):
        raise ValueError("joint names must be nonempty")
    if len(set(msg.name)) != count:
        raise ValueError("joint names must be unique")
    if not any((msg.position, msg.velocity, msg.effort)):
        raise ValueError("provide at least one state array")
    for field in ("position", "velocity", "effort"):
        values = getattr(msg, field)
        if len(values) not in (0, count):
            raise ValueError(f"{field} must be empty or match name length")
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"{field} contains NaN or infinity")


def named_position(msg, joint_name):
    validate_state(msg)
    if not msg.position or joint_name not in msg.name:
        return None
    return msg.position[msg.name.index(joint_name)]


class StateReader(Node):
    def __init__(self, context):
        super().__init__("w1_read_state", context=context)
        try:
            self.joint_name = self.declare_parameter(
                "joint_name", "right_elbow_joint"
            ).value
            self.timeout = self.declare_parameter("timeout_seconds", 5.0).value
            if not self.joint_name.strip():
                raise ValueError("joint_name must not be empty")
            if not math.isfinite(self.timeout) or self.timeout <= 0:
                raise ValueError("timeout_seconds must be finite and positive")
            self.snapshot = None
            self.invalid_message = None
            self.subscription = self.create_subscription(
                JointState, "/joint_states", self.on_state, qos_profile_sensor_data
            )
        except Exception:
            self.destroy_node()
            raise

    def on_state(self, msg):
        if self.snapshot is not None or self.invalid_message is not None:
            return
        try:
            position = named_position(msg, self.joint_name)
        except ValueError as error:
            self.invalid_message = error
            return
        if position is not None:
            self.snapshot = {
                "joint_name": self.joint_name,
                "position_rad": position,
                "stamp": {
                    "sec": msg.header.stamp.sec,
                    "nanosec": msg.header.stamp.nanosec,
                },
                "frame_id": msg.header.frame_id,
            }


def read_state(node, executor, context):
    deadline = time.monotonic() + node.timeout
    while context.ok():
        if node.invalid_message is not None:
            raise ValueError(f"invalid JointState: {node.invalid_message}")
        if node.snapshot is not None:
            print(json.dumps(node.snapshot, allow_nan=False), flush=True)
            return 0
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ReadTimeout(f"position for {node.joint_name} timed out")
        executor.spin_once(timeout_sec=min(0.1, remaining))
    raise InterruptedError("ROS context shut down")


def main(args=None):
    context = Context()
    node = None
    executor = None
    try:
        rclpy.init(args=args, context=context)
        node = StateReader(context)
        executor = SingleThreadedExecutor(context=context)
        executor.add_node(node)
        return read_state(node, executor, context)
    except (KeyboardInterrupt, InterruptedError, ExternalShutdownException):
        return 130
    except (
        ValueError,
        InvalidParameterTypeException,
        InvalidParameterValueException,
    ) as error:
        print(str(error), file=sys.stderr)
        return 2
    except ReadTimeout as error:
        print(str(error), file=sys.stderr)
        return 3
    finally:
        if executor is not None:
            executor.shutdown()
        if node is not None:
            node.destroy_node()
        context.try_shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
