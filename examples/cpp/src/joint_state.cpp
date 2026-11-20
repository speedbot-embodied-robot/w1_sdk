#include "w1_docs/joint_state.hpp"

#include <cmath>

namespace w1_docs {

ValidationResult validate_state(const JointState &state) noexcept {
  const auto count = state.names.size();
  if (count == 0) {
    return {ValidationCode::kEmptyState};
  }
  if (state.positions_rad.size() != count ||
      (!state.velocities_rad_s.empty() &&
       state.velocities_rad_s.size() != count)) {
    return {ValidationCode::kSizeMismatch};
  }
  for (std::size_t i = 0; i < count; ++i) {
    if (state.names[i].empty()) {
      return {ValidationCode::kEmptyName, i};
    }
    // Avoid allocating a hash table in this small, non-throwing validator.
    for (std::size_t j = 0; j < i; ++j) {
      if (state.names[i] == state.names[j]) {
        return {ValidationCode::kDuplicateName, i};
      }
    }
    if (!std::isfinite(state.positions_rad[i])) {
      return {ValidationCode::kNonFinitePosition, i};
    }
    if (!state.velocities_rad_s.empty() &&
        !std::isfinite(state.velocities_rad_s[i])) {
      return {ValidationCode::kNonFiniteVelocity, i};
    }
  }
  return {ValidationCode::kValid};
}

std::string_view describe(ValidationCode code) noexcept {
  switch (code) {
  case ValidationCode::kValid:
    return "valid";
  case ValidationCode::kEmptyState:
    return "state must contain at least one joint";
  case ValidationCode::kSizeMismatch:
    return "array sizes do not match joint names";
  case ValidationCode::kEmptyName:
    return "joint name must not be empty";
  case ValidationCode::kDuplicateName:
    return "joint names must be unique";
  case ValidationCode::kNonFinitePosition:
    return "position must be finite";
  case ValidationCode::kNonFiniteVelocity:
    return "velocity must be finite";
  }
  return "unknown validation code";
}

} // namespace w1_docs
