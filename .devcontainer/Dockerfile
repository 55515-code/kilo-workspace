FROM mcr.microsoft.com/devcontainers/base:bookworm

# Install common dev tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    make \
    python3 \
    python3-pip \
    python3-venv \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install common global npm tools
RUN npm install -g typescript tsx

WORKDIR /workspace
