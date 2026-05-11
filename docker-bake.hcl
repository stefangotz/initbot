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
