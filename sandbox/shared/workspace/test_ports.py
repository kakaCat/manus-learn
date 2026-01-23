#!/usr/bin/env python3
import socket
import sys

def test_port(host, port):
    """Test if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def main():
    host = 'localhost'
    common_ports = [3000, 8080, 8000, 5000, 4200, 3001, 8081, 80, 443, 5173, 5174]
    
    print(f"Testing common frontend ports on {host}...")
    print("-" * 50)
    
    open_ports = []
    for port in common_ports:
        if test_port(host, port):
            print(f"✓ Port {port}: OPEN")
            open_ports.append(port)
        else:
            print(f"✗ Port {port}: CLOSED")
    
    print("-" * 50)
    if open_ports:
        print(f"Found {len(open_ports)} open port(s): {open_ports}")
        print("\nYou can access the frontend at:")
        for port in open_ports:
            print(f"  http://localhost:{port}")
    else:
        print("No common frontend ports are open.")
        print("\nYou may need to:")
        print("1. Start a frontend server (e.g., npm start, python -m http.server)")
        print("2. Check if the server is running on a different port")
        print("3. Check the server configuration")

if __name__ == "__main__":
    main()