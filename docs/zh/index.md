---
layout: home

hero:
  name: 视比特焊接机器人Weldroid-W1
  text: 开发者文档中心
  tagline: 产品资料、作业能力与 ROS 2 开发接口
  image:
    src: /images/front-transparent.png
    alt: 视比特 W1 人形焊接机器人
  actions:
    - theme: brand
      text: SDK 集成
      link: ./sdk/integration
    - theme: alt
      text: 了解产品
      link: ./product/overview

features:
  - title: 产品资料
    details: 查看产品参数、部件信息及待确认的规格条件。
    link: ./product/specifications
  - title: 能力与应用
    details: 了解船舶焊接场景、移动与感知能力、控制架构及应用阶段。
    link: ./product/capabilities
  - title: SDK 开发
    details: 按已验证的环境完成 SDK 接入，并运行公开示例。
    link: ./sdk/integration
  - title: W1 整机控制
    details: 查看关节顺序、单位、会话和整机控制限制。
    link: ./api/w1-control
---

本手册面向 W1 开发者，提供产品信息和软件接入文档。

**资料范围**　产品部分介绍 W1 / Weldroid-W1，资料更新至 2026-11-20；ROS 2 部分对应 `speed_W1_v1.2` 的 28 轴接口配置。SDK 精确版本、固件和硬件修订仍待补充。

::: info 参数与适用范围
产品参考参数的测量条件和版本对应关系仍需确认。27 自由度与接口配置的 28 受控轴差异见[型号与规格](./product/specifications.md)；应用计划见[能力与应用](./product/capabilities.md)。
:::

## 文档目录

- [产品概览](./product/overview.md) · [能力与应用](./product/capabilities.md) · [型号与规格](./product/specifications.md) · [部件与接口](./product/interfaces.md)
- [SDK 集成](./sdk/integration.md) · [发行说明](./support/releases.md)
- [W1 ROS 2 示例](./sdk/ros2-example.md) · [W1 整机控制](./api/w1-control.md)

支持渠道：【待支持团队填写：公开服务入口、适用范围和响应方式】
