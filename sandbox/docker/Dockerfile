FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Configure apt source to use Aliyun mirror
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://ports.ubuntu.com/ubuntu-ports/|http://mirrors.aliyun.com/ubuntu-ports/|g' /etc/apt/sources.list

# Install dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    supervisor \
    novnc \
    websockify \
    net-tools \
    python3-numpy \
    xterm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install development tools (minimal for Node.js MCP servers)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure npm to use Aliyun mirror
RUN npm config set registry https://registry.npmmirror.com

# Install Chromium from PPA (better compatibility)
# Note: Need to use python3.10 for add-apt-repository due to apt_pkg dependency
RUN PYTHON_VERSION=$(python3 --version) && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 2 && \
    add-apt-repository ppa:xtradeb/apps -y && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    apt-get update && \
    apt-get install -y chromium --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create symbolic link for chromium-browser
RUN ln -sf /usr/bin/chromium /usr/bin/chromium-browser

# Install Chinese fonts and language support
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    language-pack-zh-hans \
    locales \
    && locale-gen zh_CN.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install official MCP servers
RUN npm install -g chrome-devtools-mcp@latest && \
    npm install -g @modelcontextprotocol/server-filesystem@latest && \
    npm install -g @kevinwatt/shell-mcp@latest

# Create directories for MCP server logs and workspace
RUN mkdir -p /var/log/mcp /root/shared/workspace /root/shared/workspace/screenshots /root/shared/workspace/downloads

# Configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/launch_chrome.sh /usr/local/bin/launch_chrome.sh

# Environment variables
ENV DISPLAY=:1
ENV RESOLUTION=1280x800

# Expose ports
# 5900: VNC (TCP)
# 6080: noVNC (HTTP/WebSocket)
EXPOSE 5900 6080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
