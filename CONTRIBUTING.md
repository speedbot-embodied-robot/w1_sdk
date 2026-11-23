# Contributing to the W1 documentation center

Contributions are welcome. Maintainers with repository write access can use a topic branch; other contributors can fork the repository and open a pull request from their fork. Another maintainer reviews changes before they appear on the published site.

## Before editing

1. Check the existing pages and open pull requests to avoid duplicating work.
2. For product facts or robot interfaces, record the source, applicable model/software version, verification conditions, and known limits. Keep uncertain information marked as unconfirmed.
3. For runnable examples, use the example-page template at templates/EXAMPLE_PAGE_TEMPLATE.md. Keep implementation files under examples/; do not maintain a second copy of executable code in a Markdown fence.

## Add a page

1. Create the Chinese page under docs/zh/ and its English counterpart under the same relative path in docs/en/. For example, docs/zh/sdk/my-example.md and docs/en/sdk/my-example.md.
2. Add the same route to both-language navigation in docs/.vitepress/config.mts. The route must exist in both languages.
3. If the page shows code, import the same source file and region on both pages, using the existing VitePress import style. Source files should live under the appropriate examples/ directory.
4. Explain the supported environment, setup, exact commands, expected result, errors, and validation boundary. State clearly whether a test uses a fixture or was run against W1 hardware.
5. Update the relevant overview page and add tests for new runnable behavior.

## Local checks

Run these from the repository root:

    npm ci
    npm run docs:build
    npm run docs:verify
    npm run docs:format-check
    python3 scripts/test_examples.py

For changes under examples/ros2, also build and run the isolated ROS 2 tests as described in docs/zh/sdk/ros2-example.md. The isolated endpoints verify client behavior; they are not a W1 hardware test.

## Pull requests and review

1. Create a focused branch, for example docs/<topic> or examples/<topic>. If you do not have write access, fork the repository first and create the branch in your fork.
2. Open a pull request against main. Describe the user-facing change, source/version, affected pages and examples, tests run, and any unverified hardware or software conditions.
3. Request review from a maintainer responsible for the affected area. Product claims and robot behavior need review by an appropriate product or engineering owner; tested code needs review by an engineering owner.
4. Address review comments and wait for required checks to pass before merging. Do not merge your own change when repository rules require another approval.

The repository currently has automated example and site checks. Repository administrators must enable branch protection or a ruleset in GitHub to require pull requests, approvals, and the examples and site checks; a workflow file alone does not require approvals. See GitHub's guide to [managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule).

## Ownership

Keep ownership explicit as the maintainer group grows. Agree on responsible reviewers for product, SDK/API, and infrastructure content, then add their GitHub team or usernames to .github/CODEOWNERS and require code-owner review in repository rules. Do not add placeholder teams: GitHub must be able to resolve each owner.
