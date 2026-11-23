import math
import unittest

from sensor_msgs.msg import JointState
from w1_docs_ros2.record_joint_states import (
    message_record,
    validate_joint_state,
)
from w1_docs_ros2.state_reader import named_position, validate_state


class JointStateContract(unittest.TestCase):
    def message(self):
        return JointState(
            name=["right_elbow_joint", "left_elbow_joint"],
            position=[0.1, -0.2],
        )

    def test_optional_arrays_and_velocity_only(self):
        msg = self.message()
        validate_state(msg)
        msg.position = []
        msg.velocity = [0.0, 1.0]
        validate_state(msg)
        self.assertIsNone(named_position(msg, "right_elbow_joint"))

    def test_match_by_name(self):
        msg = self.message()
        self.assertEqual(named_position(msg, "right_elbow_joint"), 0.1)
        msg.name.reverse()
        msg.position.reverse()
        self.assertEqual(named_position(msg, "right_elbow_joint"), 0.1)

    def test_passive_only_frame_is_ignored(self):
        msg = JointState(name=["passive_toe_joint"], position=[0.4])
        self.assertIsNone(named_position(msg, "right_elbow_joint"))

    def test_invalid_messages(self):
        for changes in (
            {"name": []},
            {"name": ["right_elbow_joint", "right_elbow_joint"]},
            {"name": ["right_elbow_joint", ""]},
            {"position": [0.1]},
            {"position": []},
            {"position": [math.nan, 0.0]},
            {"velocity": [math.inf, 0.0]},
            {"effort": [1.0]},
        ):
            with self.subTest(changes=changes):
                msg = self.message()
                for name, value in changes.items():
                    setattr(msg, name, value)
                with self.assertRaises(ValueError):
                    validate_state(msg)


class RecorderContract(unittest.TestCase):
    def test_preserves_stamp_frame_and_original_array_order(self):
        msg = JointState(
            name=["joint_b", "joint_a"],
            position=[0.2, -0.1],
            velocity=[0.02, -0.01],
        )
        msg.header.stamp.sec = 12
        msg.header.stamp.nanosec = 34
        msg.header.frame_id = "base_link"

        row = message_record(msg, 1.25)

        self.assertEqual(row["stamp"], {"sec": 12, "nanosec": 34})
        self.assertEqual(row["frame_id"], "base_link")
        self.assertEqual(row["name"], ["joint_b", "joint_a"])
        self.assertEqual(row["position"], [0.2, -0.1])
        self.assertEqual(row["velocity"], [0.02, -0.01])
        self.assertEqual(row["effort"], [])
        self.assertEqual(row["elapsed_seconds"], 1.25)

    def test_all_optional_arrays_can_be_empty(self):
        row = message_record(JointState(name=["joint_a"]), 0.0)
        self.assertEqual(row["position"], [])
        self.assertEqual(row["velocity"], [])
        self.assertEqual(row["effort"], [])

    def test_rejects_bad_names_lengths_and_nonfinite_values(self):
        invalid_messages = (
            JointState(name=[]),
            JointState(name=["joint_a", "joint_a"], position=[0.0, 1.0]),
            JointState(name=[""], position=[0.0]),
            JointState(name=["joint_a"], position=[0.0, 1.0]),
            JointState(name=["joint_a"], velocity=[math.nan]),
            JointState(name=["joint_a"], effort=[math.inf]),
        )
        for msg in invalid_messages:
            with self.subTest(msg=msg):
                with self.assertRaises(ValueError):
                    validate_joint_state(msg)


if __name__ == "__main__":
    unittest.main()
