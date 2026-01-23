#!/bin/bash
# Launch Chrome with remote debugging

# Wait for Xvfb to be ready
sleep 3

# Create profile directory if it doesn't exist
mkdir -p /tmp/chrome-profile

# Launch Chrome with comprehensive headless parameters
/usr/bin/chromium \
  --no-sandbox \
  --disable-dev-shm-usage \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --user-data-dir=/tmp/chrome-profile \
  --disable-gpu \
  --disable-software-rasterizer \
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --disable-features=TranslateUI \
  --disable-ipc-flooding-protection \
  --disable-extensions \
  --disable-plugins \
  --disable-images \
  --disable-javascript \
  --headless \
  --window-size=1280,800 \
  --no-first-run \
  --disable-default-apps \
  --disable-sync \
  --disable-translate \
  --hide-scrollbars \
  --metrics-recording-only \
  --mute-audio \
  --no-crash-upload \
  --disable-logging \
  --disable-login-animations \
  --disable-notifications \
  --disable-permissions-api \
  --disable-session-crashed-bubble \
  --disable-infobars &

# Get the process ID
CHROME_PID=$!

# Wait a bit for Chrome to start
sleep 2

# Check if Chrome is still running
if kill -0 $CHROME_PID 2>/dev/null; then
    echo "Chrome started successfully with PID: $CHROME_PID"

    # Test the DevTools endpoint
    sleep 3
    if curl -s http://127.0.0.1:9222/json/version > /dev/null; then
        echo "Chrome DevTools API is responding"
    else
        echo "Warning: Chrome DevTools API not responding yet"
    fi
else
    echo "Chrome failed to start"
    exit 1
fi
