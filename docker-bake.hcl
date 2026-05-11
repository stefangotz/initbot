# Both targets share the builder and runtime-base stages. Building them with
# two sequential `docker buildx build` calls causes a race condition: the
# background cache export from the first call holds a write lock on the shared
# layers when the second call starts. Baking builds both targets in a single
# BuildKit session, so the shared layers are only written once and the lock
# contention never occurs.

group "default" {
  targets = ["chat", "web"]
}

target "chat" {
  context    = "."
  target     = "chat"
  tags       = ["initbot-chat"]
  cache-from = [
    "type=local,src=/tmp/.buildx-cache/chat",
    "type=local,src=/tmp/.buildx-cache/web",
  ]
  cache-to = ["type=local,dest=/tmp/.buildx-cache-new/chat,mode=max"]
  output   = ["type=docker"]
}

target "web" {
  context    = "."
  target     = "web"
  tags       = ["initbot-web"]
  cache-from = [
    "type=local,src=/tmp/.buildx-cache/chat",
    "type=local,src=/tmp/.buildx-cache/web",
  ]
  cache-to = ["type=local,dest=/tmp/.buildx-cache-new/web,mode=max"]
  output   = ["type=docker"]
}
