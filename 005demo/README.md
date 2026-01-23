# 005 Sandbox Shell MCP Demo

This demo implements the Sandbox Shell MCP environment described in [Blog 005](../docs/blog/005-sandbox-shell-mcp.md).

## Components

- **Dockerfile**: Builds an Ubuntu-based image with Node.js and the official `@kevinwatt/shell-mcp` server.
- **supervisord.conf**: Manages the MCP Shell process.
- **docker-compose.yml**: Orchestrates the container.
- **test_shell.py**: A Python script to verify the Shell MCP functionality.

## Usage

1.  **Build and Start the Container**:
    ```bash
    docker-compose up -d --build
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Test Script**:
    ```bash
    python test_shell.py
    ```

## Expected Output

The test script should:
1.  Connect to the Shell MCP server inside the Docker container.
2.  List available tools (including `run_command`).
3.  Execute `echo` command.
4.  Execute `uname -a` to check system info.
5.  Create a file `shell_test.txt` inside the container and read it back.
