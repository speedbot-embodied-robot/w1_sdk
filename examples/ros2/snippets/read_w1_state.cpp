#include <chrono>
#include <cstddef>
#include <cmath>
#include <memory>
#include <string>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/joint_state.hpp"

using namespace std::chrono_literals;

class W1StateReader : public rclcpp::Node
{
public:
  W1StateReader() : Node("w1_state_reader")
  {
    joint_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states", rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::JointState::ConstSharedPtr msg) {
        if (joint_done_) return;
        for (std::size_t i = 0; i < msg->name.size(); ++i) {
          if (msg->name[i] != "right_elbow_joint" ||
              i >= msg->position.size() || !std::isfinite(msg->position[i])) {
            continue;
          }
          const auto velocity =
            i < msg->velocity.size() ? std::to_string(msg->velocity[i]) : "n/a";
          const auto effort =
            i < msg->effort.size() ? std::to_string(msg->effort[i]) : "n/a";
          RCLCPP_INFO(
            get_logger(), "right_elbow_joint: %.4f rad, velocity=%s rad/s, effort=%s",
            msg->position[i], velocity.c_str(), effort.c_str());
          joint_done_ = true;
          break;
        }
      });

    imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
      "/imu/data", rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::Imu::ConstSharedPtr msg) {
        if (imu_done_ || msg->header.frame_id != "base_link") return;
        RCLCPP_INFO(
          get_logger(),
          "IMU %s: q=(%.3f, %.3f, %.3f, %.3f), "
          "gyro=(%.3f, %.3f, %.3f) rad/s, accel=(%.3f, %.3f, %.3f) m/s^2",
          msg->header.frame_id.c_str(),
          msg->orientation.x, msg->orientation.y,
          msg->orientation.z, msg->orientation.w,
          msg->angular_velocity.x, msg->angular_velocity.y,
          msg->angular_velocity.z,
          msg->linear_acceleration.x, msg->linear_acceleration.y,
          msg->linear_acceleration.z);
        imu_done_ = true;
      });
  }

  bool complete() const { return joint_done_ && imu_done_; }

private:
  bool joint_done_{false};
  bool imu_done_{false};
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<W1StateReader>();
  const auto deadline = std::chrono::steady_clock::now() + 8s;

  while (rclcpp::ok() && !node->complete() &&
         std::chrono::steady_clock::now() < deadline) {
    rclcpp::spin_some(node);
    std::this_thread::sleep_for(10ms);
  }

  const bool complete = node->complete();
  rclcpp::shutdown();
  return complete ? 0 : 1;
}
