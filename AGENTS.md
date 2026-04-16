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

#### Playwright setup

**Without a sandbox:** Enable the official plugin in `~/.claude/settings.json`:
```json
"enabledPlugins": {
  "playwright@claude-plugins-official": true
}
```
The plugin starts the browser automatically — no other configuration needed. The `.mcp.json` in the project root is not required and can be ignored.

#### Playwright in a nono sandbox

Browsers cannot launch inside a nono sandbox (macOS Seatbelt blocks the Mach IPC and xattr syscalls browsers require). The workaround is to run the Playwright MCP server as an external process and connect to it over localhost.

**Before starting Claude Code in nono**, run in a separate terminal:
```
tools/run_playwright.sh
```

This starts `@playwright/mcp` on `http://localhost:8931/sse`. Claude Code connects to it via SSE transport (configured in `~/.claude/mcp.json`), so all browser automation runs outside the sandbox entirely. The nono profile needs no extra `--allow` flags beyond the defaults.

### Dev server

Start with:
```
tools/run_web_dev.sh
```

This generates 5 sample characters with fresh initiative timestamps, exports them to `dev-state/dev.sqlite`, and starts the server. The server prints the session URL to stdout:
```
URL: http://localhost:8080/dev/<token>/
```

Read the URL from the server output (e.g. `/tmp/initbot-web-dev.log` if started in the background). The state is regenerated on each run (timestamps stay fresh). `dev-state/` is gitignored.

### Datastar RC.8 gotchas

The tracker uses Datastar v1.0.0-RC.8. Several things differ from what documentation or LLM training data might suggest:

**Attribute format — colons, not hyphens, for sub-keys:**
- `data-on:click="expr"` ✓  — `data-on-click` is silently ignored
- `data-on:submit__prevent="@post(...)"` ✓
- `data-on:keydown__escape="expr"` ✗  — fires on **every** keydown, not just Escape; use `data-on:keydown="evt.key==='Escape' && expr"` instead
- `data-bind:signalname` ✓
- Plugins with no sub-key (`data-show`, `data-signals`, `data-init`, `data-text`, `data-effect`) still use plain hyphens ✓

**`data-on:click` and `data-init` cannot coexist on the same element.** Put `data-on:click` on a separate child div used as an event-delegation wrapper; `data-init` stays on the outer div.

**HTML lowercases attribute keys — signal names must be all-lowercase when referenced via `data-bind:`.** `data-bind:initVal` becomes `data-bind:initval` in the DOM. The bind plugin then looks for signal `initval`, not `initVal`. Keep signal names that appear in `data-bind:` all-lowercase throughout (`data-signals`, expressions, and server-side JSON keys must all agree).

**`evt` is available in `data-on:*` expressions.** The `on` plugin injects `evt` as an extra named argument so `evt.target.closest(...)` works correctly.

**Server → client signal reset:** After a POST action, return `SSE.patch_signals({"editing": False})` to dismiss the edit panel. Dispatching `datastar-signal-patch` CustomEvents from the browser externally has no effect.

### Design iteration workflow

1. Start the dev server in the background: `tools/run_web_dev.sh &>/tmp/initbot-web-dev.log &`
2. Read the URL from the log: `grep '^URL:' /tmp/initbot-web-dev.log`
3. Use Playwright MCP to navigate to that URL and take a screenshot
4. Edit `packages/initbot-web/src/initbot_web/templates/tracker.html`
5. Use Playwright MCP to verify the result visually before committing

**The dev server does not auto-reload.** After changing Python source files (routes, handlers), kill the running server and restart it. Stale code returns wrong HTTP status codes with no helpful error — always restart after backend changes.

**To inspect what Datastar sends in a `@post()`, intercept `window.fetch` before triggering the action:**
```js
window._bodies = [];
const orig = window.fetch;
window.fetch = async (url, opts) => { window._bodies.push(opts?.body); return orig(url, opts); };
```
Then check `window._bodies` in a follow-up `browser_evaluate`. Server logs show status codes only, not bodies.

## Implementation Workflow

Use feature branches and pull requests.
Never commit to or push the main branch directly.
The standard workflow has the following steps:

- obtain instructions for what to change from the user
- create a feature branch
- take the following actions for each step of the instructions or the plan (there may be only one step):
  - implement the changes
  - commit, push, and monitor CI/CD results (via `gh run watch` or `gh run list`) until they pass
  - if you are working off a plan file, mark the step as done in the plan file
  - if the step required multiple commits to get right, squash them into a single commit for this step
  - ask the user for a review before proceeding to the next step
- once all steps are complete, delete the plan file if you are working off a plan file in the repository
- squash all feature-branch commits unless the user's instruction say not to squash commits
- rebase the feature branch onto the latest version of the main branch
- create a pull request
- once the pull request is merged, delete the local feature branch and switch back to the main branch
