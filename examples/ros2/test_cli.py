"""Test the installed ROS examples against local, remapped synthetic endpoints.

This fixture is not W1 mock, a controller or a robot simulator. It exercises ROS
transport and application handling only. Run after building and sourcing the
example overlay. No motion command topic is created or published.
"""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ENV = {**os.environ, "ROS_LOCALHOST_ONLY": "1"}
ENV.setdefault("ROS_DOMAIN_ID", "169")


def command(topic, service, *parameters):
    return [
        "ros2", "run", "w1_docs_ros2", "state_reader", "--ros-args",
        "-r", f"/joint_states:={topic}",
        "-r", f"/mit_controller/get_pvt_interpolation_status:={service}",
        *parameters,
    ]


def recorder_command(topic, *parameters):
    return [
        "ros2", "run", "w1_docs_ros2", "record_joint_states", "--ros-args",
        "-r", f"/joint_states:={topic}", *parameters,
    ]


def fixture(topic, service, mode):
    """Internal subprocess entry; endpoints are always beneath a test namespace."""
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import JointState
    from std_srvs.srv import Trigger

    if not topic.startswith("/w1_docs_test_") or not service.startswith("/w1_docs_test_"):
        raise ValueError("test endpoints must use the isolated namespace")
    rclpy.init(args=[])
    node = rclpy.create_node("w1_reader_test_fixture")
    publisher = node.create_publisher(JointState, topic, qos_profile_sensor_data)
    sent = 0

    def publish():
        nonlocal sent
        sent += 1
        if mode == "recorder_late" and sent <= 30:
            return
        # Deliberately shuffle controlled names and include an unrelated joint.
        msg = JointState(
            name=["passive_toe_joint", "left_elbow_joint", "right_elbow_joint"],
            position=[0.4, -0.2, 0.25],
        )
        msg.header.frame_id = "test_base"
        if mode in ("invalid", "recorder_invalid"):
            msg.position = [0.1]
        elif mode == "recorder_duplicate":
            msg.name = ["joint_a", "joint_a"]
            msg.position = [0.1, 0.2]
        elif mode == "recorder_valid":
            msg.velocity = [0.01, 0.02, 0.03]
        elif mode == "missing_joint" or (mode == "valid" and sent <= 10):
            msg.name = ["passive_toe_joint"]
            msg.position = [0.4]
        elif mode == "velocity_only":
            msg.position = []
            msg.velocity = [0.0, 0.0, 0.0]
        msg.header.stamp = node.get_clock().now().to_msg()
        publisher.publish(msg)

    def status(request, response):
        if mode == "slow_service":
            time.sleep(2.0)
        response.success = mode != "rejected"
        response.message = "disabled" if mode == "rejected" else "holding"
        return response

    node.create_timer(0.05, publish)
    if mode != "no_service":
        node.create_service(Trigger, service, status)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


class InstalledCliTest(unittest.TestCase):
    def setUp(self):
        prefix = f"/w1_docs_test_{os.getpid()}/{self._testMethodName}"
        self.topic = prefix + "/joint_states"
        self.service = prefix + "/get_pvt_interpolation_status"

    def run_reader(self, *parameters):
        return subprocess.run(
            command(self.topic, self.service, *parameters),
            env=ENV, text=True, capture_output=True, timeout=15,
        )

    def run_recorder(self, output_path, *parameters, timeout=15):
        return subprocess.run(
            recorder_command(
                self.topic,
                "-p", f"output_path:={output_path}",
                *parameters,
            ),
            env=ENV, text=True, capture_output=True, timeout=timeout,
        )

    def run_exchange(self, mode="valid", *parameters):
        publisher = subprocess.Popen(
            [sys.executable, __file__, "--fixture", self.topic, self.service, mode],
            env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            text=True, start_new_session=True,
        )
        try:
            result = self.run_reader(
                "-p", "timeout_seconds:=5.0",
                "-p", "service_timeout_seconds:=3.0", *parameters,
            )
            self.assertIsNone(publisher.poll(), "test fixture exited early")
            return result
        finally:
            if publisher.poll() is None:
                os.killpg(publisher.pid, signal.SIGINT)
            try:
                publisher.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(publisher.pid, signal.SIGKILL)
                publisher.communicate()

    def run_recorder_exchange(self, output_path, mode="valid", *parameters):
        publisher = subprocess.Popen(
            [sys.executable, __file__, "--fixture", self.topic, self.service, mode],
            env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            text=True, start_new_session=True,
        )
        try:
            result = self.run_recorder(output_path, *parameters)
            self.assertIsNone(publisher.poll(), "test fixture exited early")
            return result
        finally:
            if publisher.poll() is None:
                os.killpg(publisher.pid, signal.SIGINT)
            try:
                publisher.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(publisher.pid, signal.SIGKILL)
                publisher.communicate()

    def test_valid_named_joint_and_service(self):
        result = self.run_exchange()
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["joint_name"], "right_elbow_joint")
        self.assertEqual(payload["position_rad"], 0.25)
        # Do not restrict a successful response to the startup state "waiting".
        self.assertEqual(payload["pvt"], {"success": True, "message": "holding"})
        self.assertGreater(payload["stamp"]["sec"], 0)

    def test_joint_parameter(self):
        result = self.run_exchange("valid", "-p", "joint_name:=left_elbow_joint")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["joint_name"], "left_elbow_joint")
        self.assertEqual(payload["position_rad"], -0.2)

    def test_invalid_message(self):
        result = self.run_exchange("invalid")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("position must be empty or match name length", result.stderr)
        self.assertFalse(any(line.startswith("{") for line in result.stdout.splitlines()))

    def test_missing_position_times_out(self):
        for mode in ("missing_joint", "velocity_only"):
            with self.subTest(mode=mode):
                result = self.run_exchange(mode, "-p", "timeout_seconds:=1.5")
                self.assertEqual(result.returncode, 3, result.stderr)
                self.assertIn("position for right_elbow_joint timed out", result.stderr)

    def test_timeout_with_paused_sim_clock(self):
        result = self.run_reader(
            "-p", "timeout_seconds:=0.5", "-p", "use_sim_time:=true"
        )
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("position for right_elbow_joint timed out", result.stderr)

    def test_missing_service(self):
        result = self.run_exchange("no_service", "-p", "service_timeout_seconds:=0.5")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("PVT status service discovery timed out", result.stderr)

    def test_slow_service(self):
        result = self.run_exchange("slow_service", "-p", "service_timeout_seconds:=0.5")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("PVT status service response timed out", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_service_reports_false(self):
        result = self.run_exchange("rejected")
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertEqual(
            json.loads(result.stdout.splitlines()[0])["pvt"],
            {"success": False, "message": "disabled"},
        )
        self.assertIn("success=false", result.stderr)

    def test_invalid_parameters(self):
        for parameter in (
            "timeout_seconds:=0.0", "service_timeout_seconds:=-1.0",
            "timeout_seconds:=wrong_type", "joint_name:=42", "joint_name:=' '",
        ):
            with self.subTest(parameter=parameter):
                result = self.run_reader("-p", parameter)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertTrue(result.stderr.strip())
                self.assertNotIn("Traceback", result.stderr)

    def test_recorder_writes_multiframe_jsonl_with_remapped_topic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "capture.jsonl")
            result = self.run_recorder_exchange(
                output_path,
                "recorder_valid",
                "-p", "duration_seconds:=0.8",
                "-p", "timeout_seconds:=1.5",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [json.loads(line) for line in Path(output_path).read_text().splitlines()]

        self.assertEqual(rows[0]["record_type"], "metadata")
        self.assertEqual(rows[0]["schema_version"], 1)
        self.assertEqual(rows[0]["topic"], self.topic)
        self.assertEqual(rows[0]["message_type"], "sensor_msgs/msg/JointState")
        self.assertEqual(rows[0]["units"]["position"], {
            "revolute": "rad", "prismatic": "m",
        })
        samples = rows[1:]
        self.assertGreaterEqual(len(samples), 2)
        self.assertTrue(all(row["record_type"] == "joint_state" for row in samples))
        self.assertEqual(
            samples[0]["name"],
            ["passive_toe_joint", "left_elbow_joint", "right_elbow_joint"],
        )
        self.assertEqual(samples[0]["position"], [0.4, -0.2, 0.25])
        self.assertEqual(
            samples[0]["velocity"], [0.01, 0.02, 0.03]
        )
        self.assertEqual(samples[0]["effort"], [])
        self.assertEqual(samples[0]["frame_id"], "test_base")
        self.assertGreater(samples[0]["stamp"]["sec"], 0)
        self.assertEqual(
            [row["elapsed_seconds"] for row in samples],
            sorted(row["elapsed_seconds"] for row in samples),
        )
        self.assertGreaterEqual(samples[-1]["elapsed_seconds"], 0.6)
        self.assertLess(samples[-1]["elapsed_seconds"], 0.8)

    def test_recorder_no_data_timeout_leaves_metadata_jsonl(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "empty.jsonl")
            result = self.run_recorder(
                output_path,
                "-p", "duration_seconds:=2.0",
                "-p", "timeout_seconds:=0.4",
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            rows = [json.loads(line) for line in Path(output_path).read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["record_type"], "metadata")
        self.assertIn("no valid JointState", result.stderr)

    def test_recorder_duration_without_data_exits_cleanly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "duration.jsonl")
            result = self.run_recorder(
                output_path,
                "-p", "duration_seconds:=0.4",
                "-p", "timeout_seconds:=1.0",
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            rows = [
                json.loads(line)
                for line in Path(output_path).read_text().splitlines()
            ]
        self.assertEqual(len(rows), 1)
        self.assertIn("duration ended before any valid message", result.stderr)

    def test_recorder_late_first_frame_does_not_extend_timeout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "late.jsonl")
            publisher = subprocess.Popen(
                [
                    sys.executable, __file__, "--fixture", self.topic,
                    self.service, "recorder_late",
                ],
                env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                text=True, start_new_session=True,
            )
            try:
                time.sleep(0.2)
                result = self.run_recorder(
                    output_path,
                    "-p", "duration_seconds:=2.0",
                    "-p", "timeout_seconds:=0.4",
                )
            finally:
                if publisher.poll() is None:
                    os.killpg(publisher.pid, signal.SIGINT)
                try:
                    publisher.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(publisher.pid, signal.SIGKILL)
                    publisher.communicate()

            self.assertEqual(result.returncode, 3, result.stderr)
            rows = [json.loads(line) for line in Path(output_path).read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertIn("no valid JointState", result.stderr)

    def test_recorder_timeout_uses_monotonic_time_with_paused_ros_clock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "paused.jsonl")
            result = self.run_recorder(
                output_path,
                "-p", "duration_seconds:=2.0",
                "-p", "timeout_seconds:=0.4",
                "-p", "use_sim_time:=true",
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            rows = [json.loads(line) for line in Path(output_path).read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertIn("no valid JointState", result.stderr)

    def test_recorder_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "existing.jsonl"
            output_path.write_text("keep this capture\n")
            result = self.run_recorder(str(output_path))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(output_path.read_text(), "keep this capture\n")
        self.assertIn("already exists", result.stderr)

    def test_recorder_invalid_message_exits_with_partial_file_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "invalid.jsonl")
            result = self.run_recorder_exchange(
                output_path,
                "recorder_invalid",
                "-p", "duration_seconds:=2.0",
                "-p", "timeout_seconds:=1.5",
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            rows = [json.loads(line) for line in Path(output_path).read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertIn("invalid JointState", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_recorder_invalid_parameters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for name, value in (
                ("duration_seconds", "0.0"),
                ("timeout_seconds", "-1.0"),
            ):
                with self.subTest(name=name, value=value):
                    output_path = str(Path(temp_dir) / f"{name}.jsonl")
                    result = self.run_recorder(
                        output_path, "-p", f"{name}:={value}"
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_recorder_interrupt_flushes_and_closes_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "interrupted.jsonl")
            publisher = subprocess.Popen(
                [
                    sys.executable, __file__, "--fixture", self.topic,
                    self.service, "recorder_valid",
                ],
                env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                text=True, start_new_session=True,
            )
            recorder = None
            try:
                time.sleep(0.2)
                recorder = subprocess.Popen(
                    recorder_command(
                        self.topic,
                        "-p", f"output_path:={output_path}",
                        "-p", "duration_seconds:=10.0",
                        "-p", "timeout_seconds:=5.0",
                    ),
                    env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, start_new_session=True,
                )
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if (
                        Path(output_path).exists()
                        and Path(output_path).stat().st_size > 0
                    ):
                        try:
                            rows = [
                                json.loads(line)
                                for line in Path(output_path).read_text().splitlines()
                            ]
                        except json.JSONDecodeError:
                            time.sleep(0.05)
                            continue
                        if len(rows) > 1:
                            break
                    if recorder.poll() is not None:
                        stdout, stderr = recorder.communicate()
                        self.fail(
                            f"recorder exited before interrupt test: {stderr or stdout}"
                        )
                    time.sleep(0.05)
                else:
                    self.fail("recorder did not write a JointState before interrupt")

                os.killpg(recorder.pid, signal.SIGINT)
                stdout, stderr = recorder.communicate(timeout=8)
                self.assertEqual(recorder.returncode, 130, stderr + stdout)
                closed_rows = [
                    json.loads(line)
                    for line in Path(output_path).read_text().splitlines()
                ]
                self.assertGreaterEqual(len(closed_rows), 2)
                self.assertNotIn("Traceback", stderr)
            finally:
                if recorder is not None and recorder.poll() is None:
                    os.killpg(recorder.pid, signal.SIGKILL)
                    recorder.communicate()
                elif recorder is not None:
                    recorder.communicate()
                if publisher.poll() is None:
                    os.killpg(publisher.pid, signal.SIGINT)
                try:
                    publisher.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(publisher.pid, signal.SIGKILL)
                    publisher.communicate()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fixture":
        fixture(*sys.argv[2:])
    else:
        unittest.main(verbosity=2)
