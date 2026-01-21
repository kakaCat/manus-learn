FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN sed -i 's/ports.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    supervisor \
    novnc \
    websockify \
    net-tools \
    python3-numpy \
    xterm \
    && rm -rf /var/lib/apt/lists/*

# Install development tools and dependencies for MCP servers
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    wget \
    ca-certificates \
    gnupg \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11+
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Chromium browser and chromedriver
RUN apt-get update && apt-get install -y \
    chromium-browser \
    chromium-chromedriver \
    && rm -rf /var/lib/apt/lists/*

# Install official MCP servers
RUN npm install -g chrome-devtools-mcp@latest && \
    npm install -g @modelcontextprotocol/server-filesystem@latest

# Create MCP servers directories
RUN mkdir -p /opt/mcp-servers /var/log/mcp /root/shared/workspace /root/shared/workspace/screenshots /root/shared/workspace/downloads

# Set up Python virtual environment for MCP servers (outside mounted directory)
RUN python3.11 -m venv /opt/mcp-venv

# Copy requirements file and install MCP server dependencies
# Note: MCP server code will be mounted via docker-compose volume to /opt/mcp-servers
COPY mcp-servers/requirements.txt /tmp/mcp-requirements.txt
RUN /opt/mcp-venv/bin/pip install --upgrade pip && \
    /opt/mcp-venv/bin/pip install -r /tmp/mcp-requirements.txt && \
    rm /tmp/mcp-requirements.txt

# Configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Environment variables
ENV DISPLAY=:1
ENV RESOLUTION=1280x800

# Expose ports
# 5900: VNC (TCP)
# 6080: noVNC (HTTP/WebSocket)
EXPOSE 5900 6080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
