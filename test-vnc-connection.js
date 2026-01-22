// Simple VNC connection test
const WebSocket = require('ws');

console.log('Testing VNC WebSocket connection...');

const ws = new WebSocket('ws://localhost:6080/websockify');

ws.on('open', function open() {
  console.log('✓ WebSocket connected successfully');
  console.log('✓ Port 6080 is accessible');
  ws.close();
});

ws.on('message', function message(data) {
  console.log('Received data length:', data.length);
});

ws.on('error', function error(err) {
  console.error('✗ WebSocket connection failed:', err.message);
  console.error('  Possible causes:');
  console.error('  - Container not running');
  console.error('  - websockify not started');
  console.error('  - Port not exposed');
});

ws.on('close', function close() {
  console.log('Connection closed');
  process.exit(0);
});

setTimeout(() => {
  console.log('✗ Connection timeout - check if container is running');
  process.exit(1);
}, 5000);
