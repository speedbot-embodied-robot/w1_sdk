---
layout: home

hero:
  name: Speedbot Weldroid-W1 welding robot
  text: Developer documentation
  tagline: Product information and development interfaces
  image:
    src: /images/front-transparent.png
    alt: Speedbot W1 humanoid welding robot
  actions:
    - theme: brand
      text: SDK integration
      link: ./sdk/integration
    - theme: alt
      text: Product overview
      link: ./product/overview

features:
  - title: Product information
    details: Review product parameters, components, and reference conditions.
    link: ./product/specifications
  - title: Capabilities and applications
    details: Explore shipbuilding scenarios, mobility, perception, control architecture, and application progress.
    link: ./product/capabilities
  - title: SDK development
    details: Integrate the SDK in a verified environment and run a published example.
    link: ./sdk/integration
  - title: W1 whole-body control
    details: Review joint order, units, sessions, and whole-body command restrictions.
    link: ./api/w1-control
---

This manual provides product information and software integration guidance for W1 developers.

**Scope**　The product section introduces W1 / Weldroid-W1. The ROS 2 section covers the 28-axis `speed_W1_v1.2` interface configuration.

::: info Documentation updated
Through 2026-11-20.
:::

## Browse documentation

- [Product overview](./product/overview.md) · [Capabilities and applications](./product/capabilities.md) · [Models and specifications](./product/specifications.md) · [Components and ports](./product/interfaces.md)
- [SDK integration](./sdk/integration.md) · [Release notes](./support/releases.md)
- [W1 ROS 2 example](./sdk/ros2-example.md) · [W1 whole-body control](./api/w1-control.md)
