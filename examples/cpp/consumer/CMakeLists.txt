cmake_minimum_required(VERSION 3.20)
project(w1_docs_cpp_consumer LANGUAGES CXX)

# In a real project, point this to the checked-out examples/cpp directory.
add_subdirectory("${CMAKE_CURRENT_LIST_DIR}/.." w1-docs-state)
add_executable(state_consumer ../main.cpp)
target_link_libraries(state_consumer PRIVATE w1_docs::state)
