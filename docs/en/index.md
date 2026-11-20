---
layout: home

hero:
  name: W1
  text: Developer documentation
  tagline: Product information, application capabilities, and ROS 2 interfaces
  actions:
    - theme: brand
      text: Quick start
      link: ./guide/quick-start
    - theme: alt
      text: Product overview
      link: ./product/overview

features:
  - title: Product information
    details: Review product parameters, components, and specification conditions awaiting confirmation.
    link: ./product/specifications
  - title: Capabilities and applications
    details: Explore shipbuilding scenarios, mobility, perception, control architecture, and application progress.
    link: ./product/capabilities
  - title: SDK development
    details: Integrate the SDK in a verified environment and run a published example.
    link: ./sdk/integration
  - title: API and releases
    details: Find public interfaces, compatibility, and changes by SDK version.
    link: ./api/reference
---

This manual provides product information and software integration guidance for W1 developers.

**Scope**　The product section introduces W1 / Weldroid-W1, with information updated through 2026-11-20. The ROS 2 section covers the 28-joint `speed_W1_v1.2` interface configuration. Exact SDK versions, firmware, and hardware revisions remain to be supplied.

::: info Parameters and scope
Measurement conditions and version mappings for product reference values still need confirmation. See [Models and specifications](./product/specifications.md) for the 27 degrees of freedom versus the 28 controlled joints in the interface configuration, and [Capabilities and applications](./product/capabilities.md) for dated application plans.
:::

## Browse documentation

- [Product overview](./product/overview.md) · [Capabilities and applications](./product/capabilities.md) · [Models and specifications](./product/specifications.md) · [Components and ports](./product/interfaces.md)
- [First connection](./guide/quick-start.md) · [SDK integration](./sdk/integration.md) · [Read state example](./sdk/read-state.md)
- [API reference](./api/reference.md) · [Compatibility](./support/compatibility.md) · [Release notes](./support/releases.md)
- [W1 ROS 2 example](./sdk/ros2-example.md) · [W1 whole-body control](./api/w1-control.md)
- [Troubleshooting](./support/troubleshooting.md)

Support channel: [To fill: public contact route, scope, and response expectations]
