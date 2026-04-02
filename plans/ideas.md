# Ideas

- document the need for extra state data from a getting started perspective; also handle its absence gracefully
- Does sqlite support listening for events?
- claude's /security-review seems to be testing for a whole bunch of typical web vulnerabilities; would be great to have these in CI
- consider a dev container
- rename LocalState store to JsonState store or similar, update URI as well
- enforce pinning pre-commit dependencies to commit SHAs
- an interactive configuration mode in each application for a convenient way to set and persist configuration settings; user interaction to be based on metadata of config options; auto-activate on first run; persisting optional
- minimize impact on public infrastructure (such as pypi or dockerhub.io) when building containers and running CI/CD

## web app

- front-end design
- notion of user personas or accounts; possible tie in with Discord accounts
- ini updates via web app

## chat

- support d20+d8+d6
- support advantage / don't total 2xd20
- relax command parsing
- protect discord.py token
- Chat bot should be able to emit web app URL - how?
- Can chat display dynamic content such as embedding the web app? Doesn't look like
- Voice processing
  - With speaker identification and STT, the bot could take audio commands
  - With LLM embedding, could summarise campaign progress and do recaps
- better support for removing characters with ambiguous names (differences in case)
- prevent creation of characters whose names only differ in case; fall-back to existing character for init command
