import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, JointState


class W1StateReader(Node):
    def __init__(self):
        super().__init__("w1_state_reader")
        self.joint_done = False
        self.imu_done = False
        self.create_subscription(
            JointState, "/joint_states", self.on_joint_state, qos_profile_sensor_data
        )
        self.create_subscription(
            Imu, "/imu/data", self.on_imu, qos_profile_sensor_data
        )

    def on_joint_state(self, msg):
        joint_name = "right_elbow_joint"
        if self.joint_done or joint_name not in msg.name:
            return

        index = msg.name.index(joint_name)
        if index >= len(msg.position):
            return

        position = msg.position[index]
        if not math.isfinite(position):
            return

        velocity = msg.velocity[index] if index < len(msg.velocity) else None
        effort = msg.effort[index] if index < len(msg.effort) else None
        self.get_logger().info(
            f"{joint_name}: position={position:.4f} rad, "
            f"velocity={velocity} rad/s, effort={effort} N·m"
        )
        self.joint_done = True

    def on_imu(self, msg):
        if self.imu_done or msg.header.frame_id != "base_link":
            return

        q = msg.orientation
        w = msg.angular_velocity
        a = msg.linear_acceleration
        self.get_logger().info(
            f"IMU {msg.header.frame_id}: "
            f"quaternion xyzw=({q.x}, {q.y}, {q.z}, {q.w}), "
            f"angular_velocity=({w.x}, {w.y}, {w.z}) rad/s, "
            f"linear_acceleration=({a.x}, {a.y}, {a.z}) m/s^2"
        )
        self.imu_done = True


def main():
    rclpy.init()
    node = W1StateReader()
    deadline = time.monotonic() + 8.0
    try:
        while rclpy.ok() and not (node.joint_done and node.imu_done):
            if time.monotonic() >= deadline:
                missing = []
                if not node.joint_done:
                    missing.append("/joint_states")
                if not node.imu_done:
                    missing.append("/imu/data")
                raise TimeoutError("No valid data from " + ", ".join(missing))
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
