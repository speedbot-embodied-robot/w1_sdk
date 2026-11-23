# Example page title

Describe what a reader will accomplish. State whether the example reads state, sends commands, or only validates local data.

## Supported environment

- Robot/model:
- SDK/firmware version:
- OS/architecture:
- Runtime and dependencies:
- Verification date and setup:

## Source files

List the maintained source and tests. Keep executable source under examples/; import it into the Chinese and English pages instead of copying it.

## Build and run

    # Exact commands from a clean, supported environment

Expected result:

    # Representative output, with secrets and private device data removed

## Inputs and behavior

Describe required parameters, units, message/data ordering, timeouts, side effects, cleanup, error handling, and exit codes.

## Validation and limits

- Checks run:
- Fixture/simulator or real hardware:
- What the checks do not prove:
- Known limitations:

## Source

In both language pages, import the same file and region using the repository's VitePress code import syntax:

    ::: code-group
    <<< ../../../examples/path-to-source{language:line-numbers}
    :::

## Contribution checklist

- [ ] Chinese and English pages exist at the same route.
- [ ] The route is present in docs/.vitepress/config.mts.
- [ ] Both pages import the same source file and region.
- [ ] Commands and expected output were checked in the documented environment.
- [ ] Tests cover the important success and failure behavior.
- [ ] Product/interface sources and verification limits are stated.
