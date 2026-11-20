> Template note: replace each [To fill] field with information approved for publication and backed by a source. Keep unverified details marked as pending; do not guess. Remove this note and all incomplete fields before publication.

> Template note: document only symbols approved for public use. Complete one section per API. Do not describe internal implementation, unpublished headers, or guessed behavior as a contract.

## API scope

For W1 ROS 2 command formats, the 28-joint order, and PVT sessions, see [W1 whole-body control](./w1-control.md). State, planning, teaching, and welding calls are covered in the [W1 ROS 2 example](../sdk/ros2-example.md). Use the template below for additional SDK symbols and exact release versions.

| Field                          | Value                                                                                |
| ------------------------------ | ------------------------------------------------------------------------------------ |
| SDK name and version           | [To fill: exact SDK version covered by this reference]                               |
| Applicable device and firmware | [To fill: verified models and firmware versions]                                     |
| Public languages               | [To fill: languages and versions covered here]                                       |
| Definition location            | [To fill: public header, module, or message-definition path and repository revision] |

See [SDK integration](../sdk/integration.md) for dependencies and initialization. For a first read, see [Read device state](../sdk/read-state.md).

## API: {public symbol name}

### Identity

**Full name and signature**　[To fill: language, namespace/module, and complete signature]

**Definition**　[To fill: public header or module path]

**Stability**　[To fill: stability level, deprecation policy, or change policy]

### Purpose and constraints

[To fill: the problem this API solves, what it does not do, and its preconditions.]

### Parameters

| Parameter                 | Type                   | Unit or format                               | Required/default                     | Valid range and constraints                  |
| ------------------------- | ---------------------- | -------------------------------------------- | ------------------------------------ | -------------------------------------------- |
| [To fill: parameter name] | [To fill: public type] | [To fill: unit, encoding, or not applicable] | [To fill: required or exact default] | [To fill: bounds and special-value handling] |

### Results and errors

**Success result**　[To fill: return type, fields, validity, and ownership]

**Failure behavior**　[To fill: error code/exception/status and triggering conditions]

**Resources and concurrency**　[To fill: resource release, object lifetime, and thread safety; explain if not applicable]

### Usage example

[To fill: link to a same-version, verified [usage example](../sdk/read-state.md) and state which API behavior it covers.]

### Behavior checks

| Scenario       | Input condition                             | Expected result                                |
| -------------- | ------------------------------------------- | ---------------------------------------------- |
| Normal call    | [To fill: representative valid input]       | [To fill: result confirmed by testing]         |
| Boundary input | [To fill: valid boundary or special value]  | [To fill: result confirmed by testing]         |
| Failure        | [To fill: condition that triggers an error] | [To fill: error behavior confirmed by testing] |
