# Ideas

- auto-remove old characters
- document the need for extra state data from a getting started perspective; also handle its absence gracefully
- a CI job that checks that tool versions are consistent (and up-to-date?) across pre-commit, uv.lock, and GH actions; or better yet: find a mechanism to merge these tools, such as running CI locally as precommit; or alternatively: find a unified mechanism, such as a shared dev, pre-commit, CI container
- Does sqlite support listening for events?
- claude's /security-review seems to be testing for a whole bunch of typical web vulnerabilities; would be great to have these in CI
- consider a dev container

## web app

- support d20+d8+d6
- support advantage / don't total 2xd20
- relax command parsing
- protect discord.py token
- Chat bot should be able to emit web app URL - how?
- front-end design
- notion of user personas or accounts; possible tie in with Discord accounts
- ini updates via web app

## chat

- Can chat display dynamic content such as embedding the web app? Doesn't look like
- Voice processing
  - With speaker identification and STT, the bot could take audio commands
  - With LLM embedding, could summarise campaign progress and do recaps
