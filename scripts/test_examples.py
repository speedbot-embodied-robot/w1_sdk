"""Build and test the C++ documentation example and shared source references."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*command):
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    run(
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "scripts",
        "-p",
        "test_*.py",
        "-v",
    )
    build = "examples/cpp/build"
    run("cmake", "-S", "examples/cpp", "-B", build, "-DCMAKE_BUILD_TYPE=Release")
    run("cmake", "--build", build, "--parallel", "2")
    run("ctest", "--test-dir", build, "--output-on-failure")
    consumer = build + "/consumer"
    run(
        "cmake",
        "-S",
        "examples/cpp/consumer",
        "-B",
        consumer,
        "-DCMAKE_BUILD_TYPE=Release",
    )
    run("cmake", "--build", consumer, "--parallel", "2")
    run(str(ROOT / consumer / "state_consumer"))
    print("C++, source-reference and consumer tests passed. ROS 2 has a separate job.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
