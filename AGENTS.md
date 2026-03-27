# AGENTS.md

The initbot project supports and simplifies bookkeeping and collaboration among players during role-playing sessions.
Its primary user interface is a Discord chat bot.
It also features a currently rudimentary web application.
Both applications access the same central data and storage model.

- Python project
- using discord.py
- managed with uv
- Python virtual environment in .venv directory via VIRTUAL_ENV env var and uv
- hosted on github
- gh CLI available
- precommit hooks cover code formatting and code quality
- CI/CD jobs cover additional code quality and maintenance aspects

## Instructions

- do not add Co-Authored-By lines or similar attributions to commit messages
- ensure presence of type hints for function signatures where possible
- mark constants with the type hint `Final`

## Planning Workflow

The file plans/ideas.md contains unelaborated ideas for improvements and features.
The user may occasionally ask you to elaborate one of those ideas into a full implementation plan.
Once the user approves of such a plan, store it as a separate markdown file with a short memorable name in the plans/ directory and remove the corresponding idea from the ideas.md file.

## Web Frontend

The web app package is at `packages/initbot-web/`. The single current page is the initiative tracker (`tracker.html`), served via Starlette with Datastar SSE.

### Tools for visual design work

- **Playwright MCP** is configured and connected. Use it to navigate to the running app, take screenshots, and verify visual changes after editing templates.
- **`/frontend-design` skill** is installed. Invoke it at the start of design work to establish a visual direction before writing code.

### Dev server

Start with:
```
tools/run_web_dev.sh
```

This generates 5 sample characters with fresh initiative timestamps, exports them to `dev-state/dev.sqlite`, and starts the server at:
```
http://localhost:8080/s/dev/
```

The state is regenerated on each run (timestamps stay fresh). `dev-state/` is gitignored.

### Design iteration workflow

1. Start the dev server (`tools/run_web_dev.sh`)
2. Use Playwright MCP to navigate to `http://localhost:8080/s/dev/` and take a screenshot
3. Edit `packages/initbot-web/src/initbot_web/templates/tracker.html`
4. Use Playwright MCP to verify the result visually before committing

## Implementation Workflow

The initbot project is currently maintained by only one person.
There are no other contributors available for code review.
Therefore, use feature branches, but do not use pull requests when implementing changes.
The standard workflow has the following steps:

- obtain instructions for what to change from the user
- create a feature branch
- do not create a pull request for the feature branch
- take the following actions for each step of the instructions or the plan (there may be only one step):
  - implement the changes
  - commit, push, and monitor CI/CD results (via `gh run watch` or `gh run list`) until they pass
  - if you are working off a plan file, mark the step as done in the plan file
  - if the step required multiple commits to get right, squash them into a single commit for this step
  - ask the user for a review before proceeding to the next step
- once all steps are complete, squash all feature-branch commits unless the user's instruction say not to squash commits
- rebase the feature branch onto the latest version of the main branch
- ask the user for a review
- once the user approves of the changes, delete the plan file if you are working off a plan file
- unless the user instructs you otherwise, the user usually takes care of merging the feature branch into the main branch
