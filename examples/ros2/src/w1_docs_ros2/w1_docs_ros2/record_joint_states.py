"""Record read-only JointState feedback as timestamped JSON Lines."""

import json
import math
from pathlib import Path
import queue
import sys
import threading
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


QUEUE_CAPACITY = 2048


class ReadTimeout(Exception):
    """No valid JointState arrived within the configured time budget."""


class RecorderFailure(Exception):
    """The recorder could not preserve every received sample."""


def validate_joint_state(msg):
    """Keep ROS JointState array order while checking its basic contract."""
    count = len(msg.name)
    if count == 0 or any(not name for name in msg.name):
        raise ValueError("joint names must be nonempty")
    if len(set(msg.name)) != count:
        raise ValueError("joint names must be unique")
    for field in ("position", "velocity", "effort"):
        values = getattr(msg, field)
        if len(values) not in (0, count):
            raise ValueError(f"{field} must be empty or match name length")
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"{field} contains NaN or infinity")


def message_record(msg, elapsed_seconds):
    """Convert one message without reordering or filling unavailable arrays."""
    validate_joint_state(msg)
    return {
        "record_type": "joint_state",
        "elapsed_seconds": elapsed_seconds,
        "stamp": {
            "sec": msg.header.stamp.sec,
            "nanosec": msg.header.stamp.nanosec,
        },
        "frame_id": msg.header.frame_id,
        "name": list(msg.name),
        "position": list(msg.position),
        "velocity": list(msg.velocity),
        "effort": list(msg.effort),
    }


class JointStateRecorder(Node):
    def __init__(self, context):
        super().__init__("w1_joint_state_recorder", context=context)
        self.output = None
        try:
            self.output_path = self.declare_parameter(
                "output_path", "joint_states.jsonl"
            ).value
            self.duration = self.declare_parameter(
                "duration_seconds", 10.0
            ).value
            self.timeout = self.declare_parameter(
                "timeout_seconds", 5.0
            ).value
            if (
                not isinstance(self.output_path, str)
                or not self.output_path.strip()
            ):
                raise ValueError("output_path must be a non-empty string")
            for name, value in (
                ("duration_seconds", self.duration),
                ("timeout_seconds", self.timeout),
            ):
                if not math.isfinite(value) or value <= 0:
                    raise ValueError(f"{name} must be finite and positive")

            # Exclusive creation prevents replacing an earlier capture.
            self.output = Path(self.output_path).open(
                "x", encoding="utf-8", buffering=1
            )
            self.pending = queue.Queue(maxsize=QUEUE_CAPACITY)
            self.invalid_message = None
            self.queue_overflow = False
            self.samples = 0
            self.writer_error = None
            self.writer_stop = threading.Event()
            self.received_samples = 0
            self.subscription = self.create_subscription(
                JointState,
                "/joint_states",
                self.on_joint_state,
                qos_profile_sensor_data,
            )
            self.output.write(
                json.dumps(
                    {
                        "record_type": "metadata",
                        "schema_version": 1,
                        "topic": self.subscription.topic_name,
                        "message_type": "sensor_msgs/msg/JointState",
                        "units": {
                            "position": {"revolute": "rad", "prismatic": "m"},
                            "velocity": {
                                "revolute": "rad/s",
                                "prismatic": "m/s",
                            },
                            "effort": {"revolute": "N*m", "prismatic": "N"},
                        },
                    },
                    allow_nan=False,
                )
                + "\n"
            )
            self.output.flush()
            self.started_at = time.monotonic()
            self.last_message_at = self.started_at
            self.deadline = self.started_at + self.duration
            self.writer = threading.Thread(
                target=self.write_pending, name="joint-state-jsonl-writer"
            )
            self.writer.start()
        except Exception:
            self.close_output()
            self.destroy_node()
            raise

    def on_joint_state(self, msg):
        """Validate and enqueue only; a writer thread performs file I/O."""
        if self.invalid_message is not None or self.queue_overflow:
            return
        received_at = time.monotonic()
        if (
            received_at >= self.deadline
            or received_at - self.last_message_at >= self.timeout
        ):
            return
        try:
            row = message_record(msg, received_at - self.started_at)
        except ValueError as error:
            self.invalid_message = error
            return
        try:
            self.pending.put_nowait((received_at, row))
            self.last_message_at = received_at
            self.received_samples += 1
        except queue.Full:
            self.queue_overflow = True

    def write_pending(self):
        while True:
            try:
                item = self.pending.get(timeout=0.1)
            except queue.Empty:
                if self.writer_stop.is_set():
                    return
                continue
            try:
                self.output.write(json.dumps(item[1], allow_nan=False) + "\n")
                self.samples += 1
            except (OSError, ValueError, UnicodeError) as error:
                self.writer_error = error
                self.writer_stop.set()
                return

    def stop_writer(self):
        self.writer_stop.set()
        self.writer.join()
        if self.writer_error is not None:
            raise OSError(f"could not write recording: {self.writer_error}")

    def close_output(self):
        if self.output is not None and not self.output.closed:
            try:
                self.output.flush()
            finally:
                self.output.close()


def record_for_duration(node, executor, context):
    while context.ok():
        if node.invalid_message is not None:
            raise ValueError(f"invalid JointState: {node.invalid_message}")
        if node.queue_overflow:
            raise RecorderFailure(
                f"recording queue reached its {QUEUE_CAPACITY}-message limit"
            )
        if node.writer_error is not None:
            raise RecorderFailure(
                f"could not write recording: {node.writer_error}"
            )

        now = time.monotonic()
        if now >= node.deadline:
            if node.received_samples:
                return 0
            raise ReadTimeout(
                "recording duration ended before any valid message"
            )
        if now - node.last_message_at >= node.timeout:
            raise ReadTimeout(f"no valid JointState for {node.timeout:g} s")
        remaining = min(
            node.deadline - now,
            node.timeout - (now - node.last_message_at),
        )
        executor.spin_once(timeout_sec=min(0.1, max(0.0, remaining)))
    raise InterruptedError("ROS context shut down")


def main(args=None):
    context = Context()
    node = None
    executor = None
    status = 0
    try:
        rclpy.init(args=args, context=context)
        node = JointStateRecorder(context)
        executor = SingleThreadedExecutor(context=context)
        executor.add_node(node)
        status = record_for_duration(node, executor, context)
    except (KeyboardInterrupt, InterruptedError, ExternalShutdownException):
        status = 130
    except FileExistsError as error:
        print(f"output file already exists: {error.filename}", file=sys.stderr)
        status = 2
    except (
        ValueError,
        InvalidParameterTypeException,
        InvalidParameterValueException,
    ) as error:
        print(str(error), file=sys.stderr)
        status = 2
    except ReadTimeout as error:
        print(str(error), file=sys.stderr)
        status = 3
    except (RecorderFailure, OSError) as error:
        print(f"recording failed: {error}", file=sys.stderr)
        status = 4
    finally:
        if node is not None:
            try:
                node.stop_writer()
            except OSError as error:
                print(f"could not finish recording: {error}", file=sys.stderr)
                status = 4
            try:
                node.close_output()
            except OSError as error:
                print(f"could not close recording: {error}", file=sys.stderr)
                status = 4
        if executor is not None:
            executor.shutdown()
        if node is not None:
            node.destroy_node()
        context.try_shutdown()
        if node is not None and status == 0:
            print(
                f"Recorded {node.samples} JointState messages to "
                f"{node.output_path}",
                file=sys.stderr,
            )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
