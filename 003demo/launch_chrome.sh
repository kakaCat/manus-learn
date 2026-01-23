#!/bin/bash
# 等待 Xvfb 就绪
sleep 2

# 启动 Chrome (前台运行，不要使用 &)
# 添加 --incognito 避免崩溃恢复弹窗
exec /usr/bin/chromium \
  --no-sandbox \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-profile \
  --disable-gpu \
  --disable-software-rasterizer \
  --incognito \
  --no-first-run \
  --test-type \
  --no-default-browser-check
