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

## Planning Workflow

The file plans/ideas.md contains unelaborated ideas for improvements and features.
The user may occasionally ask you to elaborate one of those ideas into a full implementation plan.
Once the user approves of such a plan, store it as a separate markdown file with a short memorable name in the plans/ directory and remove the corresponding idea from the ideas.md file.

## Implementation Workflow

The initbot project is currently maintained by only one person.
There are no other contributors available for code review.
Therefore, use feature branches, but do not use pull requests when implementing changes.
The standard workflow has the following steps:

- obtain instructions for what to change from the user
- if you are asked to implement a plan with multiple steps or phases, follow this workflow separately (with separate feature branches) for each step or phase
- create a feature branch
- do not create a pull request for the feature branch
- implement the changes
- commit, push, and monitor CI/CD results (via `gh run watch` or `gh run list`) until they pass
- squash all feature-branch commits unless the user's instruction say not to squash commits
- rebase the feature branch onto the latest version of the main branch
- ask the user for review
- if the user approves of the changes, ask the user if it is OK to mark the given step or phase as complete in the plan file or to delete the plan if it is fully implemented
- unless the user instructs you otherwise, the user usually takes care of merging the feature branch into the main branch
