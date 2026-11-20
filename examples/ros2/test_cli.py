"""Test the installed reader against local, remapped synthetic endpoints.

This fixture is not W1 mock, a controller or a robot simulator. It exercises ROS
transport and application handling only. Run after building and sourcing the
example overlay. No motion command topic is created or published.
"""

import json
import os
import signal
import subprocess
import sys
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
        # Deliberately shuffle controlled names and include an unrelated joint.
        msg = JointState(
            name=["passive_toe_joint", "left_elbow_joint", "right_elbow_joint"],
            position=[0.4, -0.2, 0.25],
        )
        if mode == "invalid":
            msg.position = [0.1]
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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fixture":
        fixture(*sys.argv[2:])
    else:
        unittest.main(verbosity=2)
