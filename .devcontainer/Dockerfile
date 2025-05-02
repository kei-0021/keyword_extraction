# Use the base image from the devcontainer.json
FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
