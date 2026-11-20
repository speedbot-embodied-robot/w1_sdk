#include "w1_docs/joint_state.hpp"

#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string_view>

int main(int argc, char **argv) {
  const std::string_view argument = argc > 1 ? argv[1] : "";
  if (argc == 2 && argument == "--help") {
    std::cout << "Usage: joint_state_demo [--invalid]\n";
    return 0;
  }
  if (argc > 2 || (argc == 2 && argument != "--invalid")) {
    std::cerr << "Usage: joint_state_demo [--invalid]\n";
    return 2;
  }
  try {
    // Owned synthetic data: no network connection and no robot command.
    w1_docs::JointState state{
        {"demo_joint_1", "demo_joint_2"}, {0.25, -0.5}, {0.1, 0.0}};
    if (argument == "--invalid") {
      state.positions_rad[1] = std::numeric_limits<double>::quiet_NaN();
    }
    const auto result = w1_docs::validate_state(state);
    if (!result) {
      std::cerr << "Invalid state: " << w1_docs::describe(result.code);
      if (result.joint_index != w1_docs::kNoJoint) {
        std::cerr << " (joint index " << result.joint_index << ')';
      }
      std::cerr << '\n';
      return 1;
    }
    std::cout << std::fixed << std::setprecision(3);
    for (std::size_t i = 0; i < state.names.size(); ++i) {
      std::cout << state.names[i] << ": position=" << state.positions_rad[i]
                << " rad";
      if (!state.velocities_rad_s.empty()) {
        std::cout << ", velocity=" << state.velocities_rad_s[i] << " rad/s";
      }
      std::cout << '\n';
    }
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "Runtime error: " << error.what() << '\n';
    return 3;
  }
}
