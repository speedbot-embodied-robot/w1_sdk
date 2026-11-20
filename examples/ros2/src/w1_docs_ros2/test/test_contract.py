import math
import unittest

from sensor_msgs.msg import JointState
from w1_docs_ros2.state_reader import named_position, validate_state


class JointStateContract(unittest.TestCase):
    def message(self):
        return JointState(
            name=["right_elbow_joint", "left_elbow_joint"], position=[0.1, -0.2]
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


if __name__ == "__main__":
    unittest.main()
