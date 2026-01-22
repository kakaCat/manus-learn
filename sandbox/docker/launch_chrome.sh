#!/bin/bash
# Launch Chrome with remote debugging

# Wait for Xvfb to be ready
sleep 2

# Launch Chrome
/usr/bin/chromium --no-sandbox --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile --disable-gpu --disable-software-rasterizer &

# Wait a bit for Chrome to start
sleep 5

echo "Chrome launched"