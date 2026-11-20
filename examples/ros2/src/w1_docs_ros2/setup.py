from setuptools import setup

package_name = "w1_docs_ros2"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="W1 documentation maintainers",
    maintainer_email="jouyang@speedbot.com",
    description="Read W1 joint feedback and query the PVT status service.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "state_reader = w1_docs_ros2.state_reader:main",
        ]
    },
)
