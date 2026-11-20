#ifndef W1_DOCS_JOINT_STATE_HPP
#define W1_DOCS_JOINT_STATE_HPP

#include <cstddef>
#include <string>
#include <string_view>
#include <vector>

namespace w1_docs {

// Synthetic revolute-joint data. This is not a W1 SDK message definition.
struct JointState {
  std::vector<std::string> names;
  std::vector<double> positions_rad;
  std::vector<double> velocities_rad_s; // Empty means velocity is unavailable.
};

enum class ValidationCode {
  kValid,
  kEmptyState,
  kSizeMismatch,
  kEmptyName,
  kDuplicateName,
  kNonFinitePosition,
  kNonFiniteVelocity,
};

inline constexpr std::size_t kNoJoint = static_cast<std::size_t>(-1);

struct ValidationResult {
  ValidationCode code;
  std::size_t joint_index = kNoJoint;

  explicit operator bool() const noexcept {
    return code == ValidationCode::kValid;
  }
};

// Borrows state for the duration of the call; does not allocate or modify it.
// Checks shape, names and finite values, not hardware operating limits.
ValidationResult validate_state(const JointState &state) noexcept;

// Returned view refers to a static string literal; no caller-owned storage.
std::string_view describe(ValidationCode code) noexcept;

} // namespace w1_docs

#endif
