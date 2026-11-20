#include "w1_docs/joint_state.hpp"

#include <iostream>
#include <limits>
#include <string_view>

int main() {
  using w1_docs::JointState;
  using w1_docs::ValidationCode;
  const JointState valid{{"a", "b"}, {0.25, -0.5}, {0.1, 0.0}};
  int failures = 0;
  const auto check = [&](std::string_view name, const JointState &state,
                         ValidationCode code,
                         std::size_t index = w1_docs::kNoJoint) {
    const auto result = w1_docs::validate_state(state);
    if (result.code != code || result.joint_index != index ||
        static_cast<bool>(result) != (code == ValidationCode::kValid)) {
      std::cerr << "FAIL: " << name << '\n';
      ++failures;
    }
  };
  check("valid state", valid, ValidationCode::kValid);
  check("empty state", {}, ValidationCode::kEmptyState);
  check("missing position", {{"a"}, {}, {}}, ValidationCode::kSizeMismatch);
  check("extra position", {{"a"}, {1.0, 2.0}, {}},
        ValidationCode::kSizeMismatch);
  check("missing optional velocity", {{"a"}, {1.0}, {}},
        ValidationCode::kValid);
  check("wrong velocity size", {{"a", "b"}, {1.0, 2.0}, {0.0}},
        ValidationCode::kSizeMismatch);
  check("empty name", {{""}, {1.0}, {}}, ValidationCode::kEmptyName, 0);
  check("duplicate name", {{"a", "a"}, {1.0, 2.0}, {}},
        ValidationCode::kDuplicateName, 1);

  auto invalid = valid;
  invalid.positions_rad[1] = std::numeric_limits<double>::quiet_NaN();
  check("NaN position", invalid, ValidationCode::kNonFinitePosition, 1);
  invalid = valid;
  invalid.positions_rad[0] = std::numeric_limits<double>::infinity();
  check("infinite position", invalid, ValidationCode::kNonFinitePosition, 0);
  invalid = valid;
  invalid.velocities_rad_s[1] = -std::numeric_limits<double>::infinity();
  check("infinite velocity", invalid, ValidationCode::kNonFiniteVelocity, 1);
  check("no invented hardware bounds", {{"a"}, {1.0e100}, {}},
        ValidationCode::kValid);

  if (failures == 0) {
    std::cout << "12 validation cases passed\n";
  }
  return failures == 0 ? 0 : 1;
}
